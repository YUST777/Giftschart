#!/usr/bin/env python3
"""
CDN Fixes for telegram_bot.py

This file contains all the fixes needed to resolve CDN path issues
"""

import os
import logging
from urllib.parse import quote
import aiohttp
import asyncio

# CDN Configuration
CDN_BASE_URL = "https://test.asadffastest.store/api"
CDN_HEALTH_URL = "https://test.asadffastest.store/health"

logger = logging.getLogger(__name__)

def normalize_cdn_path(name, path_type="general"):
    """Standardized path normalization for CDN"""
    if path_type == "gift":
        # Handle gift-specific cases
        special_mappings = {
            "B Day Candle": "B_Day_Candle",
            "Durov's Cap": "Durovs_Cap"
        }
        if name in special_mappings:
            return special_mappings[name]
        return name.replace(" ", "_")
    
    elif path_type == "collection":
        return name.replace(" ", "_").replace("-", "_").replace("'", "").replace("&", "").replace("__", "_").lower()
    
    elif path_type == "sticker":
        return name.replace(" ", "_").replace("-", "_").replace("'", "").replace(":", "").replace("__", "_").lower()
    
    else:
        return name.replace(" ", "_").replace("-", "_").replace("'", "").lower()

async def check_cdn_health():
    """Check CDN health before making requests"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CDN_HEALTH_URL, timeout=5) as response:
                return response.status == 200
    except:
        return False

async def get_cdn_url_with_fallback(base_url, fallback_url=None):
    """Get CDN URL with fallback mechanism"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(base_url) as response:
                if response.status == 200:
                    return base_url
                elif fallback_url:
                    return fallback_url
                else:
                    return None
    except:
        return fallback_url if fallback_url else None

def create_safe_cdn_url(base_path, filename, file_type="general"):
    """Create safe CDN URL with proper encoding"""
    normalized_filename = normalize_cdn_path(filename, file_type)
    encoded_filename = quote(normalized_filename)
    return f"{CDN_BASE_URL}/{base_path}/{encoded_filename}"

# Fixes to apply to telegram_bot.py:

FIXES = {
    "imports": """
# Add these imports at the top of telegram_bot.py
from urllib.parse import quote
import aiohttp
""",

    "cdn_functions": """
# Add these functions after the existing helper functions
def normalize_cdn_path(name, path_type="general"):
    \"\"\"Standardized path normalization for CDN\"\"\"
    if path_type == "gift":
        # Handle gift-specific cases
        special_mappings = {
            "B Day Candle": "B_Day_Candle",
            "Durov's Cap": "Durovs_Cap"
        }
        if name in special_mappings:
            return special_mappings[name]
        return name.replace(" ", "_")
    
    elif path_type == "collection":
        return name.replace(" ", "_").replace("-", "_").replace("'", "").replace("&", "").replace("__", "_").lower()
    
    elif path_type == "sticker":
        return name.replace(" ", "_").replace("-", "_").replace("'", "").replace(":", "").replace("__", "_").lower()
    
    else:
        return name.replace(" ", "_").replace("-", "_").replace("'", "").lower()

async def check_cdn_health():
    \"\"\"Check CDN health before making requests\"\"\"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CDN_HEALTH_URL, timeout=5) as response:
                return response.status == 200
    except:
        return False

def create_safe_cdn_url(base_path, filename, file_type="general"):
    \"\"\"Create safe CDN URL with proper encoding\"\"\"
    normalized_filename = normalize_cdn_path(filename, file_type)
    encoded_filename = quote(normalized_filename)
    return f"{CDN_BASE_URL}/{base_path}/{encoded_filename}"
""",

    "inline_query_gift_fix": """
# Replace the gift card URL creation in inline_query function (around line 1784-1785):
# OLD:
# gift_card_url = f"{CDN_BASE_URL}/new_gift_cards/{gift_file_name}_card.png?t={timestamp}"
# gift_image_url = f"{CDN_BASE_URL}/downloaded_images/{gift_file_name}.png?t={timestamp}"

# NEW:
gift_card_url = create_safe_cdn_url("new_gift_cards", f"{gift_file_name}_card.png", "gift") + f"?t={timestamp}"
gift_image_url = create_safe_cdn_url("downloaded_images", f"{gift_file_name}.png", "gift") + f"?t={timestamp}"
""",

    "inline_query_sticker_fix": """
# Replace the sticker URL creation in inline_query function (around line 1880-1882):
# OLD:
# sticker_card_url = f"{CDN_BASE_URL}/sticker_price_cards/{collection_normalized}_{sticker_normalized}_price_card.png?t={timestamp}"
# sticker_image_url = f"{CDN_BASE_URL}/sticker_collections/{collection_normalized}/{sticker_normalized}/{image_number}?t={timestamp}"

# NEW:
sticker_card_filename = f"{collection_normalized}_{sticker_normalized}_price_card.png"
sticker_card_url = create_safe_cdn_url("sticker_price_cards", sticker_card_filename) + f"?t={timestamp}"

# For sticker image, we need to handle the nested path structure:
collection_path = normalize_cdn_path(collection, "collection")
sticker_path = normalize_cdn_path(sticker, "sticker")
sticker_image_url = f"{CDN_BASE_URL}/sticker_collections/{quote(collection_path)}/{quote(sticker_path)}/{quote(image_number)}?t={timestamp}"
""",

    "gift_search_fix": """
# Replace the gift search URL creation (around line 1983-1984):
# OLD:
# gift_card_url = f"{CDN_BASE_URL}/new_gift_cards/{gift_file_name}_card.png?t={timestamp}"
# gift_image_url = f"{CDN_BASE_URL}/downloaded_images/{gift_file_name}.png?t={timestamp}"

# NEW:
gift_card_url = create_safe_cdn_url("new_gift_cards", f"{gift_file_name}_card.png", "gift") + f"?t={timestamp}"
gift_image_url = create_safe_cdn_url("downloaded_images", f"{gift_file_name}.png", "gift") + f"?t={timestamp}"
""",

    "sticker_search_fix": """
# Replace the sticker search URL creation (around line 2016-2025):
# OLD:
# sticker_card_url = f"{CDN_BASE_URL}/sticker_price_cards/{collection_normalized}_{sticker_normalized}_price_card.png"
# sticker_image_url = f"{CDN_BASE_URL}/sticker_collections/{collection_normalized}/{sticker_normalized}/{image_number}?t={timestamp}"

# NEW:
sticker_card_filename = f"{collection_normalized}_{sticker_normalized}_price_card.png"
sticker_card_url = create_safe_cdn_url("sticker_price_cards", sticker_card_filename)

collection_path = normalize_cdn_path(collection, "collection")
sticker_path = normalize_cdn_path(sticker, "sticker")
sticker_image_url = f"{CDN_BASE_URL}/sticker_collections/{quote(collection_path)}/{quote(sticker_path)}/{quote(image_number)}?t={timestamp}"
""",

    "assets_fix": """
# Replace asset URL creation (around lines 1701, 1715, 1729):
# OLD:
# thumbnail_url=f"{CDN_BASE_URL}/assets/giftschart.png",
# thumbnail_url=f"{CDN_BASE_URL}/assets/gifts.png",
# thumbnail_url=f"{CDN_BASE_URL}/assets/stickers.png",

# NEW:
thumbnail_url=create_safe_cdn_url("assets", "giftschart.png"),
thumbnail_url=create_safe_cdn_url("assets", "gifts.png"),
thumbnail_url=create_safe_cdn_url("assets", "stickers.png"),
""",

    "no_result_fix": """
# Replace no result image URL (around line 1958):
# OLD:
# thumbnail_url=f"{CDN_BASE_URL}/assets/no%20result.png",

# NEW:
thumbnail_url=create_safe_cdn_url("assets", "no result.png"),
"""
}

def apply_fixes_to_telegram_bot():
    """Apply all fixes to telegram_bot.py"""
    print("🔧 Applying CDN fixes to telegram_bot.py...")
    
    # Read the current file
    with open("telegram_bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Apply fixes
    original_content = content
    
    # Fix 1: Add imports
    if "from urllib.parse import quote" not in content:
        import_line = "from telegram.error import TelegramError, NetworkError"
        new_imports = """from telegram.error import TelegramError, NetworkError
from urllib.parse import quote
import aiohttp"""
        content = content.replace(import_line, new_imports)
    
    # Fix 2: Add CDN functions
    if "def normalize_cdn_path" not in content:
        # Add after the existing helper functions
        helper_end = content.find("def normalize_gift_filename")
        if helper_end != -1:
            cdn_functions = FIXES["cdn_functions"]
            content = content[:helper_end] + cdn_functions + "\n" + content[helper_end:]
    
    # Fix 3: Fix gift card URLs in inline query
    old_gift_pattern = 'gift_card_url = f"{CDN_BASE_URL}/new_gift_cards/{gift_file_name}_card.png?t={timestamp}"'
    new_gift_pattern = 'gift_card_url = create_safe_cdn_url("new_gift_cards", f"{gift_file_name}_card.png", "gift") + f"?t={timestamp}"'
    content = content.replace(old_gift_pattern, new_gift_pattern)
    
    old_image_pattern = 'gift_image_url = f"{CDN_BASE_URL}/downloaded_images/{gift_file_name}.png?t={timestamp}"'
    new_image_pattern = 'gift_image_url = create_safe_cdn_url("downloaded_images", f"{gift_file_name}.png", "gift") + f"?t={timestamp}"'
    content = content.replace(old_image_pattern, new_image_pattern)
    
    # Fix 4: Fix sticker URLs in inline query
    old_sticker_card_pattern = 'sticker_card_url = f"{CDN_BASE_URL}/sticker_price_cards/{collection_normalized}_{sticker_normalized}_price_card.png?t={timestamp}"'
    new_sticker_card_pattern = '''sticker_card_filename = f"{collection_normalized}_{sticker_normalized}_price_card.png"
                    sticker_card_url = create_safe_cdn_url("sticker_price_cards", sticker_card_filename) + f"?t={timestamp}"'''
    content = content.replace(old_sticker_card_pattern, new_sticker_card_pattern)
    
    # Fix 5: Fix asset URLs
    old_assets_patterns = [
        'thumbnail_url=f"{CDN_BASE_URL}/assets/giftschart.png"',
        'thumbnail_url=f"{CDN_BASE_URL}/assets/gifts.png"',
        'thumbnail_url=f"{CDN_BASE_URL}/assets/stickers.png"',
        'thumbnail_url=f"{CDN_BASE_URL}/assets/no%20result.png"'
    ]
    new_assets_patterns = [
        'thumbnail_url=create_safe_cdn_url("assets", "giftschart.png")',
        'thumbnail_url=create_safe_cdn_url("assets", "gifts.png")',
        'thumbnail_url=create_safe_cdn_url("assets", "stickers.png")',
        'thumbnail_url=create_safe_cdn_url("assets", "no result.png")'
    ]
    
    for old_pattern, new_pattern in zip(old_assets_patterns, new_assets_patterns):
        content = content.replace(old_pattern, new_pattern)
    
    # Write the fixed content
    with open("telegram_bot_fixed.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Fixed version saved as telegram_bot_fixed.py")
    print("📝 Review the changes and replace the original file if satisfied")

if __name__ == "__main__":
    apply_fixes_to_telegram_bot() 