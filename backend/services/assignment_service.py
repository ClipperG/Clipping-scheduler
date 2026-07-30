from datetime import datetime

from backend.database.database import SessionLocal
from backend.models.video import Video
from backend.models.account import BufferAccount
from backend.models.buffer_workspace import BufferWorkspace


def assign_single_video(video_id):
    """
    Assign one uploaded video to the channel with the smallest queue.
    """

    db = SessionLocal()

    try:
        video = (
            db.query(Video)
            .filter(Video.id == video_id)
            .first()
        )

        if video is None:
            print(f"❌ Video {video_id} not found")
            return False

        channels = (
            db.query(BufferAccount)
            .join(
                BufferWorkspace,
                BufferWorkspace.id == BufferAccount.workspace_id
            )
            .filter(BufferWorkspace.active == True)
            .filter(BufferAccount.enabled == True)
            .order_by(BufferAccount.id)
            .all()
        )

        if not channels:
            print("❌ No active channels available")
            return False

        # Count current queue size for each channel
        queue_sizes = {}

        for channel in channels:
            queue_sizes[channel.id] = (
                db.query(Video)
                .filter(Video.assigned_channel_id == channel.id)
                .filter(
                    Video.status.in_(
                        [
                            "assigned",
                            "scheduled"
                        ]
                    )
                )
                .count()
            )

        # Pick channel with smallest queue
        channel = min(
            channels,
            key=lambda c: (
                queue_sizes[c.id],
                c.id
            )
        )

        video.assigned_channel_id = channel.id
        video.assigned_date = datetime.utcnow()
        video.status = "assigned"

        db.commit()

        print(
            f"✅ Assigned {video.filename} "
            f"-> {channel.name} "
            f"(queue: {queue_sizes[channel.id] + 1})"
        )

        return True

    except Exception as e:
        db.rollback()
        print(f"❌ Assignment error: {e}")
        return False

    finally:
        db.close()


def assign_videos(video_ids):
    """
    Assign multiple videos.
    Used by upload pipeline.
    """

    results = []

    for video_id in video_ids:
        result = assign_single_video(video_id)
        results.append(result)

    return results