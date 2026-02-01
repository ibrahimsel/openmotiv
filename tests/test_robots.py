"""Tests for robot endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.models.robot import Robot


@pytest.mark.asyncio
async def test_list_robots_empty(client: AsyncClient, auth_headers: dict) -> None:
    """Test listing robots when none exist."""
    response = await client.get("/api/v1/robots", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_robots(client: AsyncClient, auth_headers: dict, test_robot: Robot) -> None:
    """Test listing robots."""
    response = await client.get("/api/v1/robots", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == test_robot.name


@pytest.mark.asyncio
async def test_create_robot(client: AsyncClient, auth_headers: dict) -> None:
    """Test creating a robot."""
    response = await client.post(
        "/api/v1/robots",
        headers=auth_headers,
        json={
            "name": "New Robot",
            "serial_number": "NEW-001",
            "robot_type": "amr",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Robot"
    assert data["status"] == "offline"


@pytest.mark.asyncio
async def test_get_robot(client: AsyncClient, auth_headers: dict, test_robot: Robot) -> None:
    """Test getting a specific robot."""
    response = await client.get(f"/api/v1/robots/{test_robot.id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == str(test_robot.id)


@pytest.mark.asyncio
async def test_get_robot_not_found(client: AsyncClient, auth_headers: dict) -> None:
    """Test getting non-existent robot fails."""
    response = await client.get(f"/api/v1/robots/{uuid4()}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_robot_status(client: AsyncClient, auth_headers: dict, test_robot: Robot) -> None:
    """Test updating robot status."""
    response = await client.patch(
        f"/api/v1/robots/{test_robot.id}/status",
        headers=auth_headers,
        json={"status": "active", "battery_level": 75.5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["battery_level"] == 75.5


@pytest.mark.asyncio
async def test_delete_robot(client: AsyncClient, auth_headers: dict, test_robot: Robot) -> None:
    """Test deleting a robot."""
    response = await client.delete(f"/api/v1/robots/{test_robot.id}", headers=auth_headers)

    assert response.status_code == 204
