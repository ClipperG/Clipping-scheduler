from datetime import datetime, timezone, timedelta

from backend.database.database import SessionLocal
from backend.models.video import Video
from backend.models.account import BufferAccount
from backend.services.buffer_service import upload_to_single_channel


# Fixed posting times (UTC)
POSTING_SLOTS = [
    (0, 0),
    (8, 0),
    (16, 0),
]


def get_next_post_time(last_scheduled=None):
    """
    Find the next available fixed posting slot.
    """

    now = datetime.now(timezone.utc)

    slots = []

    for days_ahead in range(0, 14):

        day = now + timedelta(days=days_ahead)

        for hour, minute in POSTING_SLOTS:

            slot = day.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
            )

            if slot > now:
                slots.append(slot)


    slots.sort()


    if last_scheduled:

        for slot in slots:

            if slot > last_scheduled:
                return slot


    return slots[0]



def schedule_single_video(video_id):
    """
    Schedule one assigned video to Buffer.
    """

    db = SessionLocal()

    try:

        video = (
            db.query(Video)
            .filter(Video.id == video_id)
            .first()
        )


        if video is None:

            print(
                f"❌ Video {video_id} not found"
            )

            return False



        channel = (
            db.query(BufferAccount)
            .filter(
                BufferAccount.id == video.assigned_channel_id
            )
            .first()
        )


        if channel is None:

            print(
                f"❌ Channel missing for {video.filename}"
            )

            return False



        last_scheduled = (
            db.query(Video.scheduled_for)
            .filter(
                Video.assigned_channel_id == channel.id
            )
            .filter(
                Video.status == "scheduled"
            )
            .order_by(
                Video.scheduled_for.desc()
            )
            .first()
        )


        last_time = None


        if last_scheduled and last_scheduled[0]:

            last_time = last_scheduled[0].replace(
                tzinfo=timezone.utc
            )



        due = get_next_post_time(
            last_time
        )


        # No hashtags/caption generator anymore
        text = ""


        result = upload_to_single_channel(
            account=channel,
            video_url=video.r2_url,
            caption=text,
            due_at=due.isoformat().replace(
                "+00:00",
                "Z"
            ),
        )


        response = (
            result["data"]["createPost"]
        )


        if response["__typename"] != "PostActionSuccess":

            print(
                f"❌ Buffer failed: {video.filename}"
            )

            print(response)

            return False



        video.status = "scheduled"

        video.scheduled_for = due.replace(
            tzinfo=None
        )


        db.commit()


        print(
            f"✅ {channel.name} -> "
            f"{video.filename} scheduled "
            f"for {due}"
        )


        return True



    except Exception as e:

        db.rollback()

        print(
            f"❌ Scheduling error: {e}"
        )

        return False



    finally:

        db.close()




def schedule_today():
    """
    Schedule all assigned videos waiting for Buffer upload.
    """

    db = SessionLocal()

    try:

        videos = (
            db.query(Video)
            .filter(
                Video.status == "assigned"
            )
            .filter(
                Video.assigned_channel_id.isnot(None)
            )
            .order_by(
                Video.id
            )
            .all()
        )


        if not videos:

            print(
                "ℹ️ No videos waiting for scheduling"
            )

            return []



        results = []



        for video in videos:

            success = schedule_single_video(
                video.id
            )


            results.append(
                {
                    "video_id": video.id,
                    "success": success,
                }
            )



        successful = sum(
            1
            for r in results
            if r["success"]
        )


        print(
            f"✅ Scheduled {successful}/{len(results)} videos"
        )


        return results



    except Exception as e:

        print(
            f"❌ Daily scheduler error: {e}"
        )

        return []



    finally:

        db.close()