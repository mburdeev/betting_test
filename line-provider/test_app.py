import time
import uuid

import pytest
from httpx import AsyncClient

from app import app


@pytest.mark.asyncio
async def test_create_event():
    test_event = {
        "coefficient": 1.0,
        "deadline": int(time.time()) + 600,
        "state": 1,
    }

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        create_response = await ac.post("/event", json=test_event)

    assert create_response.status_code == 200
    event_id = create_response.json()["event_id"]
    test_event["event_id"] = event_id

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        response = await ac.get(f"/event/{event_id}")

    assert response.status_code == 200
    assert response.json() == test_event


@pytest.mark.asyncio
@pytest.mark.parametrize("wrong_coeff", [-2.22, 0, 1.2222])
async def test_wrong_coeff_on_create_event(wrong_coeff):
    test_event = {
        "coefficient": wrong_coeff,
        "deadline": int(time.time()) + 600,
        "state": 1,
    }

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        create_response = await ac.post("/event", json=test_event)

    assert create_response.status_code == 422


@pytest.mark.asyncio
async def test_update_event():
    test_event = {
        "coefficient": 1.0,
        "deadline": int(time.time()) + 600,
        "state": 1,
    }

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        create_response = await ac.post("/event", json=test_event)

    assert create_response.status_code == 200
    event_id = create_response.json()["event_id"]
    test_event["event_id"] = event_id

    updated_event = test_event.copy()
    updated_event["coefficient"] = 1.5

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        update_response = await ac.put(f"/events/{event_id}", json=updated_event)

    assert create_response.status_code == 200
    assert update_response.json() == updated_event

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        response = await ac.get(f"/event/{event_id}")

    assert response.status_code == 200
    assert response.json() == updated_event


# TODO попытка отредактировать завершенное событие
