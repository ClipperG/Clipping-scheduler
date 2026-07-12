from backend.database.database import SessionLocal

from backend.models.video import Video
from backend.models.schedule import Schedule

from backend.services.buffer_service import upload_to_buffer


def upload_all():
    db = SessionLocal()

    schedules = (
        db.query(Schedule)
        .filter(Schedule.status == "scheduled")
        .all()
    )

    for schedule in schedules:
        video = (
            db.query(Video)
            .filter(Video.id == schedule.video_id)
            .first()
        )

        if not video:
            continue

        if not video.r2_url:
            print(f"❌ {video.filename} has no R2 URL")
            continue

        print(f"📤 Uploading {video.filename}...")

        result = upload_to_buffer(
            video_url=video.r2_url,
            caption=video.filename,
        )

        print(result)

        schedule.status = "uploaded"

    db.commit()
    db.close()

    return True