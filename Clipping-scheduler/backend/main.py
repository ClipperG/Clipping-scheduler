print("🔥 LOADED THE CORRECT MAIN.PY")

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
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

from backend.core.settings import settings
from backend.database.database import Base, engine, SessionLocal

from backend.models.video import Video
from backend.models.account import BufferAccount
from backend.models.schedule import Schedule
from backend.models.buffer_workspace import BufferWorkspace
from backend.models.channel_video_queue import ChannelVideoQueue

from backend.api.buffer_accounts import router as buffer_accounts_router
from backend.api.schedule import router as schedule_router

from backend.services.caption_service import get_random_caption
from backend.services.hashtag_service import get_random_hashtags
from backend.services.folder_watcher import start_watcher
from backend.services.background_worker import start_background_worker
from backend.services.scheduler_worker import start_scheduler_worker
from backend.services.scheduler import generate_schedule
from backend.services.uploader import upload_all
from backend.services.buffer_service import upload_to_buffer



@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting application...")

    start_watcher()
    start_background_worker()
    start_scheduler_worker()

    yield

    print("🛑 Shutting down...")


app = FastAPI(
    title="Clipping Scheduler",
    lifespan=lifespan,
)

Base.metadata.create_all(bind=engine)
app.include_router(schedule_router)
app.include_router(buffer_accounts_router)
BASE_DIR = Path(__file__).parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(directory="backend/templates")

UPLOAD_FOLDER = Path(r"C:\Users\rexhe\Clipping-scheduler\incoming")
UPLOAD_FOLDER.mkdir(exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.get("/health")
def health():
    return {
        "database": "connected",
    }


@app.get("/settings")
def get_settings():
    return {
        "app": settings.APP_NAME,
        "buffer_connected": bool(settings.BUFFER_API_KEY),
        "google_drive_connected": bool(settings.GOOGLE_DRIVE_FOLDER_ID),
    }


@app.get("/videos")
def get_videos():
    db = SessionLocal()

    videos = db.query(Video).all()

    result = []

    for video in videos:
        result.append({
            "id": video.id,
            "filename": video.filename,
            "status": video.status,
        })

    db.close()

    return result

@app.delete("/queue/{video_id}")
def delete_video(video_id: int):
    db = SessionLocal()

    try:
        schedule = (
            db.query(Schedule)
            .filter(Schedule.video_id == video_id)
            .first()
        )

        if schedule:
            db.delete(schedule)

        video = (
            db.query(Video)
            .filter(Video.id == video_id)
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
        
@app.post("/queue/{video_id}/post")
def post_now(video_id: int):
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
                "message": "Video not found"
            }

        caption = get_random_caption()
        hashtags = get_random_hashtags()

        post_text = caption

        if hashtags:
            post_text += f"\n\n{hashtags}"

        result = upload_to_buffer(
            video_url=video.r2_url,
            caption=post_text,
        )

        video.status = "posted"

        schedule = (
            db.query(Schedule)
            .filter(Schedule.video_id == video.id)
            .first()
        )

        if schedule:
            schedule.status = "posted"

        db.commit()

        return {
            "success": True,
            "result": result,
        }

    finally:
        db.close()
@app.get("/schedule")
def get_schedule():
    db = SessionLocal()

    schedule = (
        db.query(Schedule, Video)
        .join(Video, Video.id == Schedule.video_id)
        .order_by(Schedule.scheduled_time)
        .all()
    )

    result = []

    for post, video in schedule:
        result.append(
            {
                "video_id": video.id,
                "filename": video.filename,
                "scheduled_time": post.scheduled_time.strftime("%Y-%m-%d %H:%M"),
                "status": post.status,
            }
        )

    db.close()

    return result

@app.get("/stats")
def stats():
    db = SessionLocal()

    waiting = db.query(Video).filter(Video.status == "waiting").count()
    uploaded = db.query(Video).filter(Video.status == "uploaded").count()
    scheduled = db.query(Video).filter(Video.status == "scheduled").count()
    posted = db.query(Video).filter(Video.status == "posted").count()

    db.close()

    return {
        "waiting": waiting,
        "uploaded": uploaded,
        "scheduled": scheduled,
        "posted": posted,
    }


@app.get("/dashboard")
def dashboard():
    db = SessionLocal()

    stats = {
        "waiting": db.query(Video).filter(Video.status == "waiting").count(),
        "uploaded": db.query(Video).filter(Video.status == "uploaded").count(),
        "scheduled": db.query(Video).filter(Video.status == "scheduled").count(),
        "posted": db.query(Video).filter(Video.status == "posted").count(),
    }

    db.close()

    return stats


@app.get("/queue")
def queue():
    db = SessionLocal()

    videos = (
        db.query(Video)
        .order_by(Video.id.desc())
        .all()
    )

    result = []

    for video in videos:
        result.append({
            "id": video.id,
            "filename": video.filename,
            "status": video.status,
            "r2_url": video.r2_url,
            "instagram_buffer_id": video.instagram_buffer_id,
            "youtube_buffer_id": video.youtube_buffer_id,
        })

    db.close()

    return result

@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)):
    print("📥 Upload request received")

    uploaded = []

    for file in files:
        destination = UPLOAD_FOLDER / file.filename

        with open(destination, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"✅ Saved: {file.filename}")

        uploaded.append(file.filename)

    return {
        "success": True,
        "uploaded": len(uploaded),
        "files": uploaded,
    }


@app.delete("/queue")
def clear_queue():
    db = SessionLocal()

    try:
        db.query(Schedule).delete()
        db.query(Video).delete()
        db.commit()

        return {"success": True}

    finally:
        db.close()


from zoneinfo import ZoneInfo

@app.put("/schedule/{video_id}")
def update_schedule(video_id: int, body: dict = Body(...)):
    db = SessionLocal()

    try:
        video = (
            db.query(Video)
            .filter(Video.id == video_id)
            .first()
        )

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        scheduled_time = datetime.strptime(
            body["scheduled_time"],
            "%Y-%m-%d %H:%M"
        )

        schedule = (
            db.query(Schedule)
            .filter(Schedule.video_id == video_id)
            .first()
        )

        if not schedule:
            schedule = Schedule(
                video_id=video_id,
                channel="ALL",
                scheduled_time=scheduled_time,
                status="scheduled",
            )
            db.add(schedule)
        else:
            schedule.scheduled_time = scheduled_time

        local_time = scheduled_time.replace(
            tzinfo=ZoneInfo("Europe/Tirane")
        )

        due_at = (
            local_time
            .astimezone(ZoneInfo("UTC"))
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        caption = get_random_caption()
        hashtags = get_random_hashtags()

        post_text = caption

        if hashtags:
            post_text += f"\n\n{hashtags}"

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

        schedule.status = "scheduled"
        video.status = "scheduled"

        db.commit()

        return {
            "success": True,
            "scheduled_for": scheduled_time.strftime("%Y-%m-%d %H:%M"),
        }

    finally:
        db.close()