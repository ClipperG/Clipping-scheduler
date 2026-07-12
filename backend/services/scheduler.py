from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.database.database import SessionLocal
from backend.models.video import Video
from backend.models.schedule import Schedule

from backend.services.caption_service import get_random_caption
from backend.services.hashtag_service import get_random_hashtags
from backend.services.buffer_service import upload_to_buffer


START_HOUR = 8
GAP_HOURS = 2


def generate_schedule(video_id: int):
    db = SessionLocal()

    try:
        video = (
            db.query(Video)
            .filter(Video.id == video_id)
            .first()
        )

        if not video:
            return {
                "success": False,
                "message": "Video not found",
            }

        if not video.r2_url:
            return {
                "success": False,
                "message": "Video has no R2 URL",
            }

                # Find latest scheduled post
        last = (
            db.query(Schedule)
            .order_by(Schedule.scheduled_time.desc())
            .first()
        )

        now = datetime.now()

        print("NOW :", now)
        print("LAST:", last.scheduled_time if last else None)

        if last and last.scheduled_time > now:
            next_time = last.scheduled_time + timedelta(hours=GAP_HOURS)
        else:
            next_time = now.replace(
                hour=START_HOUR,
                minute=0,
                second=0,
                microsecond=0,
            )

            while next_time <= now:
                next_time += timedelta(hours=GAP_HOURS)

        next_time = next_time.replace(
            minute=0,
            second=0,
            microsecond=0,
        )

        # Build caption
        caption = get_random_caption()
        hashtags = get_random_hashtags()

        post_text = caption

        if hashtags:
            post_text += f"\n\n{hashtags}"

        # Convert Tirana time -> UTC
        local_time = next_time.replace(
            tzinfo=ZoneInfo("Europe/Tirane")
        )

        due_at = (
            local_time
            .astimezone(ZoneInfo("UTC"))
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        print(f"Scheduling Buffer for {due_at}")

        result = upload_to_buffer(
            video_url=video.r2_url,
            caption=post_text,
            due_at=due_at,
        )

        instagram = result["instagram"]["data"]["createPost"]
        youtube = result["youtube"]["data"]["createPost"]

        if (
            instagram["__typename"] != "PostActionSuccess"
            or youtube["__typename"] != "PostActionSuccess"
        ):
            return {
                "success": False,
                "instagram": instagram,
                "youtube": youtube,
            }

        # Save Buffer IDs
        video.instagram_buffer_id = instagram["post"]["id"]
        video.youtube_buffer_id = youtube["post"]["id"]

        print("Instagram Buffer ID:", video.instagram_buffer_id)
        print("YouTube Buffer ID:", video.youtube_buffer_id)

        db.add(
            Schedule(
                video_id=video.id,
                channel="ALL",
                scheduled_time=next_time,
                status="scheduled",
            )
        )

        video.status = "scheduled"

        db.commit()

        return {
            "success": True,
            "video": video.filename,
            "scheduled_for": next_time.strftime("%Y-%m-%d %H:%M"),
        }

    finally:
        db.close()