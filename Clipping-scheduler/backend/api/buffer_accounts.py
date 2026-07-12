import random
import requests

from fastapi import APIRouter, HTTPException

from backend.database.database import SessionLocal
from backend.models import account
from backend.models.buffer_workspace import BufferWorkspace
from backend.models.account import BufferAccount
from backend.models.video import Video
from backend.models.channel_video_queue import ChannelVideoQueue

router = APIRouter(
    prefix="/buffer-accounts",
    tags=["Buffer Accounts"],
)


@router.get("/")
def list_accounts():
    db = SessionLocal()
    try:
        return db.query(BufferWorkspace).all()
    finally:
        db.close()


@router.post("/")
def add_account(body: dict):
    db = SessionLocal()

    try:
        account = BufferWorkspace(
            name=body["name"],
            api_token=body["api_token"],
            active=False,
        )

        db.add(account)
        db.commit()
        db.refresh(account)

        headers = {
            "Authorization": f"Bearer {account.api_token}",
            "Content-Type": "application/json",
        }

        # Get organization ID
        org_query = """
        query {
          account {
            organizations {
              id
            }
          }
        }
        """

        response = requests.post(
            "https://api.buffer.com/graphql",
            headers=headers,
            json={"query": org_query},
            timeout=30,
        )

        response.raise_for_status()

        org_result = response.json()

        if "errors" in org_result:
            raise HTTPException(status_code=400, detail=org_result["errors"])

        organization_id = org_result["data"]["account"]["organizations"][0]["id"]

        # Get Buffer channels
        channels_query = f"""
        query {{
          channels(
            input: {{
              organizationId: "{organization_id}"
            }}
          ) {{
            id
            name
            service
          }}
        }}
        """

        response = requests.post(
            "https://api.buffer.com/graphql",
            headers=headers,
            json={"query": channels_query},
            timeout=30,
        )

        response.raise_for_status()

        result = response.json()

        if "errors" in result:
            raise HTTPException(status_code=400, detail=result["errors"])

        profiles = result["data"]["channels"]

        # Remove old channels for this workspace
        db.query(BufferAccount).filter(
            BufferAccount.workspace_id == account.id
        ).delete()

        db.commit()

        # Load videos
        videos = db.query(Video).all()
        print(f"Found {len(videos)} videos")

        # Create Buffer accounts + queues
        for profile in profiles:
            print(f"Creating queue for {profile['name']}")

            buffer_account = BufferAccount(
                workspace_id=account.id,
                name=profile["name"],
                platform=profile["service"],
                channel_id=profile["id"],
                enabled=True,
            )

            db.add(buffer_account)
            db.flush()  # Get buffer_account.id

            shuffled = videos.copy()
            random.shuffle(shuffled)

            for position, video in enumerate(shuffled):
                print(
                    f"Adding video {video.id} -> {buffer_account.name}"
                )

                db.add(
                    ChannelVideoQueue(
                        channel_id=buffer_account.id,
                        video_id=video.id,
                        queue_position=position,
                        posted=False,
                    )
                )

        print("Committing queue...")
        db.commit()
        print("Queue committed.")

        return account

    finally:
        db.close()


@router.delete("/{account_id}")
def delete_account(account_id: int):
    db = SessionLocal()

    try:
        account = (
            db.query(BufferWorkspace)
            .filter(BufferWorkspace.id == account_id)
            .first()
        )

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        db.query(BufferAccount).filter(
            BufferAccount.workspace_id == account.id
        ).delete()

        db.delete(account)
        db.commit()

        return {"success": True}

    finally:
        db.close()


@router.put("/{account_id}/activate")
def activate_account(account_id: int):
    db = SessionLocal()

    try:
        db.query(BufferWorkspace).update({"active": False})

        account = (
            db.query(BufferWorkspace)
            .filter(BufferWorkspace.id == account_id)
            .first()
        )

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        account.active = True
        db.commit()

        return {"success": True}

    finally:
        db.close()