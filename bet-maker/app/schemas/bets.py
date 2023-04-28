import enum
import uuid
import decimal

from pydantic import BaseModel, Field, validator


class BetState(enum.Enum):
    WAIT = 1
    WIN = 2
    LOSE = 3


class BetBase(BaseModel):
    event_id: uuid.UUID
    amount: decimal.Decimal

    @validator("amount")
    def check_amount(cls, value: decimal.Decimal):
        if value <= 0:
            raise ValueError("The bet amount must be strictly greater than zero")
        if value.as_tuple().exponent < -2:
            raise ValueError("The bet amount must be with two decimal places")
        return value


class BetCreate(BetBase):
    ...


class Bet(BetBase):
    id: uuid.UUID = Field(alias="bet_id")
    state: BetState
    coefficient: decimal.Decimal
    created_at: int

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
