from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.database.database import SessionLocal
from backend.models.account import BufferAccount
from backend.models.video import Video
from backend.models.channel_video_queue import ChannelVideoQueue
from backend.models.schedule import Schedule

from backend.services.caption_service import get_random_caption
from backend.services.hashtag_service import get_random_hashtags
from backend.services.buffer_service import upload_to_single_channel

UTC = ZoneInfo("UTC")

# First upload = 2 minutes from now
# Every upload after that = 2 hours later
UPLOAD_INTERVAL = timedelta(hours=2)
FIRST_UPLOAD_DELAY = timedelta(minutes=2)


def get_next_slot(db, channel_name: str):
    now = datetime.now(UTC)

    last_schedule = (
        db.query(Schedule)
        .filter(Schedule.channel == channel_name)
        .order_by(Schedule.scheduled_time.desc())
        .first()
    )

    if last_schedule is None:
        return now + FIRST_UPLOAD_DELAY

    last_time = last_schedule.scheduled_time

    # SQLite returns naive datetimes
    if last_time.tzinfo is None:
        last_time = last_time.replace(tzinfo=UTC)

    if last_time <= now:
        return now + FIRST_UPLOAD_DELAY

    return last_time + UPLOAD_INTERVAL


def run_channel_scheduler():
    db = SessionLocal()

    try:
        accounts = (
            db.query(BufferAccount)
            .filter(BufferAccount.enabled == True)
            .order_by(BufferAccount.id)
            .all()
        )

        for account in accounts:

            queue_item = (
                db.query(ChannelVideoQueue)
                .filter(
                    ChannelVideoQueue.channel_id == account.id,
                    ChannelVideoQueue.posted == False,
                )
                .order_by(ChannelVideoQueue.queue_position.asc())
                .first()
            )

            if queue_item is None:
                print(f"{account.name}: queue empty")
                continue

            video = (
                db.query(Video)
                .filter(Video.id == queue_item.video_id)
                .first()
            )

            if video is None:
                continue

            caption = get_random_caption()
            hashtags = get_random_hashtags()

            text = caption
            if hashtags:
                text += f"\n\n{hashtags}"

            next_slot = get_next_slot(db, account.name)

            due_at = (
                next_slot
                .astimezone(UTC)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )

            result = upload_to_single_channel(
                account=account,
                video_url=video.r2_url,
                caption=text,
                due_at=due_at,
            )

            create_post = result.get("data", {}).get("createPost", {})

            if create_post.get("__typename") == "PostActionSuccess":

                queue_item.posted = True

                db.add(
                    Schedule(
                        video_id=video.id,
                        channel=account.name,
                        scheduled_time=next_slot,
                        status="scheduled",
                    )
                )

                db.commit()

                print(
                    f"✅ Scheduled {video.filename} -> "
                    f"{account.name} @ {next_slot}"
                )

            else:
                db.rollback()

                print(
                    f"❌ Failed scheduling {video.filename} -> "
                    f"{account.name}"
                )
                print(create_post)

    finally:
        db.close()