import random
from datetime import datetime

from backend.database.database import SessionLocal
from backend.models.video import Video
from backend.models.account import BufferAccount
from backend.models.buffer_workspace import BufferWorkspace


POSTS_PER_DAY = 3


def assign_videos():
    db = SessionLocal()

    try:
        # Get all enabled channels
        channels = (
            db.query(BufferAccount)
            .join(BufferWorkspace, BufferWorkspace.id == BufferAccount.workspace_id)
            .filter(BufferWorkspace.active == True)
            .filter(BufferAccount.enabled == True)
            .order_by(BufferAccount.id)
            .all()
        )

        if not channels:
            return {"success": True, "channels": 0, "assigned": 0}

        # Get all uploaded videos that haven't been assigned
        unassigned = (
            db.query(Video)
            .filter(Video.assigned_channel_id == None)
            .filter(Video.status == "uploaded")
            .order_by(Video.id)
            .all()
        )

        # Shuffle once, then consume each clip exactly once.  A Video has one
        # assigned_channel_id, so it cannot be assigned to another channel.
        random.shuffle(unassigned)

        assigned_counts = {
            channel.id: (
                db.query(Video)
                .filter(Video.assigned_channel_id == channel.id)
                .filter(Video.status.in_(["assigned", "scheduled"]))
                .count()
            )
            for channel in channels
        }

        assigned = 0

        for video in unassigned:
            eligible = [
                channel
                for channel in channels
                if assigned_counts[channel.id] < POSTS_PER_DAY
            ]

            if not eligible:
                break

            # Always fill the least-populated channel first, so partial uploads
            # are spread evenly and later uploads fill the remaining gaps.
            channel = min(eligible, key=lambda item: (assigned_counts[item.id], item.id))

            video.assigned_channel_id = channel.id
            video.assigned_date = datetime.utcnow()
            video.status = "assigned"
            assigned_counts[channel.id] += 1
            assigned += 1

        db.commit()

        return {
            "success": True,
            "channels": len(channels),
            "assigned": assigned,
        }

    finally:
        db.close()
