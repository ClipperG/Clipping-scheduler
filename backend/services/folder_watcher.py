import shutil
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from backend.database.database import SessionLocal
from backend.models.video import Video

WATCH_FOLDER = Path(r"C:\Users\rexhe\Clipping-scheduler\incoming")
FAILED_FOLDER = Path(r"C:\Users\rexhe\Clipping-scheduler\failed")

WATCH_FOLDER.mkdir(exist_ok=True)
FAILED_FOLDER.mkdir(exist_ok=True)

observer = Observer()


class VideoHandler(FileSystemEventHandler):

    def process_file(self, filepath):
        filepath = Path(filepath)

        if not filepath.exists():
            return

        if filepath.suffix.lower() != ".mp4":
            return

        print(f"🎬 Detected {filepath.name}")

        db = SessionLocal()

        try:
            existing = (
                db.query(Video)
                .filter(Video.filename == filepath.name)
                .first()
            )

            if existing:
                return

            video = Video(
    filename=filepath.name,
    status="waiting",
    r2_url=None,
)

            db.add(video)
            db.commit()

            print(f"✅ Queued {filepath.name}")

        except Exception as e:
            db.rollback()
            print(e)

            try:
                if filepath.exists():
                    shutil.move(
                        str(filepath),
                        str(FAILED_FOLDER / filepath.name)
                    )
            except:
                pass

        finally:
            db.close()

    def on_created(self, event):
        if event.is_directory:
            return

        self.process_file(event.src_path)


def initial_scan(handler):
    print("🔍 Initial scan...")

    for file in WATCH_FOLDER.glob("*.mp4"):
        handler.process_file(file)

    print("✅ Scan complete")


def start_watcher():
    handler = VideoHandler()

    initial_scan(handler)

    observer.schedule(
        handler,
        str(WATCH_FOLDER),
        recursive=False,
    )

    observer.start()

    print(f"👀 Watching {WATCH_FOLDER}")
