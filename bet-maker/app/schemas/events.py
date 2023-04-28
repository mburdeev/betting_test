import enum
import uuid
import decimal

from pydantic import BaseModel, Field


class EventState(enum.Enum):
    NEW = 1
    FINISHED_WIN = 2
    FINISHED_LOSE = 3


class Event(BaseModel):
    id: uuid.UUID = Field(alias="event_id")
    coefficient: decimal.Decimal
    deadline: int
    state: EventState

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
