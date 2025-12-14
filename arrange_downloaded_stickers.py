import os
import shutil

src_base = 'downloaded_missing_stickers'
dst_base = 'sticker_collections'

moved = 0
skipped = 0
for folder in os.listdir(src_base):
    folder_path = os.path.join(src_base, folder)
    if not os.path.isdir(folder_path):
        continue
    # Split folder name into collection and pack
    if '_' in folder:
        parts = folder.split('_')
        # Try to find the split between collection and pack
        for i in range(1, len(parts)):
            collection = '_'.join(parts[:i])
            pack = '_'.join(parts[i:])
            dst_collection = os.path.join(dst_base, collection)
            if os.path.exists(dst_collection):
                dst_pack = os.path.join(dst_collection, pack)
                os.makedirs(dst_pack, exist_ok=True)
                for img_num in range(1, 6):
                    src_img = os.path.join(folder_path, f'{img_num}.png')
                    dst_img = os.path.join(dst_pack, f'{img_num}.png')
                    if os.path.exists(src_img):
                        shutil.copy2(src_img, dst_img)
                        print(f'Moved: {src_img} -> {dst_img}')
                        moved += 1
                    else:
                        skipped += 1
                break
        else:
            # If no match, just use first as collection, rest as pack
            collection = parts[0]
            pack = '_'.join(parts[1:])
            dst_pack = os.path.join(dst_base, collection, pack)
            os.makedirs(dst_pack, exist_ok=True)
            for img_num in range(1, 6):
                src_img = os.path.join(folder_path, f'{img_num}.png')
                dst_img = os.path.join(dst_pack, f'{img_num}.png')
                if os.path.exists(src_img):
                    shutil.copy2(src_img, dst_img)
                    print(f'Moved: {src_img} -> {dst_img}')
                    moved += 1
                else:
                    skipped += 1
    else:
        dst_collection = os.path.join(dst_base, folder)
        os.makedirs(dst_collection, exist_ok=True)
        for img_num in range(1, 6):
            src_img = os.path.join(folder_path, f'{img_num}.png')
            dst_img = os.path.join(dst_collection, f'{img_num}.png')
            if os.path.exists(src_img):
                shutil.copy2(src_img, dst_img)
                print(f'Moved: {src_img} -> {dst_img}')
                moved += 1
            else:
                skipped += 1
print(f'✅ Moved {moved} images. Skipped {skipped} missing files.') 