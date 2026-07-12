import json
import requests

from backend.database.database import SessionLocal
from backend.models.account import BufferAccount
from backend.models.buffer_workspace import BufferWorkspace

BUFFER_API = "https://api.buffer.com"


def get_buffer_token():
    db = SessionLocal()

    try:
        workspace = (
            db.query(BufferWorkspace)
            .filter(BufferWorkspace.active == True)
            .first()
        )

        if workspace is None:
            raise Exception("No active Buffer account found.")

        return workspace.api_token

    finally:
        db.close()


def get_active_workspace():
    db = SessionLocal()

    try:
        workspace = (
            db.query(BufferWorkspace)
            .filter(BufferWorkspace.active == True)
            .first()
        )

        if workspace is None:
            raise Exception("No active Buffer workspace selected.")

        return workspace

    finally:
        db.close()


def create_post(
    channel_id,
    video_url,
    caption,
    due_at=None,
    metadata=None,
):
    query = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        __typename

        ... on PostActionSuccess {
          post {
            id
          }
        }

        ... on InvalidInputError {
          message
        }

        ... on UnauthorizedError {
          message
        }

        ... on UnexpectedError {
          message
        }

        ... on RestProxyError {
          message
        }

        ... on LimitReachedError {
          message
        }
      }
    }
    """

    variables = {
        "input": {
            "channelId": channel_id,
            "schedulingType": "automatic",
            "mode": "customScheduled",
            "text": caption,
            "assets": [
                {
                    "video": {
                        "url": video_url
                    }
                }
            ],
        }
    }

    if due_at:
        variables["input"]["dueAt"] = due_at

    if metadata:
        variables["input"]["metadata"] = metadata

    print("========== VARIABLES ==========")
    print(json.dumps(variables, indent=2))
    print("===============================")

    response = requests.post(
        BUFFER_API,
        headers={
            "Authorization": f"Bearer {get_buffer_token()}",
            "Content-Type": "application/json",
        },
        json={
            "query": query,
            "variables": variables,
        },
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()

    print("========== BUFFER RESPONSE ==========")
    print(json.dumps(result, indent=2))
    print("=====================================")

    return result


def upload_to_buffer(
    video_url: str,
    caption: str = "",
    due_at: str = None,
):
    # Read DB only, then close it before HTTP requests
    db = SessionLocal()

    try:
        workspace = (
            db.query(BufferWorkspace)
            .filter(BufferWorkspace.active == True)
            .first()
        )

        if workspace is None:
            raise Exception("No active Buffer workspace selected.")

        accounts = (
            db.query(BufferAccount)
            .filter(BufferAccount.workspace_id == workspace.id)
            .filter(BufferAccount.enabled == True)
            .all()
        )

        account_data = [
            {
                "name": a.name,
                "platform": a.platform,
                "channel_id": a.channel_id,
            }
            for a in accounts
        ]

    finally:
        db.close()

    results = {}

    for account in account_data:
        print(f"Posting to {account['name']}...")

        metadata = {}

        if account["platform"] == "instagram":
            metadata = {
                "instagram": {
                    "type": "reel",
                    "shouldShareToFeed": True,
                }
            }

        elif account["platform"] == "youtube":
            metadata = {
                "youtube": {
                    "title": caption,
                    "categoryId": "22",
                    "privacy": "public",
                    "notifySubscribers": True,
                    "embeddable": True,
                    "madeForKids": False,
                }
            }

        result = create_post(
            channel_id=account["channel_id"],
            video_url=video_url,
            caption=caption,
            due_at=due_at,
            metadata=metadata,
        )

        results[account["platform"]] = result

    print("✅ Finished posting to all enabled accounts.")

    return results


def update_buffer_post(
    post_id: str,
    due_at: str,
    caption: str,
):
    query = """
    mutation EditPost($input: EditPostInput!) {
      editPost(input: $input) {
        __typename

        ... on PostActionSuccess {
          post {
            id
          }
        }

        ... on InvalidInputError {
          message
        }

        ... on UnauthorizedError {
          message
        }

        ... on UnexpectedError {
          message
        }

        ... on RestProxyError {
          message
        }

        ... on LimitReachedError {
          message
        }

        ... on NotFoundError {
          message
        }
      }
    }
    """

    variables = {
        "input": {
            "id": post_id,
            "schedulingType": "automatic",
            "mode": "customScheduled",
            "dueAt": due_at,
            "text": caption,
        }
    }

    print("========== EDIT VARIABLES ==========")
    print(json.dumps(variables, indent=2))
    print("====================================")

    response = requests.post(
        BUFFER_API,
        headers={
            "Authorization": f"Bearer {get_buffer_token()}",
            "Content-Type": "application/json",
        },
        json={
            "query": query,
            "variables": variables,
        },
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()

    print("========== EDIT RESPONSE ==========")
    print(json.dumps(result, indent=2))
    print("===================================")

    return result


def upload_to_single_channel(
    account,
    video_url: str,
    caption: str = "",
    due_at: str = None,
):
    metadata = {}

    if account.platform == "instagram":
        metadata = {
            "instagram": {
                "type": "reel",
                "shouldShareToFeed": True,
            }
        }

    elif account.platform == "youtube":
        metadata = {
            "youtube": {
                "title": caption,
                "categoryId": "22",
                "privacy": "public",
                "notifySubscribers": True,
                "embeddable": True,
                "madeForKids": False,
            }
        }

    return create_post(
        channel_id=account.channel_id,
        video_url=video_url,
        caption=caption,
        due_at=due_at,
        metadata=metadata,
    )