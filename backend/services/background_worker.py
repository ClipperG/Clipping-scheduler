import shutil
import threading
import time
from pathlib import Path

from backend.database.database import SessionLocal
from backend.models.video import Video
from backend.services.r2_service import upload_video
from backend.services.daily_pipeline import process_single_video


WATCH_FOLDER = Path(r"C:\Users\rexhe\Clipping-scheduler\incoming")
UPLOADED_FOLDER = Path(r"C:\Users\rexhe\Clipping-scheduler\uploaded")
FAILED_FOLDER = Path(r"C:\Users\rexhe\Clipping-scheduler\failed")


UPLOADED_FOLDER.mkdir(exist_ok=True)
FAILED_FOLDER.mkdir(exist_ok=True)


def worker():
    print("✅ Upload queue worker started")

    while True:

        db = SessionLocal()

        try:

            video = (
                db.query(Video)
                .filter(Video.status == "waiting")
                .order_by(Video.id.asc())
                .first()
            )


            if video is None:
                time.sleep(2)
                continue


            filepath = WATCH_FOLDER / video.filename


            if not filepath.exists():

                print(
                    f"❌ Missing file: {video.filename}"
                )

                video.status = "failed"
                db.commit()

                continue


            print()
            print("=====================================")
            print(f"🎬 Processing {video.filename}")
            print("=====================================")


            try:

                print(
                    "☁ Uploading to Cloudflare R2..."
                )


                r2_url = upload_video(
                    str(filepath)
                )


                print(
                    f"✅ Uploaded: {r2_url}"
                )


                video.r2_url = r2_url
                video.status = "uploaded"

                db.commit()


                #
                # NEW:
                # Immediately assign + schedule
                #

                pipeline = process_single_video(
                    video.id
                )


                if pipeline.get("success"):

                    print(
                        f"🚀 {video.filename} "
                        "assigned and scheduled"
                    )

                else:

                    print(
                        f"⚠️ Pipeline failed: "
                        f"{pipeline}"
                    )


                destination = (
                    UPLOADED_FOLDER /
                    video.filename
                )


                shutil.move(
                    str(filepath),
                    str(destination)
                )


                print(
                    f"📦 Moved to {destination}"
                )


            except Exception as e:

                print(
                    f"❌ Upload failed: {e}"
                )


                video.status = "failed"
                db.commit()


                try:

                    if filepath.exists():

                        destination = (
                            FAILED_FOLDER /
                            video.filename
                        )

                        shutil.move(
                            str(filepath),
                            str(destination)
                        )


                        print(
                            f"📦 Moved to {destination}"
                        )


                except Exception:
                    pass



        except Exception as e:

            print(
                f"❌ Worker error: {e}"
            )

            db.rollback()



        finally:

            db.close()



        time.sleep(2)



def start_background_worker():

    thread = threading.Thread(
        target=worker,
        daemon=True,
    )

    thread.start()

    print(
        "✅ Background worker started"
    )