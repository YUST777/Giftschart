import stickers_tools_api as api
import os
import json
import re

def normalize_name(name):
    name = name.strip().lower()
    name = re.sub(r'[^a-z0-9]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

# Get live stats
stats = api.get_sticker_stats(force_refresh=True)
base = 'sticker_collections'
missing = []
matched = []

for c in stats['collections'].values():
    collection = normalize_name(c['name'])
    for s in c['stickers']:
        sticker = normalize_name(s['name'])
        found = False
        for root, dirs, files in os.walk(base):
            root_norm = normalize_name(os.path.relpath(root, base))
            if collection in root_norm and sticker in root_norm:
                for file in files:
                    if normalize_name(file).endswith('png') or normalize_name(file).endswith('jpg'):
                        found = True
                        matched.append({
                            'collection': collection,
                            'sticker': sticker,
                            'image_path': os.path.join(root, file)
                        })
                        break
            if found:
                break
        if not found:
            missing.append({
                'collection': collection,
                'sticker': sticker
            })

report = {'matched': matched, 'missing': missing}
with open('sticker_card_match_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f'✅ Matched {len(matched)} sticker price cards to images.')
if missing:
    print(f'❌ {len(missing)} price cards have no matching sticker image:')
    for entry in missing:
        print(f"  - {entry['collection']} / {entry['sticker']}")
else:
    print('🎉 All price cards have matching sticker images!') 