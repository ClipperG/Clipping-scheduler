from backend.database.database import SessionLocal
from backend.models.buffer_workspace import BufferWorkspace
from backend.models.account import BufferAccount

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

        result = get_channels()

        print("BUFFER RESPONSE:")
        print(result)

        if "errors" in result:
            return {
                "success": False,
                "errors": result["errors"],
            }

        channels = result["data"]["channels"]

        added = 0

        for channel in channels:

            exists = (
                db.query(BufferAccount)
                .filter(BufferAccount.channel_id == channel["id"])
                .first()
            )

            if exists:
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
            "total": len(channels),
        }

    finally:
        db.close()