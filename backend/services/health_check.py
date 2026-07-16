from backend.database.database import SessionLocal
from backend.models.video import Video
from backend.models.account import BufferAccount
from backend.models.buffer_workspace import BufferWorkspace


POSTS_PER_DAY = 3


def health_check():
    db = SessionLocal()

    try:
        channels = (
            db.query(BufferAccount)
            .join(BufferWorkspace, BufferWorkspace.id == BufferAccount.workspace_id)
            .filter(BufferWorkspace.active == True)
            .filter(BufferAccount.enabled == True)
            .all()
        )

        bad = []

        for channel in channels:

            count = (
                db.query(Video)
                .filter(Video.assigned_channel_id == channel.id)
                .filter(Video.status == "scheduled")
                .count()
            )

            if count != POSTS_PER_DAY:
                bad.append(
                    {
                        "channel": channel.name,
                        "scheduled": count,
                    }
                )

        return {
            "success": len(bad) == 0,
            "total_channels": len(channels),
            "failed_channels": len(bad),
            "issues": bad,
        }

    finally:
        db.close()
