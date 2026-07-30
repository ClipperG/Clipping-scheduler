import threading
import time
from datetime import datetime

from backend.database.database import SessionLocal
from backend.models.schedule import Schedule
from backend.models.video import Video


def worker():

    print("✅ Schedule monitor worker started")


    while True:

        print(
            f"🔍 Checking scheduled posts... {datetime.now()}"
        )


        db = SessionLocal()


        try:

            posts = (
                db.query(Schedule)
                .filter(
                    Schedule.status == "scheduled"
                )
                .all()
            )


            print(
                f"📋 Found {len(posts)} scheduled record(s)"
            )


            for post in posts:


                video = (
                    db.query(Video)
                    .filter(
                        Video.id == post.video_id
                    )
                    .first()
                )


                if not video:

                    print(
                        "❌ Video missing"
                    )

                    post.status = "failed"

                    continue



                print(
                    "========================================"
                )

                print(
                    "📅 Scheduled already"
                )

                print(
                    f"Video: {video.filename}"
                )

                print(
                    f"Status: {video.status}"
                )

                print(
                    f"Time: {post.scheduled_time}"
                )

                print(
                    "========================================"
                )


            db.commit()



        except Exception as e:

            db.rollback()

            print(
                f"❌ Schedule worker error: {e}"
            )


        finally:

            db.close()



        time.sleep(60)



def start_buffer_worker():

    thread = threading.Thread(
        target=worker,
        daemon=True,
    )


    thread.start()