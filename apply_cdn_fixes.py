#!/usr/bin/env python3
"""
Apply CDN Fixes to telegram_bot.py

This script applies all the CDN fixes to improve path handling and URL encoding
"""

import os
import re

def apply_cdn_fixes():
    """Apply all CDN fixes to telegram_bot.py"""
    print("🔧 Applying CDN fixes to telegram_bot.py...")
    
    # Read the current file
    with open("telegram_bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    original_content = content
    
    # Fix 1: Add imports
    if "from urllib.parse import quote" not in content:
        import_line = "from telegram.error import TelegramError, NetworkError"
        new_imports = """from telegram.error import TelegramError, NetworkError
from urllib.parse import quote"""
        content = content.replace(import_line, new_imports)
        print("✅ Added urllib.parse import")
    
    # Fix 2: Add CDN helper functions
    if "def normalize_cdn_path" not in content:
        # Find where to insert the functions (after existing helper functions)
        helper_end = content.find("def normalize_gift_filename")
        if helper_end != -1:
            cdn_functions = '''

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

def create_safe_cdn_url(base_path, filename, file_type="general"):
    """Create safe CDN URL with proper encoding"""
    normalized_filename = normalize_cdn_path(filename, file_type)
    encoded_filename = quote(normalized_filename)
    return f"{CDN_BASE_URL}/{base_path}/{encoded_filename}"
'''
            content = content[:helper_end] + cdn_functions + "\n" + content[helper_end:]
            print("✅ Added CDN helper functions")
    
    # Fix 3: Fix gift card URLs in inline query
    old_gift_pattern = r'gift_card_url = f"{CDN_BASE_URL}/new_gift_cards/\{gift_file_name\}_card\.png\?t=\{timestamp\}"'
    new_gift_pattern = 'gift_card_url = create_safe_cdn_url("new_gift_cards", f"{gift_file_name}_card.png", "gift") + f"?t={timestamp}"'
    content = re.sub(old_gift_pattern, new_gift_pattern, content)
    
    old_image_pattern = r'gift_image_url = f"{CDN_BASE_URL}/downloaded_images/\{gift_file_name\}\.png\?t=\{timestamp\}"'
    new_image_pattern = 'gift_image_url = create_safe_cdn_url("downloaded_images", f"{gift_file_name}.png", "gift") + f"?t={timestamp}"'
    content = re.sub(old_image_pattern, new_image_pattern, content)
    print("✅ Fixed gift card URLs")
    
    # Fix 4: Fix sticker URLs in inline query
    old_sticker_card_pattern = r'sticker_card_url = f"{CDN_BASE_URL}/sticker_price_cards/\{collection_normalized\}_\{sticker_normalized\}_price_card\.png\?t=\{timestamp\}"'
    new_sticker_card_pattern = '''sticker_card_filename = f"{collection_normalized}_{sticker_normalized}_price_card.png"
                    sticker_card_url = create_safe_cdn_url("sticker_price_cards", sticker_card_filename) + f"?t={timestamp}"'''
    content = re.sub(old_sticker_card_pattern, new_sticker_card_pattern, content)
    print("✅ Fixed sticker card URLs")
    
    # Fix 5: Fix asset URLs
    asset_fixes = [
        (r'thumbnail_url=f"{CDN_BASE_URL}/assets/giftschart\.png"', 'thumbnail_url=create_safe_cdn_url("assets", "giftschart.png")'),
        (r'thumbnail_url=f"{CDN_BASE_URL}/assets/gifts\.png"', 'thumbnail_url=create_safe_cdn_url("assets", "gifts.png")'),
        (r'thumbnail_url=f"{CDN_BASE_URL}/assets/stickers\.png"', 'thumbnail_url=create_safe_cdn_url("assets", "stickers.png")'),
        (r'thumbnail_url=f"{CDN_BASE_URL}/assets/no%20result\.png"', 'thumbnail_url=create_safe_cdn_url("assets", "no result.png")')
    ]
    
    for old_pattern, new_pattern in asset_fixes:
        content = re.sub(old_pattern, new_pattern, content)
    print("✅ Fixed asset URLs")
    
    # Fix 6: Fix sticker image URLs with proper path handling
    old_sticker_image_pattern = r'sticker_image_url = f"{CDN_BASE_URL}/sticker_collections/\{collection_normalized\}/\{sticker_normalized\}/\{image_number\}\?t=\{timestamp\}"'
    new_sticker_image_pattern = '''collection_path = normalize_cdn_path(collection, "collection")
                    sticker_path = normalize_cdn_path(sticker, "sticker")
                    sticker_image_url = f"{CDN_BASE_URL}/sticker_collections/{quote(collection_path)}/{quote(sticker_path)}/{quote(image_number)}?t={timestamp}"'''
    content = re.sub(old_sticker_image_pattern, new_sticker_image_pattern, content)
    print("✅ Fixed sticker image URLs")
    
    # Write the fixed content
    with open("telegram_bot_fixed.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Fixed version saved as telegram_bot_fixed.py")
    
    # Show summary of changes
    changes_made = []
    if "from urllib.parse import quote" in content and "from urllib.parse import quote" not in original_content:
        changes_made.append("Added urllib.parse import")
    if "def normalize_cdn_path" in content and "def normalize_cdn_path" not in original_content:
        changes_made.append("Added CDN helper functions")
    if "create_safe_cdn_url" in content:
        changes_made.append("Applied safe CDN URL creation")
    
    print(f"\n📝 Summary of changes:")
    for change in changes_made:
        print(f"  • {change}")
    
    print(f"\n🔍 Review the changes in telegram_bot_fixed.py")
    print(f"📋 If satisfied, replace the original file:")
    print(f"   mv telegram_bot_fixed.py telegram_bot.py")

if __name__ == "__main__":
    apply_cdn_fixes() 