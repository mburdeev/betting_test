import uuid

from sqlalchemy import Column, ForeignKey
from sqlalchemy import Integer, Enum, Numeric
from sqlalchemy.dialects import postgresql

from app import schemas
from app.db.session import Base


class Event(Base):
    "Событие"
    __tablename__ = "event"

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, index=True)
    coefficient = Column(Numeric(4, 2))
    deadline = Column(Integer)
    state = Column(Enum(schemas.EventState))


class Bet(Base):
    "Ставка"
    __tablename__ = "bet"

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(ForeignKey("event.id"))
    amount = Column(Numeric(10, 2))
    coefficient = Column(Numeric(4, 2))
    created_at = Column(Integer)
    state = Column(Enum(schemas.BetState))
