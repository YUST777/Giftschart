import os
import sys
import re

def normalize_name(name):
    # Lowercase, replace all non-alphanumeric with _, collapse multiple _, trim _
    name = name.strip().lower()
    name = re.sub(r'[^a-z0-9]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

def normalize_sticker_collections(base_dir):
    for root, dirs, files in os.walk(base_dir, topdown=False):
        # Normalize files
        for fname in files:
            new_fname = normalize_name(fname)
            if fname != new_fname:
                src = os.path.join(root, fname)
                dst = os.path.join(root, new_fname)
                if not os.path.exists(dst):
                    os.rename(src, dst)
        # Normalize directories
        for dname in dirs:
            new_dname = normalize_name(dname)
            if dname != new_dname:
                src = os.path.join(root, dname)
                dst = os.path.join(root, new_dname)
                if not os.path.exists(dst):
                    os.rename(src, dst)

if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else 'sticker_collections'
    normalize_sticker_collections(base)
    print(f'✅ Normalized all folder and file names in {base}') 