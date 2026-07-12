import random

from backend.database.database import SessionLocal
from backend.models.account import BufferAccount
from backend.models.video import Video
from backend.models.channel_video_queue import ChannelVideoQueue


def build_queues():
    db = SessionLocal()

    try:
        accounts = (
            db.query(BufferAccount)
            .filter(BufferAccount.enabled == True)
            .all()
        )

        for account in accounts:

            existing_video_ids = [
                row.video_id
                for row in (
                    db.query(ChannelVideoQueue.video_id)
                    .filter(ChannelVideoQueue.channel_id == account.id)
                    .all()
                )
            ]

            videos = (
                db.query(Video)
                .filter(Video.status == "uploaded")
                .all()
            )

            print("\n===== DEBUG =====")
            print(f"Channel: {account.name}")

            print("Uploaded videos:")
            for v in videos:
                print(f"  {v.id} | {v.filename} | {v.status}")

            print("Already in queue:", existing_video_ids)

            new_videos = [
                video
                for video in videos
                if video.id not in existing_video_ids
            ]

            print("New videos:")
            for v in new_videos:
                print(f"  {v.id} | {v.filename}")

            print("=================\n")

            if not new_videos:
                print(f"{account.name}: nothing new")
                continue

            random.shuffle(new_videos)

            last = (
                db.query(ChannelVideoQueue)
                .filter(ChannelVideoQueue.channel_id == account.id)
                .order_by(ChannelVideoQueue.queue_position.desc())
                .first()
            )

            position = 0 if last is None else last.queue_position + 1

            for video in new_videos:
                db.add(
                    ChannelVideoQueue(
                        channel_id=account.id,
                        video_id=video.id,
                        queue_position=position,
                        posted=False,
                    )
                )

                position += 1

            print(f"{account.name}: added {len(new_videos)} videos")

        db.commit()

    finally:
        db.close()