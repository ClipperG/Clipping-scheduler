from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.core.settings import settings



def get_next_schedule_time():
    now = datetime.now(ZoneInfo(settings.TIMEZONE))

    post_times = sorted(settings.post_times)

    for time_str in post_times:
        hour, minute = map(int, time_str.split(":"))

        candidate = now.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )

        if candidate > now:
            return candidate

    # No times left today → first time tomorrow
    hour, minute = map(int, post_times[0].split(":"))

    tomorrow = now + timedelta(days=1)

    return tomorrow.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )

    # No slots left today, use the first slot tomorrow
    hour, minute = map(int, post_times[0].split(":"))

    tomorrow = now + timedelta(days=1)

    return tomorrow.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )