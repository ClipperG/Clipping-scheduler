import json
import random
from pathlib import Path

CAPTIONS_FILE = Path("captions.txt")
USED_FILE = Path("used_captions.json")


def get_random_caption():
    if not CAPTIONS_FILE.exists():
        return "New video!"

    captions = [
        line.strip()
        for line in CAPTIONS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if not captions:
        return "New video!"

    if not USED_FILE.exists():
        USED_FILE.write_text("[]", encoding="utf-8")

    try:
        used = json.loads(USED_FILE.read_text(encoding="utf-8"))
    except Exception:
        used = []

    available = [caption for caption in captions if caption not in used]

    # Reset after every caption has been used once
    if not available:
        used = []
        available = captions

    caption = random.choice(available)

    used.append(caption)

    USED_FILE.write_text(
        json.dumps(used, indent=4),
        encoding="utf-8"
    )

    return caption