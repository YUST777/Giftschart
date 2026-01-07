
import json
import os
import re

def normalize(name):
    # Normalize to lowercase, replace spaces/hyphens with underscores, remove special chars
    name = name.lower()
    name = name.replace(" ", "_").replace("-", "_")
    name = re.sub(r'[^a-z0-9_]', '', name)
    return name

def main():
    # Load MRKT Data
    with open('gifts_collections.json', 'r') as f:
        data = json.load(f)
    
    # Extract titles and normalize
    api_gifts = {}
    for item in data:
        title = item.get('title', 'Unknown')
        norm = normalize(title)
        api_gifts[norm] = title
        
    print(f"Loaded {len(api_gifts)} gifts from MRKT API.")

    # Load Local Files
    cards_dir = "/root/01studio/giftschart/new_gift_cards"
    local_gifts = set()
    if os.path.exists(cards_dir):
        for f in os.listdir(cards_dir):
            if f.endswith('.webp'):
                # Handle _card.webp and .webp
                name = f.replace('_card.webp', '').replace('.webp', '')
                norm = normalize(name)
                local_gifts.add(norm)
    
    print(f"Loaded {len(local_gifts)} local gift cards.")

    # Compare
    missing_in_local = []
    for norm, title in api_gifts.items():
        if norm not in local_gifts:
            missing_in_local.append(title)
            
    print(f"\nMissing in Local ({len(missing_in_local)}):")
    for title in missing_in_local:
        print(f" - {title}")
        
    # Optional: Missing in API (Extras in local)
    missing_in_api = []
    for norm in local_gifts:
        if norm not in api_gifts:
            # Try to find original name? We don't have it easily mapped back, just show norm
            missing_in_api.append(norm)

    # print(f"\nLocal files not in API ({len(missing_in_api)}):")
    # for name in missing_in_api:
    #     print(f" - {name}")

if __name__ == "__main__":
    main()
