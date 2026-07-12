print("✅ schedule.py loaded")
from fastapi import APIRouter, HTTPException

from backend.database.database import SessionLocal
from backend.models.schedule import Schedule

router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int):
    db = SessionLocal()

    try:
        post = (
            db.query(Schedule)
            .filter(Schedule.id == schedule_id)
            .first()
        )

        if not post:
            raise HTTPException(404, "Schedule not found")

        db.delete(post)
        db.commit()

        return {
            "success": True
        }

    finally:
        db.close()