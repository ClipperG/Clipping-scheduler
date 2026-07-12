Clipping Scheduler
Automate your short-form content workflow by watching a folder for new videos, uploading them to Cloudflare R2, and scheduling them to multiple Buffer channels.

Features
📂 Watches a folder for new .mp4 files

☁️ Uploads videos to Cloudflare R2

🎲 Randomizes video order per channel

📅 Automatically schedules posts to Buffer

📱 Supports multiple Buffer channels (Instagram, YouTube, etc.)

🔁 Background workers handle uploads and scheduling

🌐 Web dashboard built with FastAPI

Requirements
Python 3.11+

Buffer account

Cloudflare R2 bucket

Git

Installation
1. Clone the repository
git clone https://github.com/YOUR_USERNAME/clipping-scheduler.git
cd clipping-scheduler
2. Create a virtual environment
Windows
python -m venv .venv
.venv\Scripts\activate
macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
4. Create your environment file
Copy:

.env.example
to

.env
Then fill in your credentials.

Example:

APP_NAME=Clipping Scheduler

BUFFER_API_KEY=

R2_ENDPOINT=
R2_BUCKET=
R2_ACCESS_KEY=
R2_SECRET_KEY=
R2_PUBLIC_URL=

GOOGLE_DRIVE_FOLDER_ID=
5. Start the application
uvicorn backend.main:app --reload
You should see something similar to:

🚀 Starting application...
👀 Watching incoming/
✅ Upload queue worker started
📅 Scheduler worker started
Folder Structure
incoming/
uploaded/
failed/
data/

backend/
static/
templates/
The application automatically creates the required folders if they do not already exist.

How It Works
Copy .mp4 files into the incoming folder.

The watcher detects new videos.

Videos are uploaded to Cloudflare R2.

The uploaded video is added to every enabled Buffer channel queue.

Each channel receives its own randomized queue.

The scheduler schedules one video at a time for each channel.

Posts are automatically published by Buffer.

Running the Dashboard
After starting the server, open:

http://127.0.0.1:8000
Database
SQLite is used by default.

The database is stored in:

data/clipping_scheduler.db
Project Structure
backend/
│
├── api/
├── core/
├── database/
├── models/
├── services/
├── static/
├── templates/
└── main.py

incoming/
uploaded/
failed/
data/
Configuration
Make sure your active Buffer workspace and channels are configured before uploading videos.

Required services:

Cloudflare R2

Buffer API

Development
Run with auto-reload:

uvicorn backend.main:app --reload
Recommended .gitignore
# Virtual environment
.venv/

# Python
__pycache__/
*.pyc

# Environment variables
.env

# SQLite database
data/*.db

# Uploaded files
incoming/
uploaded/
failed/

# IDE files
.vscode/
.idea/
Notes
Before publishing your project, replace any hard-coded paths such as:

Path(r"C:\Users\YourName\Clipping-scheduler\incoming")
with project-relative paths:

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

WATCH_FOLDER = BASE_DIR / "incoming"
UPLOADED_FOLDER = BASE_DIR / "uploaded"
FAILED_FOLDER = BASE_DIR / "failed"
This makes the application portable across different machines and operating systems.

License
This project is provided as-is. Feel free to modify and extend it for your own workflow.
