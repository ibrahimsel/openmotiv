from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.robot import RobotStatus, RobotType


class RobotBase(BaseModel):
    """Base robot schema with common fields."""

    name: str = Field(..., min_length=1, max_length=100)
    serial_number: str = Field(..., min_length=1, max_length=50)
    robot_type: RobotType = RobotType.AMR
    description: str | None = None


class RobotCreate(RobotBase):
    """Schema for creating a new robot."""

    pass


class RobotUpdate(BaseModel):
    """Schema for updating a robot."""

    name: str | None = Field(None, min_length=1, max_length=100)
    robot_type: RobotType | None = None
    description: str | None = None
    firmware_version: str | None = None


class RobotStatusUpdate(BaseModel):
    """Schema for updating robot status and telemetry."""

    status: RobotStatus | None = None
    location_x: float | None = None
    location_y: float | None = None
    location_z: float | None = None
    heading: float | None = Field(None, ge=0, lt=360)
    battery_level: float | None = Field(None, ge=0, le=100)


class RobotRead(RobotBase):
    """Schema for reading robot data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: RobotStatus
    location_x: float | None
    location_y: float | None
    location_z: float | None
    heading: float | None
    firmware_version: str | None
    battery_level: float | None
    created_at: datetime
    updated_at: datetime
