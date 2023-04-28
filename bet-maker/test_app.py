import uuid
import time
import decimal

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.config import DATABASE_URL
from app.db.session import Base
from app.db import models
from app import schemas


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
async def test_create_event_on_db(session):
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
