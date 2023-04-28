import decimal
import asyncio
import enum
import time
import uuid
import json

from fastapi import FastAPI, Path, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, validator, Field

import aio_pika
import aio_pika.abc


class EventState(enum.Enum):
    NEW = 1
    FINISHED_WIN = 2
    FINISHED_LOSE = 3


class EventBase(BaseModel):
    coefficient: decimal.Decimal
    deadline: int = Field(default=int(time.time()) + 600)

    @validator("coefficient")
    def check_coeff(cls, value: decimal.Decimal):
        if value <= 0:
            raise ValueError("The coefficient must be strictly greater than zero")
        if value.as_tuple().exponent < -2:
            raise ValueError("The coefficient must be with two decimal places")
        return value


class EventCreate(EventBase):
    state: EventState = EventState.NEW


class EventUpdate(EventBase):
    state: EventState


class EventUpdateState(BaseModel):
    state: EventState


class EventUpdateCoeff(BaseModel):
    coefficient: decimal.Decimal

    @validator("coefficient")
    def check_coeff(cls, value: decimal.Decimal):
        if value <= 0:
            raise ValueError("The сoefficient must be strictly greater than zero")
        if value.as_tuple().exponent < -2:
            raise ValueError("The coefficient must be with two decimal places")
        return value


class Event(EventBase):
    event_id: uuid.UUID
    state: EventState


event_list: list[Event] = [
    Event(
        event_id=uuid.uuid4(),
        coefficient=1.2,
        deadline=int(time.time()) + 600,
        state=EventState.NEW,
    ),
    Event(
        event_id=uuid.uuid4(),
        coefficient=1.15,
        deadline=int(time.time()) + 60,
        state=EventState.NEW,
    ),
    Event(
        event_id=uuid.uuid4(),
        coefficient=1.67,
        deadline=int(time.time()) + 90,
        state=EventState.NEW,
    ),
]

events: dict[uuid.UUID, Event] = {event.event_id: event for event in event_list}

app = FastAPI(title="line-provider")

rabbitmq_url = "amqp://rabbitmq:rabbitmq@rabbitmq/"
routing_key = "events"


async def get_rabbitmq_connection():
    # Создаем подключение к RabbitMQ
    connection = await aio_pika.connect_robust(rabbitmq_url)
    try:
        yield connection
    finally:
        # close after response
        await connection.close()


async def get_events_channel(
    connection: aio_pika.RobustConnection = Depends(get_rabbitmq_connection),
):
    channel = await connection.channel()
    return channel


async def send_event_to_channel(channel: aio_pika.abc.AbstractChannel, event: Event):
    msg = json.dumps(jsonable_encoder(event)).encode("utf-8")
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=msg,
            content_type="application/json",
            content_encoding="utf-8",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=routing_key,
    )
    print(f"sended: {msg}")


@app.on_event("startup")
async def on_startup():
    # send hardcode events
    connection = await aio_pika.connect_robust(rabbitmq_url)
    async with connection:
        channel = await get_events_channel(connection)
        # make sure the queue exists
        queue = await channel.declare_queue(routing_key)
        # send events
        tasks = [send_event_to_channel(channel, event) for event in event_list]
        await asyncio.gather(*tasks)


@app.post("/event", response_model=Event)
async def create_event(
    event_create: EventCreate,
    channel: aio_pika.abc.AbstractChannel = Depends(get_events_channel),
):
    event = Event(event_id=uuid.uuid4(), **event_create.dict())
    events[event.event_id] = event
    await send_event_to_channel(channel, event)
    return event


@app.get("/events")
async def get_events():
    # add filter for event state: only new events
    return list(
        e
        for e in events.values()
        if time.time() < e.deadline and e.state == EventState.NEW
    )


@app.get("/events/all")
async def get_events():
    return list(events.values())


@app.get("/event/{event_id}")
async def get_event(event_id: uuid.UUID = Path(...)):
    if event_id in events:
        return events[event_id]

    raise HTTPException(status_code=404, detail="Event not found")


@app.put("/events/{event_id}", response_model=Event)
async def update_event(
    event_id: uuid.UUID,
    event_update: EventUpdate,
    channel: aio_pika.abc.AbstractChannel = Depends(get_events_channel),
):
    event = events.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    # check event state already not new
    if event.state != EventState.NEW:
        raise HTTPException(status_code=409, detail="Event already closed")
    updated_event = Event(event_id=event_id, **event_update.dict())
    events[event_id] = updated_event
    await send_event_to_channel(channel, updated_event)
    return updated_event


@app.patch("/events/{event_id}/state", response_model=Event)
async def update_event_state(
    event_id: uuid.UUID,
    event_update: EventUpdateState,
    channel: aio_pika.abc.AbstractChannel = Depends(get_events_channel),
):
    event = events.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    # check event state already not new
    if event.state != EventState.NEW:
        raise HTTPException(status_code=409, detail="Event already closed")
    event.state = event_update.state
    await send_event_to_channel(channel, event)
    return event


@app.patch("/events/{event_id}/coeff", response_model=Event)
async def update_event_coeff(
    event_id: uuid.UUID,
    event_update: EventUpdateCoeff,
    channel: aio_pika.abc.AbstractChannel = Depends(get_events_channel),
):
    event = events.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    # check event state already not new
    if event.state != EventState.NEW:
        raise HTTPException(status_code=409, detail="Event already closed")
    event.coefficient = event_update.coefficient
    await send_event_to_channel(channel, event)
    return event
