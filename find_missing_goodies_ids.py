import json

DUMP_PATH = "/root/01studio/giftschart/sticker_stats_dump.json"

TARGET_STICKERS = [
    "Box Box Boxie",
    "BONK: The Dog",
    "BONK: Hit Harder",
    "Meebits: Cube Culture",
    "Meebits: Blocky Drop",
    "Neiro: Woofin' Mad",
    "Neiro: Woof Vault",
    "Ted Blessed",
    "Tedism"
]

def main():
    try:
        with open(DUMP_PATH, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading dump: {e}")
        return

    found = {}

    for col_id, col_data in data.get("collections", {}).items():
        col_name = col_data.get("name")
        for sticker in col_data.get("stickers", []):
            s_name = sticker.get("name")
            if s_name in TARGET_STICKERS:
                char_id = sticker.get("char_id")
                # Normalize names for logic
                import re
                col_norm = col_name.strip().lower()
                col_norm = re.sub(r'[^a-z0-9]', '_', col_norm)
                col_norm = re.sub(r'_+', '_', col_norm).strip('_')
                
                sticker_norm = s_name.strip().lower()
                sticker_norm = re.sub(r'[^a-z0-9]', '_', sticker_norm)
                sticker_norm = re.sub(r'_+', '_', sticker_norm).strip('_')
                
                print(f"FOUND: ('{col_id}', '{char_id}', '{col_norm}', '{sticker_norm}'), # {col_name} - {s_name}")

if __name__ == "__main__":
    main()
