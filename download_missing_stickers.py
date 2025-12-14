import stickers_tools_api as api
import os
import requests

# Get live stats
stats = api.get_sticker_stats(force_refresh=True)
base = 'sticker_collections'
missing = []

# Find missing stickers (first of each pack)
for c in stats['collections'].values():
    collection = c['name'].replace(' ', '_').replace('&', 'AND')
    for s in c['stickers']:
        sticker = s['name'].replace(' ', '_')
        found = False
        for root, dirs, files in os.walk(base):
            if collection in root and sticker in root:
                found = True
                break
        if not found:
            missing.append((c['id'], c['name'], s['id'], s['name']))

# Aggressively try to download up to 5 images for each missing sticker
os.makedirs('downloaded_missing_stickers', exist_ok=True)
for col_id, col_name, pack_id, pack_name in missing:
    outdir = f'downloaded_missing_stickers/{col_name.replace(" ", "_")}_{pack_name.replace(" ", "_")}'; os.makedirs(outdir, exist_ok=True)
    found_img = False
    for img_num in range(1, 6):
        url = f'https://cdn.stickerdom.store/{col_id}/p/{pack_id}/{img_num}.png?v=3'
        outpath = f'{outdir}/{img_num}.png'
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open(outpath, 'wb') as f:
                    f.write(r.content)
                print(f'Downloaded: {url} -> {outpath}')
                found_img = True
                break  # Stop after first successful image
            else:
                print(f'Failed: {url} ({r.status_code})')
        except Exception as e:
            print(f"Error: {url} {e}")
    if not found_img:
        print(f'No image found for {col_name} / {pack_name}') 