import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DUMP_PATH = "/root/01studio/giftschart/sticker_stats_dump.json"
BASE_URL = "https://storage.googleapis.com/goodies-api-prod.firebasestorage.app/images/collection/"

def main():
    with open(DUMP_PATH, 'r') as f:
        data = json.load(f)

    for coll_id, coll_data in data.get("collections", {}).items():
        for sticker in coll_data.get("stickers", []):
            if sticker.get("name") == "Lamborghini Revuelto":
                char_id = sticker.get("char_id")
                url = f"{BASE_URL}{char_id}"
                print(f"URL: {url}")
                return

if __name__ == "__main__":
    main()
