import os
import requests

base_url = 'https://cdn.stickerdom.store/{col_id}/p/{pack_id}/{img_num}.png?v=3'
out_base = 'aggressive_cdn_scrape'
existing_base = 'sticker_collections'

success = 0
fail = 0
for col_id in range(1, 51):
    for img_num in range(1, 6):
        consecutive_not_found = 0
        for pack_id in range(1, 121):
            # Check if image already exists in sticker_collections
            existing_path = os.path.join(existing_base, str(col_id), str(pack_id), f'{img_num}.png')
            if os.path.exists(existing_path):
                print(f'Already exists: {existing_path} (skipping)')
                consecutive_not_found = 0
                continue
            url = base_url.format(col_id=col_id, pack_id=pack_id, img_num=img_num)
            outdir = os.path.join(out_base, str(col_id), 'p', str(pack_id))
            os.makedirs(outdir, exist_ok=True)
            outpath = os.path.join(outdir, f'{img_num}.png')
            try:
                r = requests.get(url, timeout=8)
                if r.status_code == 200 and r.content and r.content[:4] == b'\x89PNG':
                    with open(outpath, 'wb') as f:
                        f.write(r.content)
                    print(f'Downloaded: {url} -> {outpath}')
                    success += 1
                    consecutive_not_found = 0
                else:
                    fail += 1
                    consecutive_not_found += 1
                    print(f'Not found: {url} ({consecutive_not_found} consecutive)')
            except Exception as e:
                print(f'Error: {url} {e}')
                fail += 1
                consecutive_not_found += 1
            if consecutive_not_found >= 5:
                print(f'Skipping to next col_id after 5 consecutive not found for col {col_id} img {img_num}')
                break
print(f'✅ Downloaded {success} images. Failed {fail} attempts.') 