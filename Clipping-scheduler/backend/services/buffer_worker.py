import threading
import time
from datetime import datetime

from zoneinfo import ZoneInfo

from backend.database.database import SessionLocal
from backend.models.schedule import Schedule
from backend.models.video import Video

from backend.services.buffer_service import upload_to_buffer
from backend.services.caption_service import get_random_caption
from backend.services.hashtag_service import get_random_hashtags


def worker():
    print("✅ Buffer worker started")

    while True:
        print(f"🔍 Checking schedule... {datetime.now()}")

        db = SessionLocal()

        try:
            now = datetime.now()

            posts = (
                db.query(Schedule)
                .filter(
                    Schedule.status == "scheduled",
                    Schedule.scheduled_time <= now,
                )
                .order_by(Schedule.scheduled_time)
                .all()
            )

            print(f"📋 Found {len(posts)} scheduled post(s)")

            for post in posts:

                video = (
                    db.query(Video)
                    .filter(Video.id == post.video_id)
                    .first()
                )

                if not video:
                    print("❌ Video not found")
                    post.status = "failed"
                    continue

                if not video.r2_url:
                    print(f"❌ {video.filename} has no R2 URL")
                    post.status = "failed"
                    continue

                caption = get_random_caption()
                hashtags = get_random_hashtags()

                post_text = caption

                if hashtags:
                    post_text += f"\n\n{hashtags}"

                print()
                print("========================================")
                print("🚀 Sending to Buffer")
                print(f"Video : {video.filename}")
                print(f"Time  : {post.scheduled_time}")
                print("========================================")

                # Convert local Tirane time to UTC for Buffer
                local_time = post.scheduled_time.replace(
                    tzinfo=ZoneInfo("Europe/Tirane")
                )

                due_at = (
                    local_time
                    .astimezone(ZoneInfo("UTC"))
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z")
                )

                print(f"Local time : {local_time}")
                print(f"UTC dueAt  : {due_at}")

                result = upload_to_buffer(
                    video_url=video.r2_url,
                    caption=post_text,
                    due_at=due_at,
                )

                instagram = result["instagram"]["data"]["createPost"]
                youtube = result["youtube"]["data"]["createPost"]

                if (
                    instagram["__typename"] == "PostActionSuccess"
                    and youtube["__typename"] == "PostActionSuccess"
                ):
                    print("✅ Successfully scheduled on Buffer")
                    post.status = "uploaded"
                    video.status = "posted"
                else:
                    print("❌ Buffer rejected upload")
                    print(instagram)
                    print(youtube)
                    post.status = "failed"

            db.commit()

        except Exception as e:
            db.rollback()
            print(f"❌ Buffer worker error: {e}")

        finally:
            db.close()

        time.sleep(60)


def start_buffer_worker():
    thread = threading.Thread(
        target=worker,
        daemon=True,
    )
    thread.start()