"""Small, idempotent SQLite migrations for installations created before video assignment."""

from sqlalchemy import text


VIDEO_COLUMNS = {
    "assigned_channel_id": "INTEGER",
    "assigned_date": "DATETIME",
    "scheduled_for": "DATETIME",
    "posted_at": "DATETIME",
    "created_at": "DATETIME",
    "r2_url_instagram": "TEXT",
}


def migrate_video_assignments(engine):
    """Add assignment columns without deleting or recreating existing video data."""
    with engine.begin() as connection:
        rows = connection.execute(text("PRAGMA table_info(videos)")).mappings()
        existing = {row["name"] for row in rows}

        for name, column_type in VIDEO_COLUMNS.items():
            if name not in existing:
                connection.execute(
                    text(f"ALTER TABLE videos ADD COLUMN {name} {column_type}")
                )
