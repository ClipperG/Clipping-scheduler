from datetime import datetime, timedelta, timezone

from backend.database.database import SessionLocal
from backend.models.video import Video
from backend.models.account import BufferAccount
from backend.models.buffer_workspace import BufferWorkspace
from backend.services.buffer_service import upload_to_single_channel
from backend.services.caption_service import get_random_caption
from backend.services.hashtag_service import get_random_hashtags


POSTS_PER_DAY = 3

SCHEDULE_INTERVAL = timedelta(hours=8)
FIRST_POST_DELAY = timedelta(minutes=5)


def schedule_today():
    db = SessionLocal()

    try:
        channels = (
            db.query(BufferAccount)
            .join(BufferWorkspace, BufferWorkspace.id == BufferAccount.workspace_id)
            .filter(BufferWorkspace.active == True)
            .filter(BufferAccount.enabled == True)
            .order_by(BufferAccount.id)
            .all()
        )

        scheduled = 0

        for channel in channels:

            videos = (
                db.query(Video)
                .filter(Video.assigned_channel_id == channel.id)
                .filter(Video.status == "assigned")
                .order_by(Video.id)
                .all()
            )

            if not videos:
                continue

            last_scheduled = (
                db.query(Video.scheduled_for)
                .filter(Video.assigned_channel_id == channel.id)
                .filter(Video.status == "scheduled")
                .order_by(Video.scheduled_for.desc())
                .first()
            )

            first_due = datetime.now(timezone.utc).replace(second=0, microsecond=0)
            first_due += FIRST_POST_DELAY

            if last_scheduled and last_scheduled[0]:
                last_due = last_scheduled[0].replace(tzinfo=timezone.utc)
                first_due = max(first_due, last_due + SCHEDULE_INTERVAL)

            for position, video in enumerate(videos):
                due = first_due + position * SCHEDULE_INTERVAL

                caption = get_random_caption()
                hashtags = get_random_hashtags()

                text = caption
                if hashtags:
                    text += f"\n\n{hashtags}"

                result = upload_to_single_channel(
                    account=channel,
                    video_url=video.r2_url,
                    caption=text,
                    due_at=due.isoformat().replace("+00:00", "Z"),
                )

                response = result["data"]["createPost"]

                if response["__typename"] != "PostActionSuccess":
                    print(f"❌ Failed to schedule {video.filename} on {channel.name}")
                    print(response)
                    continue

                video.status = "scheduled"
                video.scheduled_for = due.replace(tzinfo=None)

                scheduled += 1

                # Persist every successful Buffer post immediately.  If a later
                # post fails, this clip remains scheduled and will never retry.
                db.commit()

                print(
                    f"✅ {channel.name} -> {video.filename} scheduled for {due}"
                )

        return {
            "success": True,
            "channels": len(channels),
            "scheduled": scheduled,
        }

    finally:
        db.close()
