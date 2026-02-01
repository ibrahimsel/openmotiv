"""Tests for mission endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mission import Mission, MissionPriority, MissionStatus
from app.models.robot import Robot


@pytest.mark.asyncio
async def test_list_missions_empty(client: AsyncClient, auth_headers: dict) -> None:
    """Test listing missions when none exist."""
    response = await client.get("/api/v1/missions", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_mission(client: AsyncClient, auth_headers: dict) -> None:
    """Test creating a mission."""
    response = await client.post(
        "/api/v1/missions",
        headers=auth_headers,
        json={
            "name": "Delivery Mission",
            "priority": "high",
            "target_x": 50.0,
            "target_y": 75.0,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Delivery Mission"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_get_mission(client: AsyncClient, auth_headers: dict, db_session: AsyncSession) -> None:
    """Test getting a specific mission."""
    mission = Mission(
        id=uuid4(),
        name="Test Mission",
        status=MissionStatus.PENDING,
        priority=MissionPriority.NORMAL,
    )
    db_session.add(mission)
    await db_session.commit()

    response = await client.get(f"/api/v1/missions/{mission.id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["name"] == "Test Mission"


@pytest.mark.asyncio
async def test_assign_mission_to_robot(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_robot: Robot
) -> None:
    """Test assigning a robot to a mission."""
    mission = Mission(
        id=uuid4(),
        name="Assignment Test",
        status=MissionStatus.PENDING,
        priority=MissionPriority.NORMAL,
    )
    db_session.add(mission)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/missions/{mission.id}/assign",
        headers=auth_headers,
        json={"robot_id": str(test_robot.id)},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["robot_id"] == str(test_robot.id)
    assert data["status"] == "assigned"


@pytest.mark.asyncio
async def test_delete_mission(client: AsyncClient, auth_headers: dict, db_session: AsyncSession) -> None:
    """Test deleting a mission."""
    mission = Mission(
        id=uuid4(),
        name="To Delete",
        status=MissionStatus.PENDING,
        priority=MissionPriority.NORMAL,
    )
    db_session.add(mission)
    await db_session.commit()

    response = await client.delete(f"/api/v1/missions/{mission.id}", headers=auth_headers)

    assert response.status_code == 204
