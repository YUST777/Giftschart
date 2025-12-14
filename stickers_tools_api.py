import requests
import re

_API_URL = "https://stickers.tools/api/stats"

def normalize_name(name):
    name = name.strip().lower()
    name = re.sub(r'[^a-z0-9]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

# NOTE: All collection and sticker name handling in the codebase should be normalized to lowercase for case-insensitive matching with filesystem.
def get_sticker_stats(force_refresh=False):
    response = requests.get(_API_URL)
    response.raise_for_status()
    return response.json()

def get_sticker_price(collection, sticker, force_refresh=True):
    stats = get_sticker_stats(force_refresh=force_refresh)
    collection_norm = normalize_name(collection)
    sticker_norm = normalize_name(sticker)
    for c in stats['collections'].values():
        if normalize_name(c['name']) == collection_norm:
            for s in c['stickers']:
                if normalize_name(s['name']) == sticker_norm:
                    def safe_float(val):
                        try:
                            return float(val)
                        except (TypeError, ValueError):
                            return 0.0
                    return {
                        'floor_price_ton': safe_float(s.get('floor_price_ton', 0)),
                        'floor_price_usd': safe_float(s.get('floor_price_usd', 0)),
                        'supply': s.get('supply', 0),
                        'initial_supply': s.get('initial_supply', 0),
                        'init_price_usd': safe_float(s.get('init_price_usd', 0))
                    }
    return None 