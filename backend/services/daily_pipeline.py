from backend.services.assignment_service import assign_videos
from backend.services.daily_scheduler import schedule_today
from backend.database.database import SessionLocal
from backend.models.account import BufferAccount
from backend.models.buffer_workspace import BufferWorkspace
from backend.models.video import Video


POSTS_PER_DAY = 3


def run_daily_pipeline_if_ready():
    """Run one complete batch only when every active channel can receive 3 clips."""
    db = SessionLocal()

    try:
        channel_count = (
            db.query(BufferAccount)
            .join(BufferWorkspace, BufferWorkspace.id == BufferAccount.workspace_id)
            .filter(BufferWorkspace.active == True)
            .filter(BufferAccount.enabled == True)
            .count()
        )
        available_clips = (
            db.query(Video)
            .filter(Video.status == "uploaded")
            .filter(Video.assigned_channel_id == None)
            .count()
        )
        pending_clips = (
            db.query(Video)
            .filter(Video.status == "assigned")
            .count()
        )
    finally:
        db.close()

    if channel_count == 0 or (available_clips == 0 and pending_clips == 0):
        return {
            "success": True,
            "scheduled": False,
            "available_clips": available_clips,
            "required_clips": required_clips,
        }

    return run_daily_pipeline()


def run_daily_pipeline():
    print("===================================")
    print("STARTING DAILY PIPELINE")
    print("===================================")

    assigned = assign_videos()

    print(f"Assigned {assigned['assigned']} videos.")

    scheduled = schedule_today()

    print(f"Scheduled {scheduled['scheduled']} posts.")

    print("PIPELINE COMPLETE")

    return {
        "success": True,
        "assigned": assigned["assigned"],
        "scheduled": scheduled["scheduled"],
    }
