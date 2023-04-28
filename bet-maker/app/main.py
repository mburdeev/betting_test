import asyncio

import uvicorn
import aio_pika
from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app import services, schemas
from app.db.session import get_session, init_models
from app.config import RABBITMQ_URL

app = FastAPI(title="bet-maker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await init_models()
    # check queue connect before listening
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    # run event listening
    asyncio.create_task(services.events.listen_events())


@app.get("/events", response_model=list[schemas.Event], tags=["events"])
async def get_events(db: AsyncSession = Depends(get_session)):
    return await services.events.get_active_events(db)


@app.post("/bet", response_model=schemas.Bet, tags=["bets"])
async def create_bet(
    bet_create: schemas.BetCreate, db: AsyncSession = Depends(get_session)
):
    return await services.bets.create_bet(db, bet_create)


@app.get("/bets", response_model=list[schemas.Bet], tags=["bets"])
async def get_bets(db: AsyncSession = Depends(get_session)):
    return await services.bets.get_bets(db)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8081, log_level="info", reload=True
    )
