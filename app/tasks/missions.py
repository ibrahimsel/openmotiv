"""Background tasks for mission management."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.db.session import get_sync_session
from app.models.mission import Mission, MissionStatus
from app.models.robot import Robot, RobotStatus
from app.worker import celery_app


@celery_app.task(name="app.tasks.missions.process_scheduled_missions")
def process_scheduled_missions() -> dict:
    """
    Periodic task: Process missions that are scheduled to start.
    
    - Find missions with scheduled_at in the past that are still pending
    - Auto-assign to available robots if possible
    - Start assigned missions
    """
    stats = {
        "processed": 0,
        "started": 0,
        "auto_assigned": 0,
    }
    
    now = datetime.now(timezone.utc)
    
    with get_sync_session() as session:
        # Find scheduled missions ready to start
        result = session.execute(
            select(Mission).where(
                Mission.scheduled_at <= now,
                Mission.status.in_([MissionStatus.PENDING, MissionStatus.ASSIGNED]),
            )
        )
        missions = result.scalars().all()
        
        for mission in missions:
            stats["processed"] += 1
            
            # If pending, try to auto-assign
            if mission.status == MissionStatus.PENDING:
                # Find an idle robot
                robot_result = session.execute(
                    select(Robot).where(Robot.status == RobotStatus.IDLE).limit(1)
                )
                robot = robot_result.scalar_one_or_none()
                
                if robot:
                    mission.robot_id = robot.id
                    mission.status = MissionStatus.ASSIGNED
                    stats["auto_assigned"] += 1
            
            # If assigned, start the mission
            if mission.status == MissionStatus.ASSIGNED and mission.robot_id:
                mission.status = MissionStatus.IN_PROGRESS
                mission.started_at = now
                stats["started"] += 1
                
                # Update robot status
                robot_result = session.execute(
                    select(Robot).where(Robot.id == mission.robot_id)
                )
                robot = robot_result.scalar_one_or_none()
                if robot:
                    robot.status = RobotStatus.ACTIVE
    
    return stats


@celery_app.task(name="app.tasks.missions.simulate_mission_progress")
def simulate_mission_progress(mission_id: str) -> dict:
    """
    Simulate mission progress over time.
    
    In a real system, progress would come from robot telemetry.
    This task simulates a mission completing in steps.
    """
    mission_uuid = UUID(mission_id)
    
    with get_sync_session() as session:
        result = session.execute(
            select(Mission).where(Mission.id == mission_uuid)
        )
        mission = result.scalar_one_or_none()
        
        if not mission:
            return {"success": False, "error": "Mission not found"}
        
        if mission.status != MissionStatus.IN_PROGRESS:
            return {"success": False, "error": f"Mission not in progress: {mission.status}"}
        
        # Increment progress
        new_progress = min(mission.progress + 25.0, 100.0)
        mission.progress = new_progress
        
        # Complete if 100%
        if new_progress >= 100.0:
            mission.status = MissionStatus.COMPLETED
            mission.completed_at = datetime.now(timezone.utc)
            
            # Set robot back to idle
            if mission.robot_id:
                robot_result = session.execute(
                    select(Robot).where(Robot.id == mission.robot_id)
                )
                robot = robot_result.scalar_one_or_none()
                if robot:
                    robot.status = RobotStatus.IDLE
    
    return {
        "success": True,
        "mission_id": mission_id,
        "progress": new_progress,
        "completed": new_progress >= 100.0,
    }


@celery_app.task(name="app.tasks.missions.schedule_mission")
def schedule_mission(mission_id: str, delay_seconds: int = 0) -> dict:
    """
    Schedule a mission to start after a delay.
    
    This demonstrates Celery's countdown/eta feature.
    """
    # Chain: wait -> start simulating progress
    if delay_seconds > 0:
        simulate_mission_progress.apply_async(
            args=[mission_id],
            countdown=delay_seconds,
        )
        return {"scheduled": True, "mission_id": mission_id, "delay": delay_seconds}
    else:
        simulate_mission_progress.delay(mission_id)
        return {"scheduled": True, "mission_id": mission_id, "delay": 0}
