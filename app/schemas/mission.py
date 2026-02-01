from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.mission import MissionPriority, MissionStatus


class MissionBase(BaseModel):
    """Base mission schema."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    priority: MissionPriority = MissionPriority.NORMAL
    target_x: float | None = None
    target_y: float | None = None
    target_z: float | None = None
    scheduled_at: datetime | None = None


class MissionCreate(MissionBase):
    """Schema for creating a new mission."""

    pass


class MissionUpdate(BaseModel):
    """Schema for updating a mission."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    priority: MissionPriority | None = None
    status: MissionStatus | None = None
    target_x: float | None = None
    target_y: float | None = None
    target_z: float | None = None
    scheduled_at: datetime | None = None
    progress: float | None = Field(None, ge=0, le=100)


class MissionAssign(BaseModel):
    """Schema for assigning a robot to a mission."""

    robot_id: UUID


class MissionRead(MissionBase):
    """Schema for reading mission data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: MissionStatus
    progress: float
    robot_id: UUID | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
