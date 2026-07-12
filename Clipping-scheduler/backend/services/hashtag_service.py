import json
import random
from pathlib import Path

HASHTAGS_FILE = Path("hashtags.txt")
USED_FILE = Path("used_hashtags.json")


def get_random_hashtags():
    if not HASHTAGS_FILE.exists():
        return ""

    hashtags = [
        line.strip()
        for line in HASHTAGS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if not hashtags:
        return ""

    if not USED_FILE.exists():
        USED_FILE.write_text("[]", encoding="utf-8")

    try:
        used = json.loads(USED_FILE.read_text(encoding="utf-8"))
    except Exception:
        used = []

    available = [tag for tag in hashtags if tag not in used]

    # Reset when all hashtag groups have been used
    if not available:
        used = []
        available = hashtags

    selected = random.choice(available)

    used.append(selected)

    USED_FILE.write_text(
        json.dumps(used, indent=4),
        encoding="utf-8"
    )

    return selected