from backend.database.database import SessionLocal
from backend.models.buffer_workspace import BufferWorkspace
from backend.models.account import BufferAccount
from backend.models.video import Video
import requests

from backend.services.buffer_service import get_channels


def sync_channels():
    db = SessionLocal()

    try:
        workspace = (
            db.query(BufferWorkspace)
            .filter(BufferWorkspace.active == True)
            .first()
        )

        if not workspace:
            raise Exception("No active workspace.")

        try:
            result = get_channels()
        except requests.HTTPError as exc:
            response = exc.response
            status_code = response.status_code if response is not None else 502
            retry_after = response.headers.get("Retry-After") if response is not None else None
            return {
                "success": False,
                "status_code": status_code,
                "error": "Buffer rate limit reached. Please wait before syncing again."
                if status_code == 429
                else "Buffer channel sync failed.",
                "retry_after": retry_after,
            }

        print("BUFFER RESPONSE:")
        print(result)

        if "errors" in result:
            return {
                "success": False,
                "errors": result["errors"],
            }

        channels = result["data"]["channels"]
        channel_ids = {channel["id"] for channel in channels}

        added = 0
        disabled = 0

        # Buffer is the source of truth. Keep historical account rows, but
        # disable local channels that no longer exist in this workspace.
        local_accounts = (
            db.query(BufferAccount)
            .filter(BufferAccount.workspace_id == workspace.id)
            .all()
        )

        for account in local_accounts:
            if account.channel_id in channel_ids or not account.enabled:
                continue

            account.enabled = False
            disabled += 1

            # These clips were never accepted by Buffer, so release them for
            # reassignment to a valid channel. Scheduled clips stay intact.
            for video in (
                db.query(Video)
                .filter(Video.assigned_channel_id == account.id)
                .filter(Video.status == "assigned")
                .all()
            ):
                video.assigned_channel_id = None
                video.assigned_date = None
                video.status = "uploaded"

        for channel in channels:

            exists = (
                db.query(BufferAccount)
                .filter(BufferAccount.channel_id == channel["id"])
                .filter(BufferAccount.workspace_id == workspace.id)
                .first()
            )

            if exists:
                exists.name = channel["name"]
                exists.platform = channel["service"]
                exists.enabled = True
                continue

            db.add(
                BufferAccount(
                    workspace_id=workspace.id,
                    channel_id=channel["id"],
                    name=channel["name"],
                    platform=channel["service"],
                    enabled=True,
                )
            )

            added += 1

        db.commit()

        return {
            "success": True,
            "added": added,
            "disabled": disabled,
            "total": len(channels),
        }

    finally:
        db.close()
