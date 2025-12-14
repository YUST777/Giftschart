import os
import requests

base_url = 'https://cdn.stickerdom.store/{col_id}/p/{pack_id}/{img_num}.png?v=3'
out_base = 'aggressive_cdn_scrape'

success = 0
fail = 0
for col_id in range(1, 51):
    for pack_id in range(1, 121):
        for img_num in range(1, 6):
            found = False
            for offset in range(0, 6):  # Try pack_id, pack_id+1, ..., pack_id+5
                try_pack_id = pack_id + offset
                url = base_url.format(col_id=col_id, pack_id=try_pack_id, img_num=img_num)
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
                        found = True
                        break  # Stop after first found image for this img_num
                    else:
                        fail += 1
                except Exception as e:
                    print(f'Error: {url} {e}')
                    fail += 1
            if not found:
                print(f'No image found for col {col_id} pack {pack_id} img {img_num} (tried offsets 0-5)')
print(f'✅ Downloaded {success} images. Failed {fail} attempts.') 