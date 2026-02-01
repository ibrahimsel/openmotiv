"""Background tasks for robot fleet management."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select

from app.db.session import get_sync_session
from app.models.robot import Robot, RobotStatus
from app.worker import celery_app


@celery_app.task(name="app.tasks.robots.check_fleet_health")
def check_fleet_health() -> dict:
    """
    Periodic task: Check health of all robots in the fleet.
    
    - Mark robots as offline if no update in 5 minutes
    - Alert on low battery levels
    - Collect fleet statistics
    """
    stats = {
        "total": 0,
        "online": 0,
        "offline": 0,
        "low_battery": 0,
        "marked_offline": 0,
    }
    
    with get_sync_session() as session:
        # Get all robots
        result = session.execute(select(Robot))
        robots = result.scalars().all()
        
        stats["total"] = len(robots)
        offline_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        for robot in robots:
            # Check if robot should be marked offline
            if (
                robot.status not in (RobotStatus.OFFLINE, RobotStatus.MAINTENANCE)
                and robot.updated_at < offline_threshold
            ):
                robot.status = RobotStatus.OFFLINE
                stats["marked_offline"] += 1
            
            # Count statistics
            if robot.status == RobotStatus.OFFLINE:
                stats["offline"] += 1
            else:
                stats["online"] += 1
            
            # Check battery level
            if robot.battery_level is not None and robot.battery_level < 20:
                stats["low_battery"] += 1
    
    return stats


@celery_app.task(name="app.tasks.robots.send_robot_command")
def send_robot_command(robot_id: str, command: str, payload: dict | None = None) -> dict:
    """
    Send a command to a specific robot.
    
    In a real system, this would communicate with the robot via
    MQTT, ROS2, or another protocol. Here we simulate it.
    """
    robot_uuid = UUID(robot_id)
    
    with get_sync_session() as session:
        result = session.execute(select(Robot).where(Robot.id == robot_uuid))
        robot = result.scalar_one_or_none()
        
        if not robot:
            return {"success": False, "error": "Robot not found"}
        
        # Simulate command handling
        if command == "return_to_base":
            robot.status = RobotStatus.ACTIVE
            message = f"Robot {robot.name} returning to base"
        elif command == "start_charging":
            robot.status = RobotStatus.CHARGING
            message = f"Robot {robot.name} started charging"
        elif command == "emergency_stop":
            robot.status = RobotStatus.IDLE
            message = f"Robot {robot.name} emergency stopped"
        else:
            message = f"Unknown command: {command}"
    
    return {"success": True, "message": message, "robot_id": robot_id}
