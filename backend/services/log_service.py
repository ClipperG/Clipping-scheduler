import csv
from pathlib import Path
from datetime import datetime

LOG_FILE = Path("uploads.csv")


def log_upload(
    filename,
    caption,
    hashtags,
    instagram_id,
    youtube_id,
    status,
):
    file_exists = LOG_FILE.exists()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "filename",
                "caption",
                "hashtags",
                "instagram_id",
                "youtube_id",
                "status",
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            filename,
            caption,
            hashtags,
            instagram_id,
            youtube_id,
            status,
        ])