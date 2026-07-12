import os
import mimetypes
from pathlib import Path

import boto3
from dotenv import load_dotenv

load_dotenv()

print("R2_ACCESS_KEY =", repr(os.getenv("R2_ACCESS_KEY")))
print("R2_SECRET_KEY length =", len(os.getenv("R2_SECRET_KEY") or ""))
print("R2_BUCKET_NAME =", repr(os.getenv("R2_BUCKET_NAME")))
print("R2_ENDPOINT =", repr(os.getenv("R2_ENDPOINT")))

client = boto3.client(
    "s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
    region_name="auto",
)

BUCKET = os.getenv("R2_BUCKET_NAME")
PUBLIC_URL = os.getenv("R2_PUBLIC_URL")


def upload_video(file_path: str) -> str:
    """
    Upload a video to Cloudflare R2 and return its public URL.
    """

    file_path = Path(file_path)
    filename = file_path.name

    content_type = (
        mimetypes.guess_type(filename)[0]
        or "video/mp4"
    )

    print(f"☁️ Uploading {filename}...")
    print(f"📦 Content-Type: {content_type}")

    client.upload_file(
        str(file_path),
        BUCKET,
        filename,
        ExtraArgs={
            "ContentType": content_type,
        },
    )

    print("✅ Upload complete")

    return f"{PUBLIC_URL}/{filename}"