print("🔥 LOADED THE CORRECT MAIN.PY")

from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from typing import List
import shutil

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Request,
    Body,
    HTTPException,
)

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


# Core
from backend.core.settings import settings
from backend.database.database import Base, engine, SessionLocal
from backend.database.migrations import migrate_video_assignments


# Models
from backend.models.video import Video
from backend.models.account import BufferAccount
from backend.models.schedule import Schedule
from backend.models.channel_video_queue import ChannelVideoQueue


# Routers
from backend.api.buffer_accounts import router as buffer_accounts_router
from backend.api.schedule import router as schedule_router


# Services
from backend.services.channel_sync import sync_channels
from backend.services.daily_pipeline import (
    run_daily_pipeline,
    run_daily_pipeline_if_ready,
)
from backend.services.daily_scheduler import schedule_today
from backend.services.assignment_service import assign_videos
from backend.services.health_check import health_check
from backend.services.folder_watcher import start_watcher
from backend.services.background_worker import start_background_worker




@asynccontextmanager
async def lifespan(app: FastAPI):

    print("🚀 Starting application...")

    start_watcher()

    start_background_worker()

    yield

    print("🛑 Shutting down...")


app = FastAPI(
    title="Clipping Scheduler",
    lifespan=lifespan,
)



Base.metadata.create_all(
    bind=engine
)


migrate_video_assignments(
    engine
)


app.include_router(schedule_router)

app.include_router(buffer_accounts_router)


BASE_DIR = Path(__file__).parent
@app.post("/buffer/sync")
def buffer_sync():

    result = sync_channels()


    if (
        not result.get("success", False)
        and result.get("status_code")
    ):
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"],
        )


    if result.get("success"):

        result["pipeline"] = (
            run_daily_pipeline_if_ready()
        )


    return result



@app.post("/assign")
def assign():

    return assign_videos()



@app.post("/schedule/today")
def schedule():

    return schedule_today()



@app.post("/pipeline")
def pipeline():

    return run_daily_pipeline()



@app.get("/health/posts")
def check_posts():

    return health_check()



app.mount(
    "/static",
    StaticFiles(
        directory=BASE_DIR / "static"
    ),
    name="static",
)


templates = Jinja2Templates(
    directory="backend/templates"
)



UPLOAD_FOLDER = Path(
    r"C:\Users\rexhe\Clipping-scheduler\incoming"
)


UPLOAD_FOLDER.mkdir(
    exist_ok=True
)



@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )



@app.get("/health")
def health():

    return {
        "database": "connected"
    }



@app.get("/settings")
def get_settings():

    return {
        "app": settings.APP_NAME,
        "buffer_connected": bool(
            settings.BUFFER_API_KEY
        ),
        "google_drive_connected": bool(
            settings.GOOGLE_DRIVE_FOLDER_ID
        ),
    }
@app.get("/videos")
def get_videos():

    db = SessionLocal()

    try:

        videos = (
            db.query(Video)
            .all()
        )

        result = []

        for video in videos:

            result.append(
                {
                    "id": video.id,
                    "filename": video.filename,
                    "status": video.status,
                }
            )

        return result

    finally:

        db.close()



@app.delete("/queue/{video_id}")
def delete_video(video_id: int):

    db = SessionLocal()

    try:

        schedule = (
            db.query(Schedule)
            .filter(
                Schedule.video_id == video_id
            )
            .first()
        )

        if schedule:
            db.delete(schedule)


        video = (
            db.query(Video)
            .filter(
                Video.id == video_id
            )
            .first()
        )


        if video:
            db.delete(video)


        db.commit()


        return {
            "success": True
        }


    finally:

        db.close()



@app.delete("/queue")
def clear_queue():

    db = SessionLocal()

    try:

        db.query(
            ChannelVideoQueue
        ).delete()


        db.query(
            Schedule
        ).delete()


        db.query(
            Video
        ).delete()


        db.commit()


        return {
            "success": True
        }


    finally:

        db.close()



@app.post("/upload")
async def upload(
    files: List[UploadFile] = File(...)
):

    print(
        "📥 Upload request received"
    )


    uploaded = []


    for file in files:

        destination = (
            UPLOAD_FOLDER / file.filename
        )


        with open(
            destination,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )


        print(
            f"✅ Saved: {file.filename}"
        )


        uploaded.append(
            file.filename
        )


    return {

        "success": True,

        "uploaded": len(uploaded),

        "files": uploaded,

    }



@app.get("/stats")
def stats():

    db = SessionLocal()


    try:

        return {

            "waiting":
                db.query(Video)
                .filter(
                    Video.status == "waiting"
                )
                .count(),


            "uploaded":
                db.query(Video)
                .filter(
                    Video.status == "uploaded"
                )
                .count(),


            "scheduled":
                db.query(Video)
                .filter(
                    Video.status == "scheduled"
                )
                .count(),


            "posted":
                db.query(Video)
                .filter(
                    Video.status == "posted"
                )
                .count(),

        }


    finally:

        db.close()



@app.get("/dashboard")
def dashboard():

    db = SessionLocal()


    try:

        return {

            "waiting":
                db.query(Video)
                .filter(
                    Video.status == "waiting"
                )
                .count(),


            "uploaded":
                db.query(Video)
                .filter(
                    Video.status == "uploaded"
                )
                .count(),


            "scheduled":
                db.query(Video)
                .filter(
                    Video.status == "scheduled"
                )
                .count(),


            "posted":
                db.query(Video)
                .filter(
                    Video.status == "posted"
                )
                .count(),

        }


    finally:

      db.close()
@app.get("/buffer/channels")
def buffer_channels():

    db = SessionLocal()

    try:

        channels = (
            db.query(BufferAccount)
            .all()
        )


        result = []


        for channel in channels:

            result.append(
                {
                    "name": channel.name,
                    "platform": channel.platform,
                    "enabled": channel.enabled,
                }
            )


        return result


    finally:

        db.close()



@app.get("/queue")
def queue():

    db = SessionLocal()

    try:

        videos = (
            db.query(Video)
            .order_by(
                Video.id.desc()
            )
            .all()
        )


        result = []


        for video in videos:

            result.append(
                {
                    "id": video.id,
                    "filename": video.filename,
                    "status": video.status,
                    "r2_url": video.r2_url,
                }
            )


        return result


    finally:

        db.close()



@app.get("/schedule")
def get_schedule():

    db = SessionLocal()


    try:

        schedules = (
            db.query(
                Schedule,
                Video
            )
            .join(
                Video,
                Video.id == Schedule.video_id
            )
            .order_by(
                Schedule.scheduled_time
            )
            .all()
        )


        result = []


        for schedule, video in schedules:

            result.append(
                {
                    "video_id": video.id,
                    "filename": video.filename,
                    "scheduled_time":
                        schedule.scheduled_time.strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    "status":
                        schedule.status,
                }
            )


        return result


    finally:

        db.close()