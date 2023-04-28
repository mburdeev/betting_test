import uuid
import time
import decimal
import asyncio

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.config import DATABASE_URL
from app.db.session import Base
from app.db import models
from app import schemas, services


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
def engine():
    engine = create_async_engine(DATABASE_URL)
    yield engine
    engine.sync_engine.dispose()


@pytest_asyncio.fixture()
async def create(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session(engine, create):
    async with AsyncSession(engine) as session:
        yield session


@pytest.mark.asyncio
async def test_create_event_on_db(session: AsyncSession):
    # debug event
    event_id = uuid.uuid4()
    event = models.Event(
        id=event_id,
        coefficient=decimal.Decimal("3.34"),
        deadline=int(time.time()),
        state=schemas.EventState.NEW,
    )
    session.add(event)
    await session.commit()
    stmt = sa.select(models.Event).where(models.Event.id == event_id)
    assert len((await session.execute(stmt)).scalars().all()) == 1


@pytest.mark.asyncio
async def test_create_bet(session: AsyncSession):
    # create debug event
    event_id = uuid.uuid4()
    event = models.Event(
        id=event_id,
        coefficient=decimal.Decimal("3.34"),
        deadline=int(time.time()) + 600,
        state=schemas.EventState.NEW,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)

    bet_create = schemas.BetCreate(
        event_id=event.id, amount=decimal.Decimal("50000.00")
    )
    bet = await services.bets.create_bet(session, bet_create)
    stmt = sa.select(models.Bet).where(models.Bet.id == bet.id)
    assert len((await session.execute(stmt)).scalars().all()) == 1


@pytest.mark.asyncio
async def test_update_bet_state(session: AsyncSession):
    # create debug event
    event_id = uuid.uuid4()
    event = models.Event(
        id=event_id,
        coefficient=decimal.Decimal("3.34"),
        deadline=int(time.time()) + 600,
        state=schemas.EventState.NEW,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    event_id = event.id

    # create debug bet
    bet_create = schemas.BetCreate(
        event_id=event_id, amount=decimal.Decimal("50000.00")
    )
    bet = await services.bets.create_bet(session, bet_create)

    assert bet.state == schemas.BetState.WAIT

    await services.bets.update_bet_state_by_event(
        session, event_id, schemas.BetState.WIN
    )

    stmt = sa.select(models.Bet).where(models.Bet.event_id == event_id).limit(1)
    bet = (await session.execute(stmt)).scalar()

    assert bet.state == schemas.BetState.WIN
