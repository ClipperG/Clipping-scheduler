from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.core.settings import settings
from backend.database.database import SessionLocal
from backend.models.video import Video
from backend.models.account import BufferAccount
from backend.services.buffer_service import upload_to_single_channel
from backend.services.caption_service import get_random_caption


def get_next_schedule_time():
    now = datetime.now(ZoneInfo(settings.TIMEZONE))

    post_times = sorted(settings.post_times)

    for time_str in post_times:
        hour, minute = map(int, time_str.split(":"))

        candidate = now.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )

        if candidate > now:
            return candidate

    hour, minute = map(int, post_times[0].split(":"))

    tomorrow = now + timedelta(days=1)

    return tomorrow.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )


def schedule_single_video(video_id):
    """
    Schedule one assigned video to Buffer.
    """

    db = SessionLocal()

    try:

        video = (
            db.query(Video)
            .filter(Video.id == video_id)
            .first()
        )

        if not video:
            print(f"❌ Video {video_id} not found")
            return False

        channel = (
            db.query(BufferAccount)
            .filter(
                BufferAccount.id == video.assigned_channel_id
            )
            .first()
        )

        if not channel:
            print(f"❌ No channel assigned for {video.filename}")
            return False

        due = get_next_schedule_time()

        # Caption only (NO hashtags)
        text = get_random_caption()

        result = upload_to_single_channel(
            account=channel,
            video_url=video.r2_url,
            caption=text,
            due_at=due.isoformat(),
        )

        response = result["data"]["createPost"]

        if response["__typename"] != "PostActionSuccess":
            print(f"❌ Buffer failed for {video.filename}")
            print(response)
            return False

        video.status = "scheduled"
        video.scheduled_for = due.replace(tzinfo=None)

        db.commit()

        print(
            f"✅ Scheduled {video.filename} "
            f"on {channel.name} "
            f"for {due}"
        )

        return True

    except Exception as e:

        db.rollback()

        print(f"❌ Scheduler error: {e}")

        return False

    finally:

        db.close()