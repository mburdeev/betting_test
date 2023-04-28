import json

import aio_pika
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app import schemas, services
from app.db import models, session
from app.services import utils
from app.config import RABBITMQ_URL


async def get_active_events(db: AsyncSession) -> list[models.Event]:
    """
    Получить активные события.
    Активные это те, у которых не истек дедлайн
    """
    stmt = sa.select(models.Event).where(
        models.Event.deadline >= utils.current_timestamp()
    )
    result = await db.execute(stmt)
    events = result.scalars().all()
    return events


async def get_event_by_id(
    db: AsyncSession, event_id: str, must_be: None | bool = None
) -> None | models.Event:
    """
    Получить событие по id
    """
    stmt = sa.select(models.Event).where(models.Event.id == event_id)
    result = await db.execute(stmt)
    event = result.scalar()

    if must_be == True and event is None:
        raise ValueError("The event is not store in db")
    elif must_be == False and event is not None:
        raise ValueError("The event is already stored")

    return event


async def create_event_by_full_info(
    db: AsyncSession, event_create: schemas.Event
) -> models.Event:
    event = models.Event(**event_create.dict())
    db.add(event)
    await db.commit()


async def update_event(
    db: AsyncSession, event: models.Event, event_update: schemas.Event
) -> models.Event:
    # we cannot update closed events, this will lead to unexpected behavior
    if event.state != schemas.EventState.NEW:
        raise ValueError("Event already closed")
    # update event status, close event
    elif event_update.state != schemas.EventState.NEW:
        if event_update.state == schemas.EventState.FINISHED_WIN:
            bet_state = schemas.BetState.WIN
        else:
            bet_state = schemas.BetState.LOSE
        # update event
        stmt = (
            sa.update(models.Event)
            .where(models.Event.id == event.id)
            .values(event_update.dict(exclude={"id"}))
        )
        result = await db.execute(stmt)
        await db.flush()
        # update bet state
        await services.bets.update_bet_state_by_event(db, event.id, bet_state)
    # update event fields (deadline, coiff)
    else:
        stmt = (
            sa.update(models.Event)
            .where(models.Event.id == event.id)
            .values(event_update.dict(exclude={"id", "status"}))
        )
        result = await db.execute(stmt)
        await db.commit()


async def handle_event(event_info: schemas.Event):
    """Обработчик получения события"""
    async with session.async_session() as db:
        event = await get_event_by_id(db, event_info.id)
        if event is None:
            await create_event_by_full_info(db, event_info)
        else:
            await update_event(db, event, event_info)


def parse_event(data: bytes) -> schemas.Event:
    return schemas.Event(**json.loads(data))


async def listen_events() -> None:
    connection = await aio_pika.connect_robust(RABBITMQ_URL)

    queue_name = "events"

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue(queue_name)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    logger.info(message.body)
                    try:
                        event = parse_event(message.body)
                        await handle_event(event)
                    except Exception as e:
                        logger.exception(e)
