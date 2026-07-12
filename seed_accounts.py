from backend.database.database import SessionLocal
from backend.models.account import BufferAccount
from backend.models.buffer_workspace import BufferWorkspace

db = SessionLocal()

workspace = (
    db.query(BufferWorkspace)
    .filter(BufferWorkspace.active == True)
    .first()
)

if not workspace:
    raise Exception("No active Buffer workspace found.")

accounts = [
    BufferAccount(
        workspace_id=workspace.id,
        name="Instagram Main",
        platform="instagram",
        channel_id="6a21e747c687a22dd45f99dd",
        enabled=True,
    ),
    BufferAccount(
        workspace_id=workspace.id,
        name="YouTube Main",
        platform="youtube",
        channel_id="6a21e5fbc687a22dd45f962a",
        enabled=True,
    ),
]

db.add_all(accounts)
db.commit()
db.close()

print("Accounts added!")