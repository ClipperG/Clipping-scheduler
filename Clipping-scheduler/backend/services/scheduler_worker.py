import threading
import time

from backend.services.channel_scheduler import run_channel_scheduler


def scheduler_worker():
    print("📅 Scheduler worker started")

    while True:
        try:
            run_channel_scheduler()
        except Exception as e:
            print(f"Scheduler error: {e}")

        time.sleep(60)  # Check every minute


def start_scheduler_worker():
    thread = threading.Thread(
        target=scheduler_worker,
        daemon=True,
    )

    thread.start()

    print("✅ Scheduler background worker started")