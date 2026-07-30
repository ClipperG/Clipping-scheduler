from backend.database.database import SessionLocal
from backend.models.video import Video
from backend.services.assignment_service import assign_single_video
from backend.services.scheduler_service import schedule_single_video



def process_single_video(video_id):
    """
    Upload -> Assign -> Schedule a single video.
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

            return {
                "success": False,
                "error": "video_not_found"
            }


        # Allow retrying assigned videos
        if video.status not in [
            "uploaded",
            "assigned"
        ]:
            print(
                f"⚠️ {video.filename} has status {video.status}"
            )

            return {
                "success": False,
                "error": "invalid_status"
            }


        filename = video.filename


    except Exception as e:

        print(
            f"❌ Pipeline database error: {e}"
        )

        return {
            "success": False,
            "error": str(e)
        }


    finally:
        db.close()



    print("===================================")
    print(f"PROCESSING {filename}")
    print("===================================")



    # Only assign if not already assigned
    if not assign_single_video(video_id):

        # If already assigned, continue
        db = SessionLocal()

        try:
            video = (
                db.query(Video)
                .filter(Video.id == video_id)
                .first()
            )

            if video.status != "assigned":
                print(
                    f"❌ Assignment failed: {filename}"
                )

                return {
                    "success": False,
                    "error": "assignment_failed"
                }

        finally:
            db.close()



    print(
        f"✅ Assigned {filename}"
    )



    if not schedule_single_video(video_id):

        print(
            f"❌ Scheduling failed: {filename}"
        )

        return {
            "success": False,
            "error": "schedule_failed"
        }



    print(
        f"🚀 Finished pipeline: {filename}"
    )


    return {
        "success": True,
        "video": filename
    }





def run_daily_pipeline():
    """
    Process uploaded and assigned videos.
    """

    db = SessionLocal()

    try:

        videos = (
            db.query(Video)
            .filter(
                Video.status.in_(
                    [
                        "uploaded",
                        "assigned"
                    ]
                )
            )
            .order_by(
                Video.id
            )
            .all()
        )


        if not videos:

            print(
                "ℹ️ No videos waiting"
            )

            return []


        results = []


        for video in videos:

            result = process_single_video(
                video.id
            )

            results.append(result)


        successful = sum(
            1 for r in results if r["success"]
        )


        print(
            f"✅ Daily pipeline completed: {successful}/{len(results)} videos"
        )


        return results



    except Exception as e:

        print(
            f"❌ Daily pipeline error: {e}"
        )

        return []


    finally:

        db.close()





def run_daily_pipeline_if_ready():
    """
    Run pipeline if uploaded or assigned videos exist.
    """

    db = SessionLocal()

    try:

        count = (
            db.query(Video)
            .filter(
                Video.status.in_(
                    [
                        "uploaded",
                        "assigned"
                    ]
                )
            )
            .count()
        )


        if count == 0:

            print(
                "ℹ️ Pipeline not started - no videos ready"
            )

            return []


        print(
            f"🚀 Starting pipeline for {count} videos"
        )


        return run_daily_pipeline()



    finally:

        db.close()