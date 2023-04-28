import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, services
from app.services import utils
from app.db import models


async def create_bet(db: AsyncSession, bet_create: schemas.BetCreate) -> models.Bet:
    "Создать ставку"
    # берем событие по которому делается ставка
    event = await services.events.get_event_by_id(db, bet_create.event_id, must_be=True)
    # проверяем что дедлайн события еще не истек
    if event.deadline <= utils.current_timestamp():
        # TODO ConflictError
        raise ValueError()
    # проверяем что результат события еще неизвестен, на всякий случай
    if event.state != schemas.EventState.NEW:
        raise ValueError()

    # сохраняем коэффициент: в случае если он измениться,
    # нам надо знать какой он был на момент ставки
    bet = models.Bet(
        **bet_create.dict(),
        coefficient=event.coefficient,
        state=schemas.BetState.WAIT,
        created_at=utils.current_timestamp()
    )
    db.add(bet)
    await db.commit()
    await db.refresh(bet)

    return bet


async def get_bets(db: AsyncSession) -> list[models.Bet]:
    "Получить список всех ставок"
    stmt = sa.select(models.Bet)
    result = await db.execute(stmt)
    bets = result.scalars().all()
    return bets


async def update_bet_state_by_event(
    db: AsyncSession, event_id: uuid.UUID, bet_state: schemas.BetState
) -> None:
    "Обновить статус ставки по событию, возвращает кол-во обновленных записей"
    stmt = (
        sa.update(models.Bet)
        .where(models.Bet.event_id == event_id)
        .values({models.Bet.state: bet_state})
    )
    result = await db.execute(stmt)
    await db.commit()
