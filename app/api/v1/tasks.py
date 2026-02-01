"""API endpoints for triggering background tasks."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AdminUser
from app.tasks.missions import schedule_mission, simulate_mission_progress
from app.tasks.robots import check_fleet_health, send_robot_command

router = APIRouter(prefix="/tasks", tags=["tasks"])


class CommandRequest(BaseModel):
    """Request body for robot commands."""
    command: str
    payload: dict | None = None


class ScheduleRequest(BaseModel):
    """Request body for scheduling missions."""
    delay_seconds: int = 0


class TaskResponse(BaseModel):
    """Response for task submissions."""
    task_id: str
    status: str
    message: str


@router.post("/robots/{robot_id}/command", response_model=TaskResponse)
async def trigger_robot_command(
    robot_id: UUID,
    request: CommandRequest,
    current_user: AdminUser,
) -> TaskResponse:
    """
    Send a command to a robot via background task.
    
    Available commands:
    - return_to_base: Send robot back to charging station
    - start_charging: Begin charging sequence
    - emergency_stop: Immediately stop robot
    """
    task = send_robot_command.delay(str(robot_id), request.command, request.payload)
    
    return TaskResponse(
        task_id=task.id,
        status="queued",
        message=f"Command '{request.command}' queued for robot {robot_id}",
    )


@router.post("/missions/{mission_id}/simulate", response_model=TaskResponse)
async def trigger_mission_simulation(
    mission_id: UUID,
    current_user: AdminUser,
) -> TaskResponse:
    """
    Simulate mission progress (for testing/demo).
    
    Each call advances progress by 25%.
    """
    task = simulate_mission_progress.delay(str(mission_id))
    
    return TaskResponse(
        task_id=task.id,
        status="queued",
        message=f"Mission simulation queued for {mission_id}",
    )


@router.post("/missions/{mission_id}/schedule", response_model=TaskResponse)
async def trigger_mission_schedule(
    mission_id: UUID,
    request: ScheduleRequest,
    current_user: AdminUser,
) -> TaskResponse:
    """
    Schedule a mission to start after a delay.
    """
    task = schedule_mission.delay(str(mission_id), request.delay_seconds)
    
    return TaskResponse(
        task_id=task.id,
        status="queued",
        message=f"Mission {mission_id} scheduled with {request.delay_seconds}s delay",
    )


@router.post("/fleet/health-check", response_model=TaskResponse)
async def trigger_fleet_health_check(
    current_user: AdminUser,
) -> TaskResponse:
    """
    Trigger an immediate fleet health check.
    
    Normally runs every 60 seconds automatically.
    """
    task = check_fleet_health.delay()
    
    return TaskResponse(
        task_id=task.id,
        status="queued",
        message="Fleet health check queued",
    )


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: AdminUser,
) -> dict:
    """
    Get the status of a background task.
    """
    from app.worker import celery_app
    
    result = celery_app.AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready(),
    }
    
    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.result)
    
    return response
