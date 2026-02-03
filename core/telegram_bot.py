#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys

# Add project root to path for config imports
_project_root = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(_project_root) != 'giftschart':
    _project_root = os.path.dirname(_project_root)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import random
import logging
import re
import time
import datetime
import asyncio
import socket
import subprocess
import threading
import signal
from difflib import get_close_matches
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto, InputMediaPhoto, InlineQueryResultArticle, InputTextMessageContent, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import MessageEntityType, ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, InlineQueryHandler
from uuid import uuid4
from telegram.error import TelegramError, NetworkError
from urllib.parse import quote
from httpx import HTTPError, ConnectError, ProxyError

# Import centralized paths
from config.paths import PROJECT_ROOT, GIFT_CARDS_DIR, ASSETS_DIR, CACHE_DIR

# Import premium system functions
try:
    from core.premium_system import handle_premium_status
except ImportError:
    handle_premium_status = None

# Import bot configuration
try:
    from core.bot_config import (
        BOT_TOKEN, BOT_USERNAME, RESPOND_TO_ALL_MESSAGES, USE_DIRECT_IP, API_TELEGRAM_IP, SKIP_SSL_VERIFY, SPECIAL_GROUPS,
        DEFAULT_BUY_SELL_LINK, DEFAULT_TONNEL_LINK, DEFAULT_PALACE_LINK, DEFAULT_PORTAL_LINK, DEFAULT_MRKT_LINK,
        HELP_IMAGE_PATH
    )
except ImportError:
    # Default values if config file is missing
    BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TOKEN_HERE")
    BOT_USERNAME = "@YourBotUsername"
    RESPOND_TO_ALL_MESSAGES = False
    USE_DIRECT_IP = False
    API_TELEGRAM_IP = "149.154.167.220"
    SKIP_SSL_VERIFY = False
    SPECIAL_GROUPS = {}
    DEFAULT_BUY_SELL_LINK = "https://t.me/tonnel_network_bot/gifts?startapp=ref_7660176383"
    DEFAULT_TONNEL_LINK = "https://t.me/tonnel_network_bot/gifts?startapp=ref_7660176383"
    DEFAULT_PALACE_LINK = "https://t.me/palacenftbot/app?startapp=zOyJPdbc9t"
    DEFAULT_PORTAL_LINK = "https://t.me/portals/market?startapp=q7iu6i"
    DEFAULT_MRKT_LINK = "https://t.me/mrkt/app?startapp=7660176383"
    HELP_IMAGE_PATH = os.path.join(ASSETS_DIR, "help.jpg")

# Enable logging (with reduced verbosity for HTTP requests)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Reduce logging for HTTP requests
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Use INFO level instead of DEBUG for less verbosity

# Helper function for timestamp filtering
def is_message_too_old(update: Update, max_age_seconds: int = 300) -> bool:
    """Check if a message is too old to process (prevents processing old messages when bot comes back online)."""
    if not update.message:
        return False
        
    message_time = update.message.date
    current_time = datetime.datetime.now(message_time.tzinfo)
    time_difference = current_time - message_time
    
    if time_difference.total_seconds() > max_age_seconds:
        logger.info(f"Ignoring old message from {time_difference.total_seconds():.0f} seconds ago: {update.message.text[:50] if update.message.text else 'No text'}...")
        return True
    return False

# Helper function to sanitize callback data
def sanitize_callback_data(text: str) -> str:
    """Sanitize text for use in Telegram callback data (only alphanumeric, underscore, hyphen allowed)."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', text)

# Helper function to desanitize callback data back to original name
def desanitize_callback_data(sanitized_text: str) -> str:
    """Convert sanitized callback data back to original gift name."""
    # Handle special cases first
    special_mappings = {
        "Jack_in_the_Box": "Jack-in-the-Box",
        "Durovs_Cap": "Durov's Cap"
    }
    
    if sanitized_text in special_mappings:
        return special_mappings[sanitized_text]
    
    # For general cases, replace underscores with spaces
    return sanitized_text.replace("_", " ")

# Get path to gift cards - uses centralized config
# GIFT_CARDS_DIR is imported from config.paths

# Check for Place Market sticker functionality
try:
    import place_market_integration
    from place_market_integration import (
        send_sticker_card, 
        find_matching_stickers,
        sticker_start_command,
        sticker_help_command,
        sticker_search_command,
        sticker_collection_command,
        sticker_pack_command
    )
    STICKERS_AVAILABLE = place_market_integration.check_database()
    logger.info(f"Place Market sticker functionality {'available' if STICKERS_AVAILABLE else 'not available'}")
except ImportError:
    STICKERS_AVAILABLE = False
    logger.warning("Place Market sticker functionality not available")

# Get available gift names
names = None

# Try importing from bot_config first
try:
    from core.bot_config import names
except ImportError:
    pass

# Try importing from main as fallback
if not names:
    try:
        from main import names
    except ImportError:
        pass

# Use hardcoded fallback if imports fail
if not names:
    names = [
        "Heart Locket", "Lush Bouquet", "Astral Shard", "B-Day Candle", "Berry Box",
        "Big Year", "Bonded Ring", "Bow Tie", "Bunny Muffin", "Candy Cane",
        "Cookie Heart", "Crystal Ball", "Desk Calendar", "Diamond Ring", "Durov's Cap",
        "Easter Egg", "Electric Skull", "Eternal Candle", "Eternal Rose", "Evil Eye",
        "Flying Broom", "Gem Signet", "Genie Lamp", "Ginger Cookie", "Hanging Star",
        "Heroic Helmet", "Hex Pot", "Holiday Drink", "Homemade Cake", "Hypno Lollipop",
        "Ion Gem", "Jack-in-the-Box", "Jelly Bunny", "Jester Hat", "Jingle Bells",
        "Kissed Frog", "Light Sword", "Lol Pop", "Loot Bag", "Love Candle",
        "Love Potion", "Lunar Snake", "Mad Pumpkin", "Magic Potion", "Mini Oscar",
        "Nail Bracelet", "Neko Helmet", "Party Sparkler", "Perfume Bottle", "Pet Snake",
        "Plush Pepe", "Precious Peach", "Record Player", "Restless Jar", "Sakura Flower",
        "Santa Hat", "Scared Cat", "Sharp Tongue", "Signet Ring", "Skull Flower",
        "Sleigh Bell", "Snake Box", "Snow Globe", "Snow Mittens", "Spiced Wine",
        "Spy Agaric", "Star Notepad", "Swiss Watch", "Tama Gadget", "Top Hat",
        "Toy Bear", "Trapped Heart", "Vintage Cigar", "Voodoo Doll", "Winter Wreath",
        "Witch Hat", "Xmas Stocking"
    ]

# Create a lowercase and simplified version of each name for better matching
simplified_names = {}
# Only exclude these very common words as parts
exclude_words = ["the", "and", "of", "for", "with", "in", "on", "at", "by"]

for name in names:
    # Create variations of the name for matching
    simple_name = name.lower().replace('-', ' ').replace("'", '')
    simplified_names[simple_name] = name
    
    # Add hyphenated variations if applicable
    if "-" in name:
        no_hyphen = name.lower().replace("-", " ")
        simplified_names[no_hyphen] = name
    
    # Add apostrophe variations if applicable
    if "'" in name:
        no_apostrophe = name.lower().replace("'", "")
        simplified_names[no_apostrophe] = name
    
    # Add individual parts of names for better partial matching
    parts = simple_name.split()
    for part in parts:
        # Only add substantial parts (3+ chars) that aren't common words
        if len(part) >= 3 and part not in exclude_words:
            # For ambiguous words (same part in multiple gifts), we'll still add them
            # This makes matching more inclusive but might lead to multiple matches
            simplified_names[part] = name

# Import the callback handler from the external module
try:
    # Import the callback handler from the external module
    from core.callback_handler import callback_handler as external_callback_handler
    
    # Create a wrapper function that will use the imported handler
    async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Forward callback queries to the proper handler in callback_handler.py"""
        query = update.callback_query
        data = query.data
        
        logger.info(f"Received callback query: {data}")
        logger.info(f"Callback from user {update.effective_user.id} in chat {update.effective_chat.id} (type: {update.effective_chat.type})")
        
        # Check if this is a help callback - handle it directly here
        if data == "help":
            logger.info("Handling help callback directly in main handler")
            await show_help_page(update, context, page=1)
            return
        
        # Check if this is a help page navigation callback
        if data.startswith("help_page_"):
            logger.info(f"Handling help page navigation: {data}")
            try:
                page_number = int(data.split("_")[-1])
                await show_help_page(update, context, page=page_number)
            except (ValueError, IndexError):
                logger.error(f"Invalid help page number in callback: {data}")
                await query.answer("Invalid page number", show_alert=True)
            return
        
        # Check if this is a configure callback
        if data.startswith("edit_"):
            logger.info("Handling configure callback")
            if data == "edit_done":
                await configure_done_handler(update, context)
            else:
                await configure_callback_handler(update, context)
            return
        

        
        # Check if this is a sticker-related callback
        if data.startswith("sticker_"):
            # Handle sticker-related callbacks with the sticker integration
            try:
                from services import sticker_integration
                await sticker_integration.handle_sticker_callback(update, context)
            except ImportError:
                logger.error("Sticker integration not available")
                await query.answer("Sticker functionality not available")
            return
        
        # Check if this is a refund-related callback
        if data.startswith("refund_"):
            await handle_refund_callback(update, context)
            return
        

            
        # Use the regular callback handler for other callbacks
        logger.info(f"Forwarding callback '{data}' to external handler")
        await external_callback_handler(update, context)
        
except ImportError:
    logger.warning("Callback handler not found. Creating a basic one.")
    async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        
        logger.info(f"Fallback callback handler received: {query.data}")
        
        # Check if this is a help callback
        if query.data == "help":
            logger.info("Handling help callback in fallback handler")
            await show_help_page(update, context, page=1)
            return
        
        # Check if this is a help page navigation callback
        if query.data.startswith("help_page_"):
            logger.info(f"Handling help page navigation in fallback handler: {query.data}")
            try:
                page_number = int(query.data.split("_")[-1])
                await show_help_page(update, context, page=page_number)
            except (ValueError, IndexError):
                logger.error(f"Invalid help page number in callback: {query.data}")
                await query.answer("Invalid page number", show_alert=True)
            return
        

        
        # Check if this is a sticker-related callback
        if query.data.startswith("sticker_"):
            # Handle sticker-related callbacks with the sticker integration
            try:
                from services import sticker_integration
                await sticker_integration.handle_sticker_callback(update, context)
            except ImportError:
                logger.error("Sticker integration not available")
                await query.answer("Sticker functionality not available")
            return
        
        # Check if this is a refund-related callback
        if query.data.startswith("refund_"):
            await handle_refund_callback(update, context)
            return
        

            
        await query.message.reply_text("Callback handling is not fully set up.")

# Import the image uploader
# Image uploader (Catbox fallback) - DISABLED per user request
IMAGE_UPLOADER_AVAILABLE = False
# try:
#     from image_uploader import get_gift_card_url
#     IMAGE_UPLOADER_AVAILABLE = True
#     logger.info("Image uploader available.")
# except ImportError:
#     logger.warning("Image uploader not available. Inline images will not work correctly.")
#     IMAGE_UPLOADER_AVAILABLE = False

# Admin dashboard removed
ADMIN_DASHBOARD_AVAILABLE = False

# We use catbox.moe for image hosting via image_uploader.py


def format_display_name(name):
    """Convert snake_case or underscored names to proper Title Case for display.
    
    Examples:
        'bored_stickers' -> 'Bored Stickers'
        'cool_cats' -> 'Cool Cats'
        '2092' -> '#2092' (numeric sticker IDs get # prefix)
    """
    if not name:
        return name
    
    # If it's just a number (sticker ID), add # prefix
    if name.isdigit():
        return f"#{name}"
    
    # Replace underscores with spaces and title case
    formatted = name.replace('_', ' ').title()
    return formatted


def normalize_cdn_path(name, path_type="general"):
    """Standardized path normalization for CDN - matches generator's normalize_name()"""
    if path_type == "gift":
        # Handle gift-specific cases
        special_mappings = {
            "B Day Candle": "B_Day_Candle",
            "Durov's Cap": "Durovs_Cap"
        }
        if name in special_mappings:
            return special_mappings[name]
        return name.replace(" ", "_")
    
    elif path_type == "collection" or path_type == "sticker":
        # Use same logic as generator's normalize_name() for robust matching
        normalized = name.strip().lower()
        normalized = re.sub(r'[^a-z0-9]', '_', normalized)  # Replace ALL non-alphanumeric with _
        normalized = re.sub(r'_+', '_', normalized)          # Collapse multiple _ to single _
        return normalized.strip('_')
    
    else:
        # Fallback: also use robust normalization
        normalized = name.strip().lower()
        normalized = re.sub(r'[^a-z0-9]', '_', normalized)
        normalized = re.sub(r'_+', '_', normalized)
        return normalized.strip('_')

# CDN Configuration - Import from bot_config (do not hardcode!)
try:
    from bot_config import CDN_BASE_URL
except ImportError:
    CDN_BASE_URL = "https://giftschart.the01studio.xyz/api"  # Fallback

def create_safe_cdn_url(base_path, filename, file_type="general"):
    """Create safe CDN URL with proper encoding"""
    # Don't normalize filenames that have file extensions (e.g., .webp, .png)
    # The normalize function replaces '.' with '_' which breaks URLs
    if '.' in filename and filename.rsplit('.', 1)[-1] in ['webp', 'png', 'jpg', 'jpeg', 'gif']:
        encoded_filename = quote(filename)
        return f"{CDN_BASE_URL}/{base_path}/{encoded_filename}"
    
    normalized_filename = normalize_cdn_path(filename, file_type)
    encoded_filename = quote(normalized_filename)
    return f"{CDN_BASE_URL}/{base_path}/{encoded_filename}"

def normalize_gift_filename(gift_name):
    # Handles all special and general cases for gift card filenames
    if gift_name == "Jack-in-the-Box":
        return "Jack_in_the_Box"
    elif gift_name == "Durov's Cap":
        return "Durovs_Cap"
    elif gift_name == "Swag Bag":
        return "SwagBag"
    elif gift_name == "West Sign":
        return "WestsideSign"
    elif gift_name == "B-Day Candle":
        return "B_Day_Candle"

    else:
        return gift_name.replace(" ", "_").replace("-", "_").replace("'", "")

def get_high_value_sticker_priority(collection, sticker):
    """Get priority for high-value stickers (lower number = higher priority) - Updated with current API data"""
    # High-value stickers in order of priority (highest price first) - Updated from API data
    high_value_stickers = [
        ("DOGS Rewards", "Gold bone"),                    # 19,465 TON
        ("Project Soap", "Tyler Gold Edition"),          # 719.98 TON
        ("DOGS OG", "Not Cap"),                          # 420.02 TON
        ("Project Soap", "Tyler Mode: On"),              # 319.27 TON
        ("Pudgy Penguins", "Ice Pengu"),                 # 281.25 TON
        ("CHIMPERS", "GENESIS ENERGY"),                  # 144.90 TON
        ("DOGS OG", "Sheikh"),                           # 120.75 TON
        ("Pudgy & Friends", "Pengu x Baby Shark"),       # 120.00 TON
        ("Pudgy Penguins", "Cool Blue Pengu"),           # 111.00 TON
        ("Sappy", "Sappy Originals"),                    # 79.00 TON
        ("Sticker Pack", "Freedom"),                     # 67.50 TON
        ("No signal", "Error #1"),                       # 67.50 TON
        ("CITY Holder", "Holder's Guide"),               # 64.12 TON
        ("Pudgy & Friends", "Pengu x NASCAR"),           # 59.96 TON
        ("Notcoin", "Flags"),                            # 57.99 TON
        ("Bored Ape Yacht Club", "Bored Ape Originals"), # 54.00 TON
        ("Pudgy Penguins", "Midas Pengu"),               # 50.00 TON
        ("Pudgy Penguins", "Pengu CNY"),                 # 44.33 TON
        ("Pudgy Penguins", "Blue Pengu"),                # 42.75 TON
        ("DOGS Rewards", "Silver bone"),                 # 40.08 TON
        ("Azuki", "Raizan"),                             # 38.00 TON
        ("Not Pixel", "Cute pack"),                      # 37.00 TON
        ("Moonbirds", "Moonbirds Originals"),            # 35.14 TON
        ("Not Pixel", "Random memes"),                   # 33.90 TON
        ("Bored Stickers", "3278"),                      # 30.99 TON
        ("Azuki", "Shao"),                               # 28.99 TON
        ("Lil Pudgys", "Lil Pudgys x Baby Shark"),       # 22.67 TON
        ("Mr. Freeman", "Eat. Shit. Laugh."),            # 20.02 TON
        ("Doodles", "OG Icons"),                         # 19.55 TON
        ("Pudgy Penguins", "Pengu Valentines"),          # 19.09 TON
        ("Bored Stickers", "3151"),                      # 18.32 TON
        ("Ponke", "Ponke Day Ones"),                     # 18.00 TON
        ("VOID", "VOID Dudes"),                          # 18.00 TON
        ("Bored Stickers", "6527"),                      # 16.00 TON
        ("Bored Stickers", "9780"),                      # 16.00 TON
        ("Lazy & Rich", "Sloth Capital"),                # 15.75 TON
        ("Doodles", "Doodles Dark Mode"),                # 15.64 TON
        ("Bored Stickers", "2092"),                      # 14.95 TON
        ("SUNDOG", "TO THE SUN"),                        # 14.62 TON
        ("Pudgy Penguins", "Classic Pengu"),             # 13.80 TON
        ("DOGS Unleashed", "Bones"),                     # 12.94 TON
        ("DOGS OG", "King"),                             # 12.38 TON
        ("CyberKongz", "Wilson"),                        # 11.97 TON
        ("DOGS OG", "Knitted Hat"),                      # 11.81 TON
        ("Not Pixel", "Tournament S1"),                  # 11.48 TON
        ("Notcoin", "Not Memes"),                        # 11.36 TON
        ("Not Pixel", "Smileface pack"),                 # 10.93 TON
        ("DOGS OG", "Shaggy"),                           # 10.11 TON
        ("DOGS OG", "Viking"),                           # 9.56 TON
        ("Not Pixel", "Films memes")                     # 9.50 TON
    ]
    
    # Normalize for comparison
    collection_lower = collection.lower()
    sticker_lower = sticker.lower()
    
    for i, (priority_collection, priority_sticker) in enumerate(high_value_stickers):
        if collection_lower == priority_collection.lower() and sticker_lower == priority_sticker.lower():
            return i  # Return priority index (0 = highest priority)
    
    return 999  # Low priority for other stickers

def get_sticker_image_number(collection, sticker):
    """Get the correct image number for a sticker based on CDN data"""
    # Normalize names for lookup - handle special characters properly
    collection_normalized = collection.replace(" ", "_").replace("-", "_").replace("'", "").replace("&", "").replace("__", "_").lower()
    sticker_normalized = sticker.replace(" ", "_").replace("-", "_").replace("'", "").replace(":", "").replace("__", "_").lower()
    
    # CDN data mapping based on the API response
    sticker_images = {
        # Dogs OG - most use 1_png
        "dogs_og": {
            "alien": "1_png", "alumni": "1_png", "anime_ears": "1_png", "asterix": "1_png",
            "baseball_bat": "1_png", "baseball_cap": "1_png", "blue_eyes_hat": "1_png",
            "bodyguard": "1_png", "bow_tie": "1_png", "cherry_glasses": "1_png",
            "cook": "1_png", "cyclist": "1_png", "diver": "1_png", "dogtor": "1_png",
            "dog_tyson": "1_png", "duck": "1_png", "emo_boy": "1_png", "extra_eyes": "1_png",
            "frog_glasses": "1_png", "frog_hat": "1_png", "gentleman": "1_png",
            "gnome": "1_png", "google_intern_hat": "1_png", "green_hair": "1_png",
            "hello_kitty": "1_png", "hypnotist": "1_png", "ice_cream": "1_png",
            "jester": "1_png", "kamikaze": "1_png", "kfc": "1_png",
            "king": "8_png", "og_king": "1_png", "knitted_hat": "1_png", "nerd": "1_png",
            "newsboy_cap": "1_png", "noodles": "1_png", "nose_glasses": "1_png",
            "not_cap": "1_png", "og_not_cap": "1_png", "not_coin": "1_png",
            "one_piece_sanji": "1_png", "orange_hat": "1_png", "panama_hat": "1_png",
            "pilot": "1_png", "pink_bob": "1_png", "princess": "1_png", "robber": "1_png",
            "santa_dogs": "1_png", "scarf": "1_png", "scary_eyes": "1_png",
            "shaggy": "1_png", "sharky_dog": "1_png", "sheikh": "1_png", "og_sheikh": "1_png",
            "sherlock_holmes": "1_png", "smile": "1_png", "sock_head": "1_png",
            "strawberry_hat": "1_png", "tank_driver": "1_png", "tattoo_artist": "1_png",
            "teletubby": "1_png", "termidogtor": "1_png", "tin_foil_hat": "1_png",
            "toast_bread": "1_png", "toddler": "1_png", "tubeteyka": "1_png",
            "unicorn": "1_png", "ushanka": "1_png", "van_dogh": "1_png",
            "viking": "1_png", "witch": "1_png"
        },
        # Blum collection
        "blum": {
            "bunny": "18_png", "cap": "3_png", "cat": "7_png", "cook": "7_png",
            "curly": "20_png", "general": "4_png", "no": "2_png", "worker": "15_png"
        },
        # Not Pixel collection
        "not_pixel": {
            "cute_pack": "11_png", "diamond_pixel": "15_png", "dogs_pixel": "15_png",
            "error_pixel": "15_png", "films_memes": "1_png", "grass_pixel": "15_png",
            "macpixel": "15_png", "pixanos": "15_png", "pixel_phrases": "1_png",
            "pixioznik": "15_png", "random_memes": "9_png", "retro_pixel": "15_png",
            "smileface_pack": "4_png", "superpixel": "15_png", "tournament_s1": "1750388827892_png",
            "vice_pixel": "15_png", "zompixel": "15_png"
        },
        # Pudgy Penguins
        "pudgy_penguins": {
            "blue_pengu": "3_png", "classic_pengu": "1_png", "cool_blue_pengu": "3_png", 
            "ice_pengu": "1_png", "midas_pengu": "1_png", "pengu_cny": "10_png",
            "pengu_valentines": "3_png"
        },
        # Flappy Bird
        "flappy_bird": {
            "blue_wings": "15_png", "blush_flight": "15_png", "frost_flap": "6_png",
            "light_glide": "15_png", "ruby_wings": "6_png"
        },
        # Other collections with specific numbers
        "azuki": {"raizan": "1_png", "shao": "9_png"},
        "babydoge": {"mememania": "13_png"},
        "baby_shark": {"doo_doo_moods": "2_png"},
        "bored_ape_yacht_club": {"bored_ape_originals": "1_png"},
        "bored_stickers": {
            "3151": "5_png", "3278": "5_png", "4017": "5_png", "5824": "5_png",
            "6527": "5_png", "9287": "5_png", "9765": "5_png", "9780": "5_png",
            "cny_2092": "8_png"
        },
        "cattea_life": {"cattea_chaos": "7_png"},
        "chimpers": {"genesis_energy": "1_png"},
        "claynosaurz": {"red_rex_pack": "1_png"},
        "cyberkongz": {"wilson": "1_png"},
        "dogs_rewards": {
            "full_dig": "1_png", "gold_bone": "1_png", "silver_bone": "1_png"
        },
        "dogs_unleashed": {"bones": "1_png"},
        "doodles": {
            "doodles_dark_mode": "7_png",
            "og_icons": "da9119b67185e0dd76a1186883737c6e_png"
        },
        "imaginary_ones": {"panda_warrior": "1_png"},
        "kudai": {"gmi": "7_png", "ngmi": "4_png"},
        "lazy_rich": {"chill_or_thrill": "1_png", "sloth_capital": "1_png"},
        "lil_pudgys": {"lil_pudgys_x_baby_shark": "1_png"},
        "lost_dogs": {"lost_memeries": "4_png", "magic_of_the_way": "1_png"},
        "moonbirds": {"moonbirds_originals": "1_png"},
        "notcoin": {"flags": "2_png", "not_memes": "picsart_25_06_20_05_55_41_906_png"},
        "ponke": {"ponke_day_ones": "1_png"},
        "project_soap": {"tyler_mode_on": "1_png", "tyler_gold_edition": "1_png"},
        "pucca": {"pucca_moods": "6_png"},
        "pudgy_friends": {"pengu_x_baby_shark": "1_png", "pengu_x_nascar": "1_png"},
        "ric_flair": {"ric_flair": "2_png"},
        "sappy": {"sappy_originals": "1_png"},
        "smeshariki": {"chamomile_valley": "13_png", "the_memes": "6_png"},
        "sticker_pack": {"freedom": "1_png"},
        "sundog": {"to_the_sun": "4_png"},
        "wagmi_hub": {"egg_hammer": "1_png", "wagmi_ai_agent": "3_png"},
        # New collections
        "void": {"void_dudes": "1_png"},
        "mr_freeman": {"eat_shit_laugh": "1_png"},
        "no_signal": {"error_1": "1_png"},
        "city_holder": {"holder_s_guide": "1_png"}
    }
    
    # Get the image number for this specific sticker
    if collection_normalized in sticker_images:
        if sticker_normalized in sticker_images[collection_normalized]:
            return sticker_images[collection_normalized][sticker_normalized]
    
    # Default to 1_png if not found
    return "1_png"

# Function to get a gift card by name
def get_gift_card_by_name(gift_name):
    # Normalize gift name for file matching
    normalized_name = normalize_gift_filename(gift_name)
    
    # Check if this is a plus premarket gift (uses different filename format)
    is_plus_premarket = False
    try:
        from plus_premarket_gifts import is_plus_premarket_gift
        is_plus_premarket = is_plus_premarket_gift(gift_name)
    except ImportError:
        pass
    
    # Plus premarket gifts use filename without _card suffix
    if is_plus_premarket:
        filename = f"{normalized_name}.webp"
    else:
        filename = f"{normalized_name}_card.webp"
    
    filepath = os.path.join(GIFT_CARDS_DIR, filename)
    
    # Check if file exists
    if os.path.exists(filepath):
        logger.info(f"Found existing card for {gift_name}: {filepath}")
        return filepath
    
    # If not found, try the alternative format (for backward compatibility)
    if is_plus_premarket:
        # Try with _card suffix as fallback
        alt_filename = f"{normalized_name}_card.webp"
        alt_filepath = os.path.join(GIFT_CARDS_DIR, alt_filename)
        if os.path.exists(alt_filepath):
            logger.info(f"Found existing card for {gift_name} (alt format): {alt_filepath}")
            return alt_filepath
    else:
        # Try without _card suffix as fallback
        alt_filename = f"{normalized_name}.webp"
        alt_filepath = os.path.join(GIFT_CARDS_DIR, alt_filename)
        if os.path.exists(alt_filepath):
            logger.info(f"Found existing card for {gift_name} (alt format): {alt_filepath}")
            return alt_filepath
    
    # If not found, log for debugging
    logger.info(f"Card not found for {gift_name} at {filepath}")
    
    # If not, it might be a name we need to generate
    return None

# Get pre-generated gift card (no on-demand generation)
def generate_gift_card(gift_file_name):
    try:
        logger.info(f"generate_gift_card called for: {gift_file_name}")
        
        # Convert file_name to display name for the card generator
        gift_display_name = gift_file_name.replace("_", " ")
        
        normalized_filename = normalize_gift_filename(gift_file_name)
        logger.info(f"Normalized filename: {normalized_filename}")
        
        # Check if the pre-generated card exists
        card_path = get_gift_card_by_name(gift_file_name)
        if card_path:
            logger.info(f"Found pre-generated card: {card_path}")
            return card_path
            
        logger.info(f"No pre-generated card found for {gift_file_name}, checking timestamp...")
        
        # If card doesn't exist, check if we need to regenerate all cards
        from config.paths import LAST_GENERATION_TIME_FILE
        timestamp_file = LAST_GENERATION_TIME_FILE
        current_time = int(time.time())
        
        if os.path.exists(timestamp_file):
            try:
                with open(timestamp_file, 'r') as f:
                    last_time = int(f.read().strip())
                
                elapsed_minutes = (current_time - last_time) / 60
                
                # If more than 32 minutes have passed, regenerate cards
                if elapsed_minutes >= 32:
                    logging.info("Cards are stale, triggering regeneration")
                    # Run the pregeneration script in the background
                    subprocess.Popen([sys.executable, os.path.join(PROJECT_ROOT, "pregenerate_gift_cards.py")])
            except Exception as e:
                logging.error(f"Error checking timestamp: {e}")
        else:
            # No timestamp file, trigger regeneration
            logging.info("No timestamp file found, triggering regeneration")
            subprocess.Popen([sys.executable, os.path.join(PROJECT_ROOT, "pregenerate_gift_cards.py")])
        
        # Try one more time to get the card (it might exist now)
        card_path = get_gift_card_by_name(gift_file_name)
        if card_path:
            logger.info(f"Found card after regeneration check: {card_path}")
            return card_path
            
        # If we still don't have the card, generate it on demand as a fallback
        logging.info(f"Pre-generated card not found for {gift_file_name}, generating on demand")
        import gift_card_generator
        gift_card_generator.generate_specific_gift(gift_display_name)
        
        # Get the card path using the file_name format
        final_card_path = get_gift_card_by_name(gift_file_name)
        logger.info(f"Final card path after on-demand generation: {final_card_path}")
        return final_card_path
    except Exception as e:
        logging.error(f"Error getting gift card for {gift_file_name}: {e}")
        return None

# Get list of all available gift cards in the directory
def get_available_gift_cards():
    """Get all available gift cards including both _card.webp and .png files"""
    if os.path.exists(GIFT_CARDS_DIR):
        # Get both _card.webp files (regular gifts) and .png files (+premarket gifts)
        card_files = [f for f in os.listdir(GIFT_CARDS_DIR) if f.endswith('_card.webp')]
        png_files = [f for f in os.listdir(GIFT_CARDS_DIR) if f.endswith('.webp') and not f.endswith('_card.webp')]
        # Combine and return all gift card files
        return card_files + png_files
    return []

# Function to get a random gift card
def get_random_gift_card():
    available_cards = get_available_gift_cards()
    if not available_cards:
        return None
    return os.path.join(GIFT_CARDS_DIR, random.choice(available_cards))

# Convert filename to display name
def get_gift_name(filename):
    # Remove _card.webp and replace underscores with spaces
    return os.path.splitext(filename)[0].replace('_card', '').replace('_', ' ')

# Enhanced function to find matching gifts with smart context detection
def find_matching_gifts(query):
    # Ignore extremely short queries to avoid false matches
    if len(query.strip()) < 2:
        return []
        
    query = query.lower().replace('-', ' ').replace("'", '')
    matching_gifts = []
    
    # Skip common phrases
    common_phrases = [
        "thank you", "hello there", "how are you", "what's up", 
        "good morning", "good evening", "good night", "see you later"
    ]
    
    if any(phrase in query for phrase in common_phrases):
        return []
    
    # Gift groups for disambiguation
    gift_groups = {
        "ring": ["Diamond Ring", "Bonded Ring", "Signet Ring"],
        "hat": ["Jester Hat", "Santa Hat", "Top Hat", "Witch Hat", "Durov's Cap"],
        "heart": ["Heart Locket", "Cookie Heart", "Trapped Heart"],
        "candle": ["B-Day Candle", "Eternal Candle", "Love Candle"],
        "snake": ["Pet Snake", "Lunar Snake", "Snake Box"],
        "box": ["Berry Box", "Snake Box", "Loot Bag"],
        "bunny": ["Bunny Muffin", "Jelly Bunny"],
        "signet": ["Gem Signet", "Signet Ring"],
        "bell": ["Jingle Bells", "Sleigh Bell"],
        "pad": ["Star Notepad"],
        "pepe": ["Plush Pepe"],
        "peach": ["Precious Peach"],
        "plush": ["Plush Pepe"]
    }
    
    # Check if query exactly matches a gift group
    if query.lower() in gift_groups:
        return gift_groups[query.lower()]  # Return the whole group for disambiguation
    
    # Check for exact matches in simplified names first
    if query in simplified_names:
        matching_gifts.append(simplified_names[query])
        return matching_gifts
    
    # First try exact gift name matches (case insensitive)
    for simple_name, original_name in simplified_names.items():
        if query == simple_name:
            if original_name not in matching_gifts:
                matching_gifts.append(original_name)
            return matching_gifts  # Return immediately for exact matches
    
    # Special prioritized partial matches (more accurate)
    special_matches = {
        "pepe": "Plush Pepe",
        "peach": "Precious Peach",
        "plush": "Plush Pepe",
        "precious": "Precious Peach",
        "pad": "Star Notepad",
        "notepad": "Star Notepad",
        "gadget": "Tama Gadget",
        "tama": "Tama Gadget",
        "diamond": "Diamond Ring",
        "locket": "Heart Locket",
        "jack": "Jack-in-the-Box",
        "durov": "Durov's Cap",
        "cap": "Durov's Cap"
    }
    
    # Check for special partial matches
    for keyword, gift in special_matches.items():
        if query == keyword or (len(query) >= 3 and keyword.startswith(query)):
            if gift not in matching_gifts:
                matching_gifts.append(gift)
    
    # If we found special matches, return them first
    if matching_gifts:
        return matching_gifts
    
    # Then try partial word matching
    for simple_name, original_name in simplified_names.items():
        # Skip if we already have this gift in our matches
        if original_name in matching_gifts:
            continue
            
        # Check if query is contained in the gift name
        if query in simple_name.lower():
            if original_name not in matching_gifts:
                matching_gifts.append(original_name)
    
    # If still no matches, try fuzzy matching with a moderate threshold
    if not matching_gifts and len(query) >= 3:
        # Get all simplified names as a list
        all_simple_names = list(simplified_names.keys())
        
        # Find close matches
        close_matches = get_close_matches(query, all_simple_names, n=3, cutoff=0.75)
        
        # Add the corresponding original names
        for match in close_matches:
            if match in simplified_names and simplified_names[match] not in matching_gifts:
                matching_gifts.append(simplified_names[match])
    
    # Remove any duplicates and limit to 5 results to avoid overwhelming the user
    return list(dict.fromkeys(matching_gifts))[:5]

# Create a keyboard with gift categories
def get_category_keyboard():
    categories = [
        "Popular", "Holiday", "Seasonal", "Decorative", "Toys", 
        "Magical", "Food", "Accessories", "+Premarket", "View All"
    ]
    
    keyboard = []
    row = []
    for i, category in enumerate(categories):
        row.append(InlineKeyboardButton(category, callback_data=f"category_{category}"))
        
        # Create rows with 3 buttons each
        if (i + 1) % 3 == 0 or i == len(categories) - 1:
            keyboard.append(row)
            row = []
    
    # Add a "Random" button
    keyboard.append([InlineKeyboardButton("🎲 Random Gift", callback_data="random_gift")])
    
    return InlineKeyboardMarkup(keyboard)

# Create a keyboard with gifts from a specific category or paginated gifts
def get_gift_keyboard(category=None, page=0):
    # Filter gifts by category if provided
    if category and category != "View All":
        # Define which gifts belong to which category (simplified)
        category_mapping = {
            "Popular": ["Plush Pepe", "Diamond Ring", "Heart Locket", "Eternal Rose", "Durov's Cap"],
            "Holiday": ["Christmas Hat", "Xmas Stocking", "Santa Hat", "Candy Cane", "Winter Wreath"],
            "Seasonal": ["Easter Egg", "Bunny Muffin", "Halloween Pumpkin", "Valentine Heart"],
            "Decorative": ["Snow Globe", "Hanging Star", "Eternal Candle", "Crystal Ball"],
            "Toys": ["Jack-in-the-Box", "Toy Bear", "Loot Bag", "Tama Gadget"],
            "Magical": ["Magic Potion", "Love Potion", "Genie Lamp", "Witch Hat"],
            "Food": ["Ginger Cookie", "Spiced Wine", "Cookie Heart", "Berry Box"],
            "Accessories": ["Top Hat", "Bow Tie", "Swiss Watch", "Signet Ring"],
            "+Premarket": ["1 May", "Backpack", "Bird Mark", "Book", "Case", "Coconut Drink", "Coffin",
                          "Cone IceCream", "Cream IceCream", "Durov Glasses", "Durov's Statuette", "Eagle",
                          "Easter Cake", "Eight Roses", "Golden Medal", "Grave", "Heart Pendant", "Lamp Candle",
                          "Mask", "Pencil", "Pink Flamingo", "REDO", "Red Star", "Sand Castle", "Sneakers",
                          "Statue", "Surfboard", "T-shirt", "Torch"]
        }
        
        # Get gifts for this category
        filtered_gifts = [name for name in names if any(name.lower() in gift.lower() or gift.lower() in name.lower() 
                                                     for gift in category_mapping.get(category, []))]
    else:
        # Use all gifts
        filtered_gifts = names
    
    # Paginate gifts (8 per page)
    items_per_page = 8
    total_pages = (len(filtered_gifts) + items_per_page - 1) // items_per_page
    
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(filtered_gifts))
    page_gifts = filtered_gifts[start_idx:end_idx]
    
    # Create buttons for each gift
    keyboard = []
    row = []
    for i, gift_name in enumerate(page_gifts):
        # Sanitize callback data to avoid Telegram callback data errors
        sanitized_name = sanitize_callback_data(gift_name)
        row.append(InlineKeyboardButton(gift_name, callback_data=f"gift_{sanitized_name}"))
        
        # Create rows with 2 buttons each
        if i % 2 == 1 or i == len(page_gifts) - 1:
            keyboard.append(row)
            row = []
    
    # Add navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{page-1}_{category}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}_{category}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Add a back button to categories
    keyboard.append([InlineKeyboardButton("🔙 Back to Categories", callback_data="back_to_categories")])
    
    return InlineKeyboardMarkup(keyboard)

# Generate a timestamped card for refresh functionality
def generate_timestamped_card(gift_file_name):
    try:
        # Convert file_name to display name for the card generator
        gift_display_name = gift_file_name.replace("_", " ")
        
        # Normalize the filename for file system compatibility
        # First, fix specific problematic gift names
        if gift_file_name == "Jack-in-the-Box":
            normalized_filename = "Jack_in_the_Box"
        elif gift_file_name == "Durov's Cap":
            normalized_filename = "Durovs_Cap"
        else:
            # General normalization for other names
            normalized_filename = gift_file_name.replace("-", "_").replace("'", "")
        
        # Generate with timestamp suffix to ensure it's fresh
        import gift_card_generator
        timestamp = int(time.time())
        output_path = gift_card_generator.generate_specific_gift(gift_display_name, f"_{timestamp}")
        
        return output_path
    except Exception as e:
        logging.error(f"Error generating timestamped card for {gift_file_name}: {e}")
        return None

# Function to generate a price card for a gift with refresh option
async def generate_gift_price_card(gift_file_name, refresh=False):
    """Generate a price card for a gift with option to refresh."""
    if refresh:
        # Generate with timestamp to ensure it's fresh
        return generate_timestamped_card(gift_file_name)
    else:
        # Use standard generation
        return generate_gift_card(gift_file_name)

# Function to refresh a price card
async def refresh_price_card(update: Update, context: ContextTypes.DEFAULT_TYPE, gift_name):
    """Refresh a price card with latest data."""
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    
    # Generate fresh card and update the message
    await send_gift_card(update, context, gift_name, edit_message_id=message_id, chat_id=chat_id)



# Function to generate gift card with buttons
async def send_gift_card(update: Update, context: ContextTypes.DEFAULT_TYPE, gift_name, edit_message_id=None, chat_id=None):
    from premium_system import premium_system
    is_premium = premium_system.is_group_premium(chat_id or update.effective_chat.id)
    links = premium_system.get_premium_links(chat_id or update.effective_chat.id) if is_premium else None
    mrkt_link = links.get('mrkt_link') if links else DEFAULT_MRKT_LINK
    tonnel_link = links.get('tonnel_link') if links else DEFAULT_TONNEL_LINK
    portal_link = links.get('portal_link') if links else DEFAULT_PORTAL_LINK
    palace_link = links.get('palace_link') if links else DEFAULT_PALACE_LINK
    reply_markup = get_gift_price_card_keyboard(is_premium, mrkt_link, tonnel_link, portal_link, palace_link, update.effective_user.id)

    logger.info(f"Attempting to send gift card for: {gift_name}")
    card_path = generate_gift_card(gift_name)
    logger.info(f"Card path returned for {gift_name}: {card_path}")
    
    if card_path and os.path.exists(card_path):
        logger.info(f"Card exists and will be sent: {card_path}")
        # Create caption based on premium status
        if is_premium:
            # Premium groups: show gift name + pro tip
            caption = f"{gift_name}\n\nJoin @The01Studio\nTry @CollectibleKITbot"
        else:
            # Non-premium groups: show gift name + promotional text + sticker promotion
            caption = f"{gift_name}\n\nJoin @The01Studio\nTry @CollectibleKITbot"
        
        sent_message = await update.message.reply_photo(
            photo=open(card_path, 'rb'),
            caption=caption,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        # Register the message owner in the database for delete permission tracking
        try:
            from rate_limiter import register_message
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            register_message(user_id, chat_id, sent_message.message_id)
            logging.info(f"Registered message {sent_message.message_id} to user {user_id}")
        except ImportError:
            logging.warning("Rate limiter not available, message ownership not registered")
        except Exception as e:
            logging.error(f"Error registering message ownership: {e}")
    else:
        logger.error(f"Card not found or could not be generated for {gift_name}")
        await update.message.reply_text(f"Sorry, could not find the card for {gift_name}.")

# Command handler for /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    # TIMESTAMP FILTERING: Ignore commands older than 5 minutes
    if is_message_too_old(update):
        return
        
    # Get user and chat info for rate limiting
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Apply rate limiting for start command
    try:
        from rate_limiter import can_user_use_command
        can_use, seconds_remaining = can_user_use_command(user_id, chat_id, "start")
        
        if not can_use:
            # User is rate limited for this command
            if update.effective_chat.type == "private":
                # Only notify in private chats to avoid spam
                await update.message.reply_text(f"⏰ Please wait {seconds_remaining} seconds before using /start again.")
            return
    except ImportError:
        # Rate limiter not available, continue without rate limiting
        logger.warning("Rate limiter not available, continuing without rate limiting")
    
    user = update.effective_user
    
    # Get script directory for cross-platform compatibility
    video_path = os.path.join(ASSETS_DIR, "start.mp4")
    
    welcome_text = (
        f"Hi {user.first_name}! I'm the Telegram Gift Price Bot. ✨\n\n"
        "I can show you price cards for Telegram gifts with modern cool chart photos. 📊\n\n"
        "Add @giftsChartBot to your public/private group - no admin privileges needed! Just type any gift name in the chat and have fun! 🎁"
    )
    
    # Create keyboard with help button only
    keyboard = [
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Send video with caption and keyboard
        with open(video_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=welcome_text,
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        # Fallback to text only if video not found
        logger.warning(f"Video file not found at {video_path}, sending text only")
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    except Exception as e:
        # Fallback to text only if any error occurs
        logger.error(f"Error sending video: {e}, sending text only")
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# Command handler for /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    # Get user and chat info for rate limiting
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Apply rate limiting for help command
    try:
        from rate_limiter import can_user_use_command
        can_use, seconds_remaining = can_user_use_command(user_id, chat_id, "help")
        
        if not can_use:
            # User is rate limited for this command
            if update.effective_chat.type == "private":
                # Only notify in private chats to avoid spam
                await update.message.reply_text(f"⏰ Please wait {seconds_remaining} seconds before using /help again.")
            return
    except ImportError:
        # Rate limiter not available, continue without rate limiting
        logger.warning("Rate limiter not available, continuing without rate limiting")
    
    # Show first page by default
    await show_help_page(update, context, page=1)

async def show_help_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1) -> None:
    """Show a specific page of the help guide."""
    
    if page == 1:
        # Page 1: What the bot provides
        help_text = (
            "*Gifts Chart Guide*\n"
            "📖 *Page 1 of 3*\n\n"
            "*What the bot provides:*\n"
            "• All gift prices (86+) using Portal API for market prices\n"
            "• *Pre-market* prices powered by Tonnel\n"
            "• *++Pre-market* gifts monitoring and alerts\n"
            "• *Goodies* collections real-time price tracking\n\n"
        )
        
        # Add sticker info if available
        try:
            import sticker_integration
            if sticker_integration.is_sticker_functionality_available():
                help_text += "• All the sticker prices (159 of them) in a beautiful card using stickers.tools API\n\n"
        except ImportError:
            pass
        
        help_text += "• You can use the bot in inline or normal mode\n\n"
        help_text += "📄 *Next page: How to use the bot*"
        
        keyboard = [
            [InlineKeyboardButton("➡️ Next Page", callback_data="help_page_2")]
        ]
        
    elif page == 2:
        # Page 2: How to use
        help_text = (
            "*Gifts Chart Guide*\n"
            "📖 *Page 2 of 3*\n\n"
            "📱 *How to use:*\n"
            "You have three ways:\n\n"
            "First, add the bot @giftschartbot to your group of choice (no admin privileges needed)\n\n"
            "1️⃣ Send a message in the group chat like @giftschartbot tama or pepe and the bot will answer you\n\n"
            "2️⃣ For sticker prices, you need to type /sticker\n\n"
            "3️⃣ You can use the inline mode as: @giftschartbot term collection/gift\n\n"
            "*Examples:*\n"
            "• @giftschartbot gift pepe\n"
            "• @giftschartbot sticker blue pengu\n"
            "• @giftschartbot goodies\n\n"
            "📄 *Next page: All available commands*"
        )
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Previous Page", callback_data="help_page_1")],
            [InlineKeyboardButton("➡️ Next Page", callback_data="help_page_3")]
        ]
        
    elif page == 3:
        # Page 3: Commands
        help_text = (
            "*Gifts Chart Guide*\n"
            "📖 *Page 3 of 3*\n\n"
            "👨‍💻 *All Commands:*\n"
            "/start - Welcome message\n"
            "/help - This help guide\n"
            "/sticker - Browse all sticker collections\n"
            "/premium - Get premium subscription\n"
            "/devs - About the developers\n"
            "/terms - Terms of service and policies\n"
            "/refund - Refund policy information\n\n"
            "💡 *Pro Tips:*\n"
            "• Use inline mode to share prices in any chat\n"
            "• Search by collection name or specific sticker\n"
            "• Results show current prices and market links\n\n"
            "📄 *Previous page: How to use the bot*"
        )
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Previous Page", callback_data="help_page_2")],
            [InlineKeyboardButton("🏠 Back to Start", callback_data="help_page_1")]
        ]
    
    else:
        # Invalid page, show page 1
        await show_help_page(update, context, page=1)
        return
    
    # Create keyboard markup
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit the message with image
    # Use the configured help image path
    help_image_path = HELP_IMAGE_PATH
    
    if update.callback_query:
        # Edit existing message for pagination
        try:
            # Try to edit with photo first
            with open(help_image_path, 'rb') as photo:
                await update.callback_query.edit_message_media(
                    media=InputMediaPhoto(
                        media=photo,
                        caption=help_text,
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    reply_markup=reply_markup
                )
        except FileNotFoundError:
            # Fallback to text-only if image not found
            await update.callback_query.edit_message_text(
                help_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error editing message with image: {e}")
            # Fallback to text-only
            await update.callback_query.edit_message_text(
                help_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
        await update.callback_query.answer()
    elif update.message:
        # Send new message with image
        try:
            with open(help_image_path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=help_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        except FileNotFoundError:
            # Fallback to text-only if image not found
            await update.message.reply_text(
                help_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error sending message with image: {e}")
            # Fallback to text-only
            await update.message.reply_text(
                help_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )

# Command handler for /devs
async def devs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send information about the developers when the command /devs is issued."""
    # Get user and chat info for rate limiting
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Apply rate limiting for devs command
    try:
        from rate_limiter import can_user_use_command
        can_use, seconds_remaining = can_user_use_command(user_id, chat_id, "devs")
        
        if not can_use:
            # User is rate limited for this command
            if update.effective_chat.type == "private":
                # Only notify in private chats to avoid spam
                await update.message.reply_text(f"⏰ Please wait {seconds_remaining} seconds before using /devs again.")
            return
    except ImportError:
        # Rate limiter not available, continue without rate limiting
        logger.warning("Rate limiter not available, continuing without rate limiting")
    
    # Get the path to the devs image
    devs_image_path = os.path.join(ASSETS_DIR, "devs.jpg")
    
    # Check if the image exists
    if os.path.exists(devs_image_path):
        try:
            # Send the image with caption
            await update.message.reply_photo(
                photo=open(devs_image_path, 'rb'),
                caption=(
                    "👨‍💻 Developers of GiftsChart\n"
                    "Crafted by the GiftCharts team — fueled by coffee ☕️\n\n"
                    "• Lead Developer: @GiftsChart_Support\n"
                    "• Portal api thanks to @giftsdevs ❤️\n"
                    "• Sticker api thanks to @stickers_tools ❤️\n\n"
                    "💬 Need help, new features, or anything else?\n"
                    "Don't hesitate to contact us !"
                ),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error sending devs image: {e}")
            # Fallback to text-only if image fails
            await update.message.reply_text(
                "👨‍💻 Developers of GiftsChart\n"
                "Crafted by the GiftCharts team — fueled by coffee ☕️\n\n"
                "• Lead Developer: @GiftsChart_Support\n"
                "• Portal api thanks to @giftsdevs ❤️\n"
                "• Sticker api thanks to @stickers_tools ❤️\n\n"
                "💬 Need help, new features, or anything else?\n"
                "Don't hesitate to contact us !",
                parse_mode=ParseMode.HTML
            )
    else:
        # Image not found, send text-only
        logger.warning(f"Devs image not found at: {devs_image_path}")
        await update.message.reply_text(
            "👨‍💻 Developers of GiftsChart\n"
            "Crafted by the GiftCharts team — fueled by coffee ☕️\n\n"
            "• Lead Developer: @GiftsChart_Support\n"
            "• Portal api thanks to @giftsdevs ❤️\n"
            "• Sticker api thanks to @stickers_tools ❤️\n\n"
            "💬 Need help, new features, or anything else?\n"
            "Don't hesitate to contact us !",
            parse_mode=ParseMode.HTML
        )

# Command handler for /premium
async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /premium command for premium subscriptions with admin/owner checks."""
    # Check if user is in private chat (required for payment)
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "💫 Premium subscriptions can only be purchased in private chat.\n"
            "Please message me privately to continue."
        )
        return
    
    # Import premium system
    try:
        from premium_system import handle_premium_button
        PREMIUM_AVAILABLE = True
    except ImportError:
        PREMIUM_AVAILABLE = False
        logger.warning("Premium system not available")
    
    if not PREMIUM_AVAILABLE:
        await update.message.reply_text(
            "❌ Premium system is not available at the moment.\n"
            "Please try again later."
        )
        return
    
    # Create a mock update with .message for direct command
    class MockUpdate:
        def __init__(self, message, user):
            self.callback_query = None  # No callback query for direct command
            self.effective_chat = message.chat
            self.effective_user = user
            self.message = message  # Add .message for compatibility
    
    # Call the premium button handler which will handle the payment flow
    mock_update = MockUpdate(update.message, update.effective_user)
    await handle_premium_button(mock_update, context)

# Command handler for /cancel_premium
async def cancel_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /cancel_premium command to cancel premium setup."""
    # Check if user is in private chat (required for premium operations)
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "💫 Premium operations can only be performed in private chat.\n"
            "Please message me privately to continue."
        )
        return
    
    # Clear premium setup data
    if 'premium_setup_step' in context.user_data:
        context.user_data.clear()
        await update.message.reply_text(
            "✅ Premium setup cancelled. You can start again with /premium anytime."
        )
    elif 'configure_step' in context.user_data:
        context.user_data.clear()
        await update.message.reply_text(
            "✅ Configuration cancelled. You can start again with /configure anytime."
        )
    else:
        await update.message.reply_text(
            "No premium setup or configuration in progress."
    )

# Command handler for /terms
async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /terms command to show terms of service."""
    terms_text = (
        "📋 **GiftsChart Terms of Service & Policies**\n\n"
        "📄 **Full Terms Document**: https://telegra.ph/GiftsChart-07-06"
    )
    
    # Send photo with terms text
    photo_path = os.path.join(ASSETS_DIR, "terms.webp")
    if os.path.exists(photo_path):
        await update.message.reply_photo(
            photo=open(photo_path, 'rb'),
            caption=terms_text,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Fallback to text only if image not found
        await update.message.reply_text(
            terms_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )

# Command handler for /refund
async def refund_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /refund command to show refund information and process refunds."""
    # Check if user is in private chat (for privacy)
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "🔒 For privacy, please use /refund in a private chat with me."
        )
        return
    
    user_id = update.effective_user.id
        
    # Check if user has any premium groups
    try:
        import premium_system
        user_groups = premium_system.premium_system.get_user_premium_groups(user_id)
        
        if not user_groups:
            await update.message.reply_text(
                "❌ You do not have an active premium subscription for any group.\n"
                "To request a refund, you must first purchase premium.\n"
                "Use the Premium button or /premium to get started."
            )
            return
        
        # User has premium groups, show refund options
        refund_text = (
            "💰 **GiftsChart Refund System**\n\n"
            "You have active premium subscriptions. Here are your options:\n\n"
        )
        
        # Check refund eligibility for each group
        refundable_groups = []
        non_refundable_groups = []
        
        for group in user_groups:
            eligibility = premium_system.premium_system.can_request_refund(user_id, group['group_id'])
            if eligibility["can_refund"]:
                refundable_groups.append({
                    "group_id": group['group_id'],
                    "days_remaining": eligibility["days_remaining"]
                })
            else:
                non_refundable_groups.append({
                    "group_id": group['group_id'],
                    "reason": eligibility["reason"]
                })
        
        if refundable_groups:
            refund_text += "✅ **Groups Eligible for Refund:**\n"
            for group in refundable_groups:
                refund_text += f"• Group ID: {group['group_id']} ({group['days_remaining']} days remaining)\n"
            
            # Create refund buttons
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = []
            for group in refundable_groups:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🔄 Request Refund (Group {group['group_id']})",
                        callback_data=f"refund_request:{group['group_id']}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("📋 View Refund Policy", callback_data="refund_policy")])
            keyboard.append([InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            refund_text += "\nClick the button below to request a refund for any eligible group."
            
            # Send photo with refund text
            photo_path = os.path.join(ASSETS_DIR, "refund.webp")
            if os.path.exists(photo_path):
                await update.message.reply_photo(
                    photo=open(photo_path, 'rb'),
                    caption=refund_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                # Fallback to text only if image not found
                await update.message.reply_text(
                    refund_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        else:
            refund_text += "❌ **No Groups Eligible for Refund:**\n"
            for group in non_refundable_groups:
                refund_text += f"• Group ID: {group['group_id']}: {group['reason']}\n"
            
            refund_text += "\n📞 **Contact Support**: @GiftsChart_Support for assistance."
            
            # Send photo with refund text
            photo_path = os.path.join(ASSETS_DIR, "refund.webp")
            if os.path.exists(photo_path):
                await update.message.reply_photo(
                    photo=open(photo_path, 'rb'),
                    caption=refund_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Fallback to text only if image not found
                await update.message.reply_text(
                    refund_text,
                    parse_mode=ParseMode.MARKDOWN
                )
    except ImportError:
        # Fallback to basic refund info if premium system not available
        refund_text = (
            "💰 **GiftsChart Refund Policy**\n\n"
            "**Refund Eligibility:**\n"
            "• Only the original purchaser can request refunds\n"
            "• Refund window: 3 days from purchase date\n"
            "• Each group can only be refunded once\n"
            "• Groups that have been refunded cannot be refunded again\n\n"
            "**Refund Process:**\n"
            "• Full refund of 99 Telegram Stars\n"
            "• Processed within 24 hours\n"
            "• Warning system for previously refunded groups\n\n"
            "**How to Request a Refund:**\n"
                            "1. Contact @GiftsChart_Support directly\n"
            "2. Provide your group ID and purchase details\n"
            "3. Explain the reason for refund\n"
            "4. Wait for confirmation and processing\n\n"
            "**Important Notes:**\n"
            "• Refunds are final and cannot be reversed\n"
            "• Premium features will be disabled immediately\n"
            "• Custom referral links will be reset to defaults\n\n"
            "📄 **Full Terms**: https://telegra.ph/GiftsChart-07-06\n"
                            "📞 **Support**: @GiftsChart_Support"
        )
        
        await update.message.reply_text(
            refund_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error in refund command: {e}")
        await update.message.reply_text(
            "❌ Error processing refund request. Please contact @GiftsChart_Support for assistance."
        )

# Refund callback handler
async def handle_refund_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle refund-related callback queries."""
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    
    try:
        await query.answer()
        
        if data == "refund_policy":
            # Show refund policy
            policy_text = (
                "💰 **GiftsChart Refund Policy**\n\n"
                "**Refund Eligibility:**\n"
                "• Only the original purchaser can request refunds\n"
                "• Refund window: 3 days from purchase date\n"
                "• Each group can only be refunded once\n"
                "• Groups that have been refunded cannot be refunded again\n\n"
                "**Refund Process:**\n"
                "• Full refund of 99 Telegram Stars\n"
                "• Processed within 24 hours\n"
                "• Warning system for previously refunded groups\n\n"
                "📄 **Full Terms**: https://telegra.ph/GiftsChart-07-06\n"
                "📞 **Support**: @GiftsChart_Support"
            )
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=policy_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            return
        
        elif data == "contact_support":
            # Show contact information
            support_text = (
                "📞 **Contact Support**\n\n"
                "For refund requests and assistance:\n\n"
                "**Telegram:** @GiftsChart_Support\n"
                "**Response Time:** Within 24 hours\n\n"
                "Please provide:\n"
                "• Your group ID\n"
                "• Purchase details\n"
                "• Reason for refund\n\n"
                "We'll process your request as quickly as possible!"
            )
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=support_text,
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        elif data.startswith("refund_request:"):
            # Handle refund request
            group_id = int(data.split(":")[1])
            
            # Check if user is in private chat
            if update.effective_chat.type != "private":
                await query.message.edit_text(
                    "🔒 Refund requests can only be processed in private chat for security."
                )
                return
            
            # Check refund eligibility
            import premium_system
            eligibility = premium_system.premium_system.can_request_refund(user_id, group_id)
            
            if not eligibility["can_refund"]:
                await query.message.edit_text(
                    f"❌ **Refund Not Eligible**\n\n"
                    f"**Reason:** {eligibility['reason']}\n\n"
                    f"📞 Contact @GiftsChart_Support for assistance."
                )
                return
            
            # Request the refund and process it immediately
            refund_result = premium_system.premium_system.request_refund(user_id, group_id)
            
            if refund_result["success"]:
                # Process the refund immediately through Telegram API
                try:
                    # Get the payment details for the refund
                    import premium_system
                    payment_details = premium_system.premium_system.get_payment_details_for_refund(refund_result["refund_id"])
                    
                    if payment_details and payment_details.get("telegram_payment_charge_id"):
                        # Process the Telegram Stars refund immediately
                        # According to Telegram API: refundStarPayment can only be called for payments made via Stars
                        # and only within 24 hours after the payment was made
                        await context.bot.refund_star_payment(
                            user_id=user_id,
                            telegram_payment_charge_id=payment_details["telegram_payment_charge_id"]
                        )
                        
                        # Mark refund as processed in our system
                        process_result = premium_system.premium_system.process_refund(refund_result["refund_id"], "auto_processed")
                        
                        if process_result["success"]:
                            success_text = (
                                f"✅ **Refund Processed Successfully**\n\n"
                                f"**Group ID:** {group_id}\n"
                                f"**Stars Amount:** {refund_result['stars_amount']}\n"
                                f"**Status:** Refunded immediately\n\n"
                                f"Your Telegram Stars have been refunded to your account.\n"
                                f"Premium features for this group have been disabled.\n\n"
                                f"📞 **Support:** @GiftsChart_Support\n"
                                f"📄 **Terms:** https://telegra.ph/GiftsChart-07-06"
                            )
                        else:
                            success_text = (
                                f"⚠️ **Refund Partially Processed**\n\n"
                                f"**Group ID:** {group_id}\n"
                                f"**Stars Amount:** {refund_result['stars_amount']}\n"
                                f"**Status:** Stars refunded, but system update failed\n\n"
                                f"Your Telegram Stars have been refunded, but there was an issue updating our system.\n"
                                f"Please contact support if premium features are still active.\n\n"
                                f"📞 **Support:** @GiftsChart_Support"
                            )
                    else:
                        # Fallback if payment details not found
                        success_text = (
                            f"❌ **Refund Processing Error**\n\n"
                            f"**Group ID:** {group_id}\n"
                            f"**Error:** Payment details not found or invalid\n\n"
                            f"Please contact support for manual processing.\n\n"
                            f"📞 **Support:** @GiftsChart_Support"
                        )
                        
                except Exception as e:
                    logger.error(f"Error processing Telegram refund: {e}")
                    success_text = (
                        f"⚠️ **Refund Processing Error**\n\n"
                        f"**Group ID:** {group_id}\n"
                        f"**Stars Amount:** {refund_result['stars_amount']}\n"
                        f"**Error:** {str(e)}\n\n"
                        f"Your refund request has been recorded, but there was an error processing the Telegram Stars refund.\n"
                        f"Please contact support for assistance.\n\n"
                        f"📞 **Support:** @GiftsChart_Support"
                    )
                
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=success_text,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
                
                # Log the refund request
                logger.info(f"Refund request submitted by user {user_id} for group {group_id}")
                
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"❌ **Refund Request Failed**\n\n"
                         f"**Error:** {refund_result['reason']}\n\n"
                         f"📞 Contact @GiftsChart_Support for assistance.",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        else:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Invalid refund action. Please try again.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    except Exception as e:
        logger.error(f"Error in refund callback handler: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ Error processing refund request. Please contact @GiftsChart_Support for assistance.",
            parse_mode=ParseMode.MARKDOWN
        )









# Command handler for /sticker
async def sticker_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send sticker collection options when the command /sticker is issued."""
    # Get user and chat info for rate limiting
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Apply rate limiting for sticker command
    try:
        from rate_limiter import can_user_use_command
        can_use, seconds_remaining = can_user_use_command(user_id, chat_id, "sticker")
        
        if not can_use:
            # User is rate limited for this command
            if update.effective_chat.type == "private":
                # Only notify in private chats to avoid spam
                await update.message.reply_text(f"⏰ Please wait {seconds_remaining} seconds before using /sticker again.")
            return
    except ImportError:
        # Rate limiter not available, continue without rate limiting
        logger.warning("Rate limiter not available, continuing without rate limiting")
    
    try:
        import sticker_integration
        if sticker_integration.is_sticker_functionality_available():
            reply_markup = sticker_integration.get_sticker_keyboard()
            sent_message = await update.message.reply_text(
                "🌟 Choose a sticker collection to browse:",
                reply_markup=reply_markup
            )
            
            # Register the message owner in the database for button permission tracking
            try:
                from rate_limiter import register_message
                register_message(user_id, chat_id, sent_message.message_id)
                logger.info(f"Registered sticker collections message {sent_message.message_id} to user {user_id}")
            except ImportError:
                logger.warning("Rate limiter not available, message ownership not registered")
            except Exception as e:
                logger.error(f"Error registering message ownership: {e}")
        else:
            await update.message.reply_text("Sorry, sticker functionality is not available at the moment.")
    except ImportError:
        await update.message.reply_text("Sorry, sticker functionality is not available at the moment.")
    except Exception as e:
        logger.error(f"Error in sticker command: {e}")
        await update.message.reply_text("Sorry, there was an error loading sticker collections.")





# Function to handle inline queries
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the inline queries with improved user experience."""
    query = update.inline_query.query.lower().strip()
    user_id = update.inline_query.from_user.id
    offset = update.inline_query.offset or "0"
    logger.info(f"Received inline query: '{query}' from user {user_id}, offset: {offset}")
    
    # CDN base URL (already defined at top of file)
    
    # Handle empty query - show helpful tips
    if not query:
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="How to use it",
                description="Learn how to use the bot effectively",
                thumbnail_url=create_safe_cdn_url("assets", "giftschart.webp"),
                input_message_content=InputTextMessageContent(
                    message_text="**How to use Gift Price Tracker**\n\nTrack real-time prices of Telegram gifts and stickers!\n\nBrowse gifts: Type 'gift' (includes Pre-market)\nBrowse stickers: Type 'sticker'\nBrowse Goodies: Type 'goodies'\n\n**the flow**\n\n`@TWETestBot gift pepe`\n`@TWETestBot sticker azuki`\n`@TWETestBot goodies`\n\n**Want to support the bot?**\nTON Donation Address:\n`UQCFRqB2vZnGZRh3ZoZAItNidk8zpkN0uRHlhzrnwweU3mos`\n\nOr you can use the Donate button below.\n\n> Every NFT has a price.\n> Know it. Live.",
                    parse_mode=ParseMode.MARKDOWN
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")],
                    [InlineKeyboardButton("Donate", url="https://app.tonkeeper.com/transfer/UQCFRqB2vZnGZRh3ZoZAItNidk8zpkN0uRHlhzrnwweU3mos")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Browse All Gifts",
                description="Type 'gift' to see all 139 gifts (most expensive first)",
                thumbnail_url=create_safe_cdn_url("assets", "gifts.webp"),
                input_message_content=InputTextMessageContent(
                    message_text="**Browse All Gifts**\n\nType 'gift' to see all 139 available gifts with their price cards!\n\n💎 *Most expensive gifts shown first*",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")],
                    [InlineKeyboardButton("Type 'gift' to browse", switch_inline_query_current_chat="gift")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Browse All Stickers",
                description="Type 'sticker' to see all 166 stickers (most expensive first)",
                thumbnail_url=create_safe_cdn_url("assets", "stickers.webp"),
                input_message_content=InputTextMessageContent(
                    message_text="**Browse All Stickers**\n\nType 'sticker' to see all 166 available sticker packs!\n\n💎 *Most expensive stickers shown first*",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")],
                    [InlineKeyboardButton("Type 'sticker' to browse", switch_inline_query_current_chat="sticker")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Browse All Goodies",
                description="Type 'goodies' to see all 21 Goodies collections",
                thumbnail_url=create_safe_cdn_url("assets", "goodies.webp"),
                input_message_content=InputTextMessageContent(
                    message_text="**Browse All Goodies**\n\nType 'goodies' to see all 21 Goodies collections!\n\n🎨 *Premium collectibles from Goodies app*",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")],
                    [InlineKeyboardButton("Type 'goodies' to browse", switch_inline_query_current_chat="goodies")]
                ])
            )
        ]
        await update.inline_query.answer(results, cache_time=0)
        return
        
    # Handle 'gift' query - show all gifts (NO leaderboard entry)
    if query == "gift":
        try:
            logger.info("Processing 'gift' inline query")
            all_gifts = get_available_gift_cards()
            logger.info(f"Found {len(all_gifts)} gift cards")
            
            if not all_gifts:
                logger.warning("No gift cards found in directory")
                results = [
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title="No gifts available",
                        description="No gift cards found",
                        input_message_content=InputTextMessageContent(
                            message_text="No gift cards available at the moment. Please try again later.",
                            parse_mode=ParseMode.HTML
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")]
                        ])
                    )
                ]
                await update.inline_query.answer(results, cache_time=0)
                return
            
            # Load price data to sort by real API prices (similar to stickers)
            import json
            gift_price_file = os.path.join(CACHE_DIR, "gift_price_results.json")
            price_data = {}
            if os.path.exists(gift_price_file):
                try:
                    with open(gift_price_file, 'r') as f:
                        price_json = json.load(f)
                        gifts_with_prices = price_json.get('gifts_with_prices', [])
                        for gift_info in gifts_with_prices:
                            gift_name = gift_info.get('name', '')
                            price = gift_info.get('price', 0)
                            price_data[gift_name.lower()] = price
                    logger.info(f"Loaded price data for {len(price_data)} gifts")
                except Exception as e:
                    logger.warning(f"Error loading gift price data: {e}, will fetch dynamically")
                    price_data = {}
            
            # Prepare gift list with names for sorting
            gift_list = []
            for gift in all_gifts:
                # Extract clean gift name from filename
                if gift.endswith("_card.webp"):
                    clean_gift_name = gift.replace("_card.webp", "").replace("_", " ")
                else:
                    clean_gift_name = gift.replace(".webp", "").replace("_", " ")
                
                # Special handling for B-Day Candle
                if clean_gift_name == "B Day Candle":
                    clean_gift_name = "B-Day Candle"
                
                gift_list.append((gift, clean_gift_name))
            
            # Sort gifts by price (highest first), fallback to alphabetical if no price
            def get_gift_sort_key(gift_tuple):
                gift_file, gift_name = gift_tuple
                price = price_data.get(gift_name.lower(), 0)
                if price > 0:
                    # Return negative price so highest prices come first (reverse sort)
                    return -price
                else:
                    # Fallback to alphabetical order for gifts without prices
                    return gift_name.lower()
            
            gift_list.sort(key=get_gift_sort_key)
            logger.info(f"Sorted {len(gift_list)} gifts by price (highest first), with alphabetical fallback")
            
            results = []
            
            # Implement pagination using offset
            try:
                page_offset = int(offset) if offset.isdigit() else 0
            except (ValueError, AttributeError):
                page_offset = 0
            
            # Show 50 gifts per page
            RESULTS_PER_PAGE = 50
            start_idx = page_offset * RESULTS_PER_PAGE
            end_idx = start_idx + RESULTS_PER_PAGE
            
            # Calculate next offset if there are more results
            next_offset = None
            if end_idx < len(gift_list):
                next_offset = str(page_offset + 1)
            
            logger.info(f"Showing gifts {start_idx} to {end_idx} (page {page_offset}, total: {len(gift_list)})")
            
            # Show gifts for current page
            for gift, clean_gift_name in gift_list[start_idx:end_idx]:
                result_id = str(uuid4())
                
                # clean_gift_name is already extracted in gift_list preparation above
                gift_file_name = normalize_gift_filename(clean_gift_name)
                
                # Create CDN URLs - price card with cache-busting, gift image without cache-busting
                timestamp = int(datetime.datetime.now().timestamp())
                
                # Use the actual filename from the directory for price card
                card_filename = gift
                gift_card_url = create_safe_cdn_url("new_gift_cards", card_filename, "gift") + f"?t={timestamp}"
                
                # Use the gift image from downloaded_images as thumbnail (like stickers do)
                gift_image_url = create_safe_cdn_url("downloaded_images", f"{gift_file_name}.webp", "gift")
                
                # Get price for description if available
                price = price_data.get(clean_gift_name.lower(), 0)
                if price > 0:
                    description = f"${price:,.2f}"
                else:
                    description = "Gift Price Card"
                
                # Use InlineQueryResultArticle like stickers - show gift image as thumbnail, send price card when clicked
                results.append(
                    InlineQueryResultArticle(
                        id=result_id,
                        title=clean_gift_name,
                        description=description,
                        thumbnail_url=gift_image_url,
                        input_message_content=InputTextMessageContent(
                            message_text=f"<a href='{gift_card_url}'> </a><b>{clean_gift_name}</b>",
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=False
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")]
                        ])
                    )
                )
            
            # Count gifts with real prices vs fallback (for current page)
            current_page_gifts = gift_list[start_idx:end_idx]
            with_real_prices = sum(1 for _, name in current_page_gifts if price_data.get(name.lower(), 0) > 0)
            with_fallback = len(current_page_gifts) - with_real_prices
            
            logger.info(f"Sending {len(results)} gift results ({with_real_prices} with real prices, {with_fallback} with alphabetical fallback), next_offset: {next_offset}")
            await update.inline_query.answer(results, cache_time=0, next_offset=next_offset)  # Pagination support
            return
            
        except Exception as e:
            logger.error(f"Error showing all gifts: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Handle 'sticker' query - show all individual stickers
    if query == "sticker":
        try:
            logger.info("Processing 'sticker' inline query")
            import sticker_integration
            if sticker_integration.is_sticker_functionality_available():
                # Get all stickers from all collections
                all_stickers = []
                collections = sticker_integration.get_sticker_collections()
                logger.info(f"Found {len(collections)} sticker collections")
                
                for collection in collections:
                    # Skip dogs_og collection from general sticker query (too many stickers)
                    if collection.lower() == "dogs og":
                        continue
                    
                    # Skip Goodies collections (they have their own dedicated inline query 'goodies')
                    goodies_collections = [
                        'Teddie', 'WSB', 'Lamborghini', 'Cool Cats', 'Oracle Red Bull Racing', 
                        'NOT Wise', 'Moonbirds', 'Pudgy Penguins x Kung Fu Panda', 'Doodles'
                    ]
                    if collection in goodies_collections:
                        continue
                    stickers = sticker_integration.get_stickers_in_collection(collection)
                    for sticker in stickers:
                        all_stickers.append((collection, sticker))
                
                logger.info(f"Found {len(all_stickers)} total stickers")
                
                # Load price data to sort by real API prices
                import json
                sticker_price_file = os.path.join(CACHE_DIR, "sticker_price_results.json")
                price_data = {}
                if os.path.exists(sticker_price_file):
                    try:
                        with open(sticker_price_file, 'r') as f:
                            price_json = json.load(f)
                            stickers_with_prices = price_json.get('stickers_with_prices', [])
                            for sticker_info in stickers_with_prices:
                                collection = sticker_info.get('collection', '')
                                sticker = sticker_info.get('sticker', '')
                                price = sticker_info.get('price', 0)
                                key = (collection.lower(), sticker.lower())
                                price_data[key] = price
                        logger.info(f"Loaded price data for {len(price_data)} stickers")
                    except Exception as e:
                        logger.warning(f"Error loading price data: {e}, using priority system")
                        price_data = {}
                
                # Sort stickers by real API price (highest first), fallback to priority if no price
                def get_sticker_sort_key(sticker_tuple):
                    collection, sticker = sticker_tuple
                    key = (collection.lower(), sticker.lower())
                    price = price_data.get(key, 0)
                    if price > 0:
                        # Return negative price so highest prices come first (reverse sort)
                        return -price
                    else:
                        # Fallback to priority system for stickers without prices
                        return get_high_value_sticker_priority(collection, sticker) + 10000
                
                all_stickers.sort(key=get_sticker_sort_key)
                logger.info("Sorted stickers by real API prices (highest first), with priority fallback")
                
                if not all_stickers:
                    logger.warning("No stickers found")
                    results = [
                        InlineQueryResultArticle(
                            id=str(uuid4()),
                            title="No stickers available",
                            description="No sticker cards found",
                            input_message_content=InputTextMessageContent(
                                message_text="❌ No sticker cards available at the moment. Please try again later.",
                                parse_mode=ParseMode.HTML
                            ),
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")]
                            ])
                        )
                    ]
                    await update.inline_query.answer(results, cache_time=0)
                    return
                
                results = []
                
                # Filter out Blum collection
                all_stickers_filtered = [s for s in all_stickers if s[0].lower() != 'blum']
                
                # Implement pagination using offset
                try:
                    page_offset = int(offset) if offset.isdigit() else 0
                except (ValueError, AttributeError):
                    page_offset = 0
                
                # Show 50 stickers per page
                RESULTS_PER_PAGE = 50
                start_idx = page_offset * RESULTS_PER_PAGE
                end_idx = start_idx + RESULTS_PER_PAGE
                
                # Calculate next offset if there are more results
                next_offset = None
                if end_idx < len(all_stickers_filtered):
                    next_offset = str(page_offset + 1)
                
                logger.info(f"Showing stickers {start_idx} to {end_idx} (page {page_offset}, total: {len(all_stickers_filtered)})")
                
                stickers_to_show = all_stickers_filtered[start_idx:end_idx]
                
                # Count stickers with real prices vs fallback
                with_real_prices = sum(1 for s in stickers_to_show if price_data.get((s[0].lower(), s[1].lower()), 0) > 0)
                with_fallback = len(stickers_to_show) - with_real_prices
                
                logger.info(f"Showing {len(stickers_to_show)} stickers ({with_real_prices} with real prices, {with_fallback} with fallback priority, Blum excluded)")
                
                for collection, sticker in stickers_to_show:
                    result_id = str(uuid4())
                    
                    # Normalize names for CDN URL using the proper normalization function
                    collection_normalized = normalize_cdn_path(collection, "collection")
                    sticker_normalized = normalize_cdn_path(sticker, "sticker")
                    
                    # Create CDN URLs - price card with cache-busting, thumbnail without cache-busting
                    timestamp = int(datetime.datetime.now().timestamp())
                    sticker_card_filename = f"{collection_normalized}_{sticker_normalized}_price_card.webp"
                    sticker_card_url = create_safe_cdn_url("sticker_price_cards", sticker_card_filename) + f"?t={timestamp}"
                    image_number = get_sticker_image_number(collection, sticker)
                    collection_path = normalize_cdn_path(collection, "collection")
                    sticker_path = normalize_cdn_path(sticker, "sticker")
                    sticker_image_url = f"{CDN_BASE_URL}/sticker_collections/{quote(collection_path)}/{quote(sticker_path)}/{quote(image_number)}"
                    
                    # Format names for display (convert snake_case to Title Case)
                    collection_display = format_display_name(collection)
                    sticker_display = format_display_name(sticker)
                    title = f"{collection_display} - {sticker_display}"
                    
                    results.append(
                        InlineQueryResultArticle(
                            id=result_id,
                            title=title,
                            description=f"Sticker Price Card",
                            thumbnail_url=sticker_image_url,
                            input_message_content=InputTextMessageContent(
                                message_text=f"<a href='{sticker_card_url}'> </a><b>{collection_display} - {sticker_display}</b>",
                                parse_mode=ParseMode.HTML,
                                disable_web_page_preview=False
                            ),
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")]
                            ])
                        )
                    )
                
                logger.info(f"Sending {len(results)} sticker results for inline query, next_offset: {next_offset}")
                await update.inline_query.answer(results, cache_time=0, next_offset=next_offset)  # Pagination support
                return
            else:
                logger.warning("Sticker functionality not available")
                
        except Exception as e:
            logger.error(f"Error showing all stickers: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Handle 'goodies' query - show all Goodies stickers
    if query == "goodies" or query.startswith("goodies"):
        try:
            logger.info("Processing 'goodies' inline query")
            
            # Goodies stickers with their prices (complete list from stickers.tools)
            GOODIES_STICKERS = [
                # Teddie (3)
                ('teddie', 'teddie_goodies_intern', 245),
                ('teddie', 'teddie_nakamoto', 303.8),
                ('teddie', 'teddie_xmas', 313.9),
                # Goodies Blindbox (8)
                ('goodies_blindbox', 'teddie_s_goodies', 999),
                ('goodies_blindbox', 'conviction_or_capitulation', 90),
                ('goodies_blindbox', 'box_box_boxie', 34.5),
                ('goodies_blindbox', 'be_cool', 20),
                ('goodies_blindbox', 'origin_of_the_birb', 20),
                ('goodies_blindbox', 'monsters_unleashed_icons_of_horror', 11.8),
                ('goodies_blindbox', 'masters_drop', 11),
                ('goodies_blindbox', 'lamborghini', 11),
                # Oracle Red Bull Racing (3)
                ('oracle_red_bull_racing', 'boxie_pitwall', 11.3),
                ('oracle_red_bull_racing', 'boxie_racer', 23),
                ('oracle_red_bull_racing', 'boxie_feels', 85),
                # NOT Wise (1)
                ('not_wise', 'not_wise_stonks_x_goodies', 15.6),
                # WSB (2)
                ('wsb', 'paper_hands', 8.5),
                ('wsb', 'diamond_hands', 21.5),
                # Cool Cats (2)
                ('cool_cats', 'cool_cat_react_pack_i', 11),
                ('cool_cats', 'cool_cat_react_pack_ii', 22),
                # Doodles (4)
                ('doodles', 'doodles_icons_awaken', 44.9),
                ('doodles', 'doodles_timeless_monsters', 14.4),
                ('doodles', 'doodles_holo_pack', 0),
                ('doodles', 'doodles_gold_pack', 0),
                # Moonbirds (2)
                ('moonbirds', 'moonbirds_set_2', 26),
                ('moonbirds', 'moonbirds_set_2_sketch', 45),
                # Pudgy Penguins x Kung Fu Panda (3)
                ('pudgy_penguins_x_kung_fu_panda', 'grand_master_oogway', 11.7),
                ('pudgy_penguins_x_kung_fu_panda', 'dragon_warrior_po', 5.8),
                ('pudgy_penguins_x_kung_fu_panda', 'master_shifu', 46.9),
                # Lamborghini (3)
                ('lamborghini', 'lamborghini_revuelto', 27),
                ('lamborghini', 'lamborghini_urus', 6),
                ('lamborghini', 'lamborghini_temerario', 8.5),
                # BONK (2)
                ('bonk', 'bonk_the_dog', 27),
                ('bonk', 'bonk_hit_harder', 15),
                # Neiro (2)
                ('neiro', 'neiro_woof_vault', 27.5),
                ('neiro', 'neiro_woofin_mad', 15),
                # Meebits (2)
                ('meebits', 'meebits_cube_culture', 16.6),
                ('meebits', 'meebits_blocky_drop', 8.2),
                # Steady Teddys (2)
                ('steady_teddys', 'tedism', 15),
                ('steady_teddys', 'ted_blessed', 8.5),
                # Final Bosu (2) - NEW
                ('final_bosu', 'final_bosu_letsugo_vol_i', 4.2),
                ('final_bosu', 'final_bosu_letsugo_vol_ii', 1.3),
            ]
            
            # Sort by price (highest first)
            all_goodies = sorted(GOODIES_STICKERS, key=lambda x: -x[2])
            logger.info(f"Found {len(all_goodies)} Goodies stickers")
            
            if not all_goodies:
                results = [
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title="No Goodies available",
                        description="No Goodies cards found",
                        input_message_content=InputTextMessageContent(
                            message_text="❌ No Goodies cards available at the moment. Please try again later.",
                            parse_mode=ParseMode.HTML
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")]
                        ])
                    )
                ]
                await update.inline_query.answer(results, cache_time=0)
                return
            
            results = []
            
            # Implement pagination using offset
            try:
                page_offset = int(offset) if offset.isdigit() else 0
            except (ValueError, AttributeError):
                page_offset = 0
            
            # Show 50 goodies per page
            RESULTS_PER_PAGE = 50
            start_idx = page_offset * RESULTS_PER_PAGE
            end_idx = start_idx + RESULTS_PER_PAGE
            
            # Calculate next offset if there are more results
            next_offset = None
            if end_idx < len(all_goodies):
                next_offset = str(page_offset + 1)
            
            logger.info(f"Showing Goodies {start_idx} to {end_idx} (page {page_offset}, total: {len(all_goodies)})")
            
            goodies_to_show = all_goodies[start_idx:end_idx]
            
            for collection, sticker, price in goodies_to_show:
                result_id = str(uuid4())
                
                # Normalize names for CDN URL
                collection_normalized = normalize_cdn_path(collection, "collection")
                sticker_normalized = normalize_cdn_path(sticker, "sticker")
                
                # Create CDN URLs
                timestamp = int(datetime.datetime.now().timestamp())
                goodies_card_filename = f"{collection_normalized}_{sticker_normalized}_price_card.webp"
                goodies_card_url = create_safe_cdn_url("sticker_price_cards", goodies_card_filename) + f"?t={timestamp}"
                goodies_image_url = f"{CDN_BASE_URL}/sticker_collections/{quote(collection_normalized)}/{quote(sticker_normalized)}/1.webp"
                
                # Format display names
                display_collection = collection.replace('_', ' ').title()
                display_sticker = sticker.replace('_', ' ').title()
                
                results.append(
                    InlineQueryResultArticle(
                        id=result_id,
                        title=f"{display_collection} - {display_sticker}",
                        description=f"Goodies from {display_collection}",
                        thumbnail_url=goodies_image_url,
                        input_message_content=InputTextMessageContent(
                            message_text=f"<a href='{goodies_card_url}'> </a><b>{display_collection} - {display_sticker}</b>",
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=False
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")]
                        ])
                    )
                )
            
            logger.info(f"Sending {len(results)} Goodies results for inline query, next_offset: {next_offset}")
            await update.inline_query.answer(results, cache_time=0, next_offset=next_offset)
            return
                
        except Exception as e:
            logger.error(f"Error showing all Goodies: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Handle specific gift search - extract gift name if query starts with "gift "
    search_query = query
    if query.startswith("gift "):
        search_query = query[5:].strip()  # Remove "gift " prefix
        logger.info(f"Extracted gift search query: '{search_query}' from '{query}'")
    
    gifts_to_show = find_matching_gifts(search_query)
    
    # Handle specific sticker collection search
    stickers_to_show = []
    try:
        import sticker_integration
        if sticker_integration.is_sticker_functionality_available():
            # Extract collection name from query (remove "sticker" prefix)
            search_query = query
            if query.startswith("sticker "):
                search_query = query[8:]  # Remove "sticker " prefix
            
            # First try to find matching collections
            collections = sticker_integration.get_sticker_collections()
            matching_collections = [col for col in collections if search_query in col.lower()]
            
            if matching_collections:
                # Count total stickers first
                total_stickers_available = 0
                for collection in matching_collections:
                    stickers = sticker_integration.get_stickers_in_collection(collection)
                    total_stickers_available += len(stickers)
                
                # Show ALL stickers from matching collections
                for collection in matching_collections:
                    stickers = sticker_integration.get_stickers_in_collection(collection)
                    for sticker in stickers:
                        stickers_to_show.append((collection, sticker))
            else:
                # Try exact sticker matching
                sticker_matches = sticker_integration.find_matching_stickers(search_query)
                stickers_to_show = sticker_matches[:10]  # Limit to 10 sticker results for exact matches
                
    except Exception as e:
        logger.error(f"Error finding stickers: {e}")
    

    
    # If no results found, show helpful message
    if not gifts_to_show and not stickers_to_show:
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="No results found",
                description=f"No gifts or stickers found for '{query}'",
                thumbnail_url=create_safe_cdn_url("assets", "no result.webp"),
                input_message_content=InputTextMessageContent(
                    message_text=f"No results found for '{query}'\n\nTry:\n• Type 'gift' to see all gifts\n• Type 'sticker' to see all stickers\n• Search for specific names",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")],
                    [InlineKeyboardButton("Browse Gifts", switch_inline_query_current_chat="gift")],
                    [InlineKeyboardButton("Browse Stickers", switch_inline_query_current_chat="sticker")]
                ])
            )
        ]
        await update.inline_query.answer(results, cache_time=0)
        return
    
    # Create results with images from CDN
    results = []
    
    # Add gift card results
    for gift in gifts_to_show:
        result_id = str(uuid4())
        gift_file_name = normalize_gift_filename(gift)
        
        # Check if this is a plus premarket gift (different filename format)
        try:
            from plus_premarket_gifts import is_plus_premarket_gift
            is_plus_premarket = is_plus_premarket_gift(gift)
        except ImportError:
            is_plus_premarket = False
        
        # Plus premarket gifts use filename without _card suffix
        if is_plus_premarket:
            card_filename = f"{gift_file_name}.webp"
        else:
            card_filename = f"{gift_file_name}_card.webp"
        
        # Create CDN URL for gift card with cache-busting, thumbnail without cache-busting
        timestamp = int(datetime.datetime.now().timestamp())
        gift_card_url = create_safe_cdn_url("new_gift_cards", card_filename, "gift") + f"?t={timestamp}"
        gift_image_url = create_safe_cdn_url("downloaded_images", f"{gift_file_name}.webp", "gift")
        
        # Prepare the caption
        caption = f"💎 {gift} 💎"
        
        # Create a result with photo from CDN
        results.append(
            InlineQueryResultPhoto(
                id=result_id,
                photo_url=gift_card_url,
                thumbnail_url=gift_card_url,
                title=f"{gift}",
                description="Gift Card",
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")]
                ])
            )
        )
    
    # Add sticker results
    for collection, sticker in stickers_to_show:
        result_id = str(uuid4())
        
        # Normalize collection and sticker names for CDN URL using the proper normalization function
        collection_normalized = normalize_cdn_path(collection, "collection")
        sticker_normalized = normalize_cdn_path(sticker, "sticker")
        
        # Create CDN URL for sticker card
        sticker_card_url = f"{CDN_BASE_URL}/sticker_price_cards/{collection_normalized}_{sticker_normalized}_price_card.webp"
        
        # Format names for display (convert snake_case to Title Case)
        collection_display = format_display_name(collection)
        sticker_display = format_display_name(sticker)
        
        # Get sticker info for display
        title = f"{collection_display} - {sticker_display}"
        description = f"Sticker Price Card"
        caption = f"<b>{collection_display} - {sticker_display}</b>"
        
        # Create CDN URL for sticker image thumbnail without cache-busting
        image_number = get_sticker_image_number(collection, sticker)
        collection_path = normalize_cdn_path(collection, "collection")
        sticker_path = normalize_cdn_path(sticker, "sticker")
        sticker_image_url = f"{CDN_BASE_URL}/sticker_collections/{quote(collection_path)}/{quote(sticker_path)}/{quote(image_number)}"
        
        # Create a result with thumbnail from CDN
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title=title,
                description=description,
                thumbnail_url=sticker_image_url,
                input_message_content=InputTextMessageContent(
                    message_text=f"<a href='{sticker_card_url}'> </a>{caption}",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=False
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")]
                ])
            )
        )
    
    # Answer with the results immediately
    try:
        await update.inline_query.answer(results, cache_time=0)
        logger.info(f"Sent inline query results with CDN images")
    except Exception as e:
        logger.error(f"Error sending inline query results: {e}")
        # Fallback to text-only results if image loading fails
        logger.warning("Falling back to text-only results due to image loading error")
        fallback_results = []
        for gift in gifts_to_show:
            result_id = str(uuid4())
            fallback_results.append(
                InlineQueryResultArticle(
                    id=result_id,
                    title=f"{gift}",
                    description="Gift Card (Text Only)",
                    input_message_content=InputTextMessageContent(
                        message_text=f"💎 <b>{gift}</b> 💎\n\nPrice information temporarily unavailable.",
                        parse_mode=ParseMode.HTML
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📢 Join our channel", url="https://t.me/The01Studio")]
                    ])
                )
            )
        
        for collection, sticker in stickers_to_show:
            result_id = str(uuid4())
            fallback_results.append(
                InlineQueryResultArticle(
                    id=result_id,
                    title=f"{collection} - {sticker}",
                    description="Sticker Card (Text Only)",
                    input_message_content=InputTextMessageContent(
                        message_text=f"<b>{collection} - {sticker}</b>\n\nPrice information temporarily unavailable.",
                        parse_mode=ParseMode.HTML
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📢 Join our channel", url="https://t.me/The01Studio")]
                    ])
                )
            )
        
        await update.inline_query.answer(fallback_results, cache_time=0)


# Update the handle_message function to check for FOMO, Samir and Zeus keywords
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages that might contain gift or sticker names."""
    # Skip if message is None or doesn't have text
    if not update.message or not hasattr(update.message, 'text'):
        return
        
    # Skip if the message is a command
    if update.message.text.startswith('/'):
        return
    
    # TIMESTAMP FILTERING: Ignore messages older than 5 minutes
    # This prevents processing old messages when bot comes back online
    if is_message_too_old(update):
        return
        
    # Get user and chat info
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_text = update.message.text
    
    # Get user info for logging
    username = update.effective_user.username or "Unknown"
    chat_type = update.effective_chat.type
    
    
    # Check if we're in a group chat
    is_group = update.effective_chat.type in ["group", "supergroup"]
    
    # Check if the bot was mentioned or replied to
    is_mentioned = False
    is_reply_to_bot = False
    
    # Check if the message is a reply to the bot
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        is_reply_to_bot = update.message.reply_to_message.from_user.id == context.bot.id
    
    # Check if the bot was mentioned in the message
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == MessageEntityType.MENTION:
                mention = update.message.text[entity.offset:entity.offset + entity.length]
                if mention.lower() == BOT_USERNAME.lower() or mention.lower() == BOT_USERNAME.lower().replace('@', ''):
                    is_mentioned = True
                    break
    
    # In groups, only respond if:
    # 1. Bot is mentioned or replied to
    # 2. RESPOND_TO_ALL_MESSAGES is True
    # 3. The chat is in SPECIAL_GROUPS with respond_to_all=True
    should_respond = True
    if is_group:
        # Check if this is a special group with custom settings
        special_group = False
        for group_id, settings in SPECIAL_GROUPS.items():
            if str(chat_id) == str(group_id):
                special_group = True
                if "respond_to_all" in settings:
                    should_respond = settings["respond_to_all"]
                break
                
        # If not a special group, use the default setting
        if not special_group:
            should_respond = RESPOND_TO_ALL_MESSAGES
            
        # Always respond if mentioned or replied to
        if is_mentioned or is_reply_to_bot:
            should_respond = True
    
    # Check premium setup and configure flows ONLY in private chats
    if update.effective_chat.type == "private":
        try:
            # Check for premium setup flow
            if context.user_data.get('premium_setup_step'):
                try:
                    from premium_system import handle_premium_setup
                    await handle_premium_setup(update, context)
                    return
                except ImportError as e:
                    logger.error(f"Premium system module not available: {e}")
                    await update.message.reply_text(
                        f"❌ Premium system not available: {e}"
                    )
                    return
                except Exception as e:
                    logger.error(f"Error in premium setup handler: {e}")
                    logger.exception("Premium setup handler exception details")
                    await update.message.reply_text(
                        f"❌ Error in premium setup: {str(e)}\n\nPlease try /premium again or contact support."
                    )
                    return
            
            # Check for configure flow - handle it directly here
            if context.user_data.get('configure_step') == 'link_update':
                logger.info("Handling link update in message handler")
                try:
                    from premium_system import premium_system, is_valid_link
                    logger.info("Imported premium system modules")
                    
                    # Get data from context
                    link_type = context.user_data.get('configure_link_type')
                    group_id = context.user_data.get('configure_group_id')
                    logger.info(f"Link type: {link_type}, Group ID: {group_id}")
                    
                    if not link_type or not group_id:
                        logger.warning("Missing link_type or group_id in user data")
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="❌ Missing configuration data. Please use /configure to start again."
                        )
                        context.user_data.clear()
                        return
                    
                    # Get the new link from the message
                    new_link = update.message.text.strip()
                    logger.info(f"New link received: {new_link}")
                    
                    # Validate the link format
                    is_valid = is_valid_link(new_link, link_type)
                    logger.info(f"Link validation result: {is_valid}")
                    
                    if not is_valid:
                        logger.warning(f"Invalid {link_type} link format")
                        example = (
                            "https://t.me/mrkt/app?startapp=123456789" if link_type == 'mrkt' else
                            "https://t.me/tonnel_network_bot/gifts?startapp=ref_123456789" if link_type == 'tonnel' else
                            "https://t.me/portals/market?startapp=abc123" if link_type == 'portal' else
                            "https://t.me/palacenftbot/app?startapp=abc123def"
                        )
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=f"❌ Invalid {link_type.upper()} link format.\n\nExample: {example}\n\nPlease try again:"
                        )
                        return
                    
                    # Get current links
                    logger.info(f"Getting current links for group {group_id}")
                    links = premium_system.get_premium_links(group_id)
                    logger.info(f"Current links: {links}")
                    
                    if not links:
                        logger.warning(f"No premium subscription found for group {group_id}")
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="❌ Could not find premium subscription for this group. Please use /configure to start again."
                        )
                        context.user_data.clear()
                        return
                    
                    # Prepare updated links
                    mrkt_link = new_link if link_type == 'mrkt' else links.get('mrkt_link')
                    palace_link = new_link if link_type == 'palace' else links.get('palace_link')
                    tonnel_link = new_link if link_type == 'tonnel' else links.get('tonnel_link')
                    portal_link = new_link if link_type == 'portal' else links.get('portal_link')
                    
                    logger.info(f"Updating links: MRKT={mrkt_link}, Palace={palace_link}, Tonnel={tonnel_link}, Portal={portal_link}")
                    
                    # Update the subscription
                    success = premium_system.add_premium_subscription(
                        user_id, group_id, 'update', mrkt_link, palace_link, tonnel_link, portal_link
                    )
                    logger.info(f"Update result: {success}")
                    
                    if success:
                        # Send success message
                        success_msg = f"✅ {link_type.upper()} link updated successfully!\n\nNew link: {new_link}"
                        logger.info(f"Sending success message: {success_msg}")
                        
                        sent_msg = await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=success_msg
                        )
                        logger.info(f"Success message sent with ID: {sent_msg.message_id}")
                        
                        # Show updated menu with current status
                        from premium_system import premium_system
                        links = premium_system.get_premium_links(group_id)
                        
                        # Create keyboard with 4 market buttons in 2x2 grid plus Done button
                        keyboard = [
                            [
                                InlineKeyboardButton("🛒 MRKT", callback_data="edit_mrkt"),
                                InlineKeyboardButton("🏰 Palace", callback_data="edit_palace")
                            ],
                            [
                                InlineKeyboardButton("🌉 Tonnel", callback_data="edit_tonnel"),
                                InlineKeyboardButton("🚪 Portal", callback_data="edit_portal")
                            ],
                            [
                                InlineKeyboardButton("✅ Done", callback_data="edit_done")
                            ]
                        ]
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        # Show current links status
                        current_links = []
                        for market in ["MRKT", "Palace", "Tonnel", "Portal"]:
                            link_key = f"{market.lower()}_link"
                            if links.get(link_key):
                                current_links.append(f"✅ {market}: Set")
                            else:
                                current_links.append(f"❌ {market}: Not set")
                        
                        status_text = "\n".join(current_links)
                        
                        menu_msg = (
                            "🔧 **Configure Your Referral Links**\n\n"
                            "Click on any market button to update its referral link.\n\n"
                            "**Current Status:**\n" + status_text + "\n\n"
                            "Click **Done** when you're finished."
                        )
                        
                        sent_menu = await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=menu_msg,
                            parse_mode='Markdown',
                            reply_markup=reply_markup
                        )
                        logger.info(f"Menu message sent with ID: {sent_menu.message_id}")
                        
                        # Reset step to edit_menu
                        context.user_data['configure_step'] = 'edit_menu'
                        logger.info(f"Updated user data: {context.user_data}")
                    else:
                        # Send failure message
                        logger.warning("Failed to update link")
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="❌ Failed to update link. Please try again later."
                        )
                    
                    return
                except Exception as e:
                    logger.error(f"Error handling link update: {e}", exc_info=True)
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="❌ An error occurred while updating the link. Please try again or use /configure to restart."
                    )
                    return
        except Exception as e:
            logger.error(f"Error checking for setup flows: {e}")
    
    # Don't proceed if we shouldn't respond to regular messages
    if not should_respond:
        return
    
    # Stickers are only accessible via inline mode or /sticker command
    # Chat messages only search for gifts
    # Try to find matching gifts
    matching_gifts = find_matching_gifts(message_text)
    
    # If we found exactly one matching gift, show it
    if len(matching_gifts) == 1:
        gift_name = matching_gifts[0]
        # Apply rate limiting
        try:
            from rate_limiter import can_user_request
            can_request, seconds_remaining = can_user_request(user_id, chat_id, f"gift_{gift_name}")
            
            if not can_request:
                # User is rate limited for this gift
                if seconds_remaining > 0:
                    # Only notify in private chats or when mentioned to avoid spam
                    is_private = update.message.chat.type == "private"
                    
                    if is_private or is_mentioned:
                        await update.message.reply_text(
                            f"⏱️ You can request each gift once per minute. Please wait {seconds_remaining} seconds to request {gift_name} again.",
                            reply_to_message_id=update.message.message_id
                        )
                return
        except ImportError:
            # Rate limiter not available, continue without rate limiting
            logger.warning("Rate limiter not available, continuing without rate limiting")
        
        # Log gift request for analytics
        if ADMIN_DASHBOARD_AVAILABLE:
            log_gift_request(user_id, username, chat_type, gift_name)
        
        await send_gift_card(update, context, gift_name)
        return
    if len(matching_gifts) > 1 and len(matching_gifts) <= 8:
        # Apply rate limiting for gift searches
        try:
            from rate_limiter import can_user_use_command
            search_query = message_text.lower().replace(' ', '_')
            can_use, seconds_remaining = can_user_use_command(user_id, chat_id, f"gift_search_{search_query}")
            
            if not can_use:
                # User is rate limited for this gift search
                if update.effective_chat.type == "private":
                    # Only notify in private chats to avoid spam
                    await update.message.reply_text(f"⏰ Please wait {seconds_remaining} seconds before searching for '{message_text}' again.")
                return
        except ImportError:
            # Rate limiter not available, continue without rate limiting
            logger.warning("Rate limiter not available, continuing without rate limiting")
        
        # Build keyboard with gifts
        keyboard = []
        row = []
        for i, name in enumerate(matching_gifts[:8]):  # Limit to 8 results
            # Sanitize callback data - replace spaces and special chars with underscores
            sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
            row.append(InlineKeyboardButton(name, callback_data=f"gift_{sanitized_name}"))
            if i % 2 == 1 or i == len(matching_gifts[:8]) - 1:
                keyboard.append(row)
                row = []
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_message = await update.message.reply_text(
            f"🔍 Found {len(matching_gifts)} gifts matching '{message_text}'.\nSelect one to view:",
            reply_markup=reply_markup
        )
        
        # Register the message owner in the database for button permission tracking
        try:
            from rate_limiter import register_message
            register_message(user_id, chat_id, sent_message.message_id)
            logger.info(f"Registered gift search results message {sent_message.message_id} to user {user_id}")
        except ImportError:
            logger.warning("Rate limiter not available, message ownership not registered")
        except Exception as e:
            logger.error(f"Error registering message ownership: {e}")
        
        return
    
    # Don't show any default message - just stay silent if no matches found
    # This prevents spam in group chats

# Command handler for /configure
async def configure_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger = logging.getLogger(__name__)
    
    # Check if user is in private chat (required for premium operations)
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "💫 Premium operations can only be performed in private chat.\n"
            "Please message me privately to continue."
        )
        return
    
    try:
        user_id = update.effective_user.id
        from premium_system import premium_system
        groups = premium_system.get_user_premium_groups(user_id)
        if not groups:
            await update.message.reply_text(
                "❌ You do not own any active premium groups.\nPurchase premium with /premium first."
            )
            return
        
        # Use selected or only group
        group_id = context.user_data.get('configure_group_id') or groups[0]['group_id']
        context.user_data['configure_group_id'] = group_id
        
        # Check for missing links
        links = premium_system.get_premium_links(group_id)
        if not links:
            await update.message.reply_text(
                "❌ No premium subscription found for this group.\nPurchase premium with /premium first."
            )
            return
        
        # Show the configure menu with 4 buttons for each market plus Done button
        
        # Create keyboard with 4 market buttons in 2x2 grid plus Done button
        keyboard = [
            [
                InlineKeyboardButton("🛒 MRKT", callback_data="edit_mrkt"),
                InlineKeyboardButton("🏰 Palace", callback_data="edit_palace")
            ],
            [
                InlineKeyboardButton("🌉 Tonnel", callback_data="edit_tonnel"),
                InlineKeyboardButton("🚪 Portal", callback_data="edit_portal")
            ],
            [
                InlineKeyboardButton("✅ Done", callback_data="edit_done")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Show current links status
        current_links = []
        for market in ["MRKT", "Palace", "Tonnel", "Portal"]:
            link_key = f"{market.lower()}_link"
            if links.get(link_key):
                current_links.append(f"✅ {market}: Set")
            else:
                current_links.append(f"❌ {market}: Not set")
        
        status_text = "\n".join(current_links)
        
        message_text = (
            "🔧 **Configure Your Referral Links**\n\n"
            "Click on any market button to update its referral link.\n\n"
            "**Current Status:**\n" + status_text + "\n\n"
            "Click **Done** when you're finished."
        )
        
        # Send photo with configure text
        photo_path = os.path.join(ASSETS_DIR, "configure.webp")
        if os.path.exists(photo_path):
            await update.message.reply_photo(
                photo=open(photo_path, 'rb'),
                caption=message_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            # Fallback to text only if image not found
            await update.message.reply_text(
                message_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        # Set the step to edit_menu
        context.user_data['configure_step'] = 'edit_menu'
        
    except Exception as e:
        logger.error(f"Error in /configure: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing /configure. Please try again or contact support."
        )
        return

# Add a callback handler for the edit buttons
async def configure_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callbacks for editing referral links."""
    logger.info("Configure callback handler started")
    
    try:
        # Get the callback query
        query = update.callback_query
        
        # Log the query data
        logger.info(f"Received callback query with data: {query.data}")
        
        # Answer the callback query to remove the loading indicator
        await query.answer()
        logger.info("Callback query answered")
        
        # Get user and chat info
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        logger.info(f"User ID: {user_id}, Chat ID: {chat_id}")
        
        # Get the group ID from user data
        group_id = context.user_data.get('configure_group_id')
        logger.info(f"Group ID from user data: {group_id}")
        
        if not group_id:
            logger.warning("No group ID found in user data")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Please use /configure to start the configuration process."
            )
            return
        
        # Extract the link type from the callback data
        link_type = query.data.replace('edit_', '')
        logger.info(f"Link type: {link_type}")
        
        # Store the link type and step in user data
        context.user_data['configure_link_type'] = link_type
        context.user_data['configure_step'] = 'link_update'
        logger.info(f"Updated user data: {context.user_data}")
        
        # Get the example link based on link type
        example = (
            "https://t.me/mrkt/app?startapp=123456789" if link_type == 'mrkt' else
            "https://t.me/tonnel_network_bot/gifts?startapp=ref_123456789" if link_type == 'tonnel' else
            "https://t.me/portals/market?startapp=abc123" if link_type == 'portal' else
            "https://t.me/palacenftbot/app?startapp=abc123def"
        )
        
        # Prepare the message text
        message_text = f"📝 Send your new {link_type.upper()} link.\n\nExample: {example}"
        logger.info(f"Prepared message text: {message_text}")
        
        # Send the message
        try:
            sent_message = await context.bot.send_message(
                chat_id=chat_id,
                text=message_text
            )
            logger.info(f"Message sent successfully with ID: {sent_message.message_id}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
        
        logger.info(f"User {user_id} started editing {link_type} link for group {group_id}")
        
    except Exception as e:
        logger.error(f"Error in configure callback handler: {e}", exc_info=True)
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred. Please try again or use /configure to restart."
            )
        except Exception as e2:
            logger.error(f"Error sending error message: {e2}", exc_info=True)

# Add a callback handler for the edit_done button
async def configure_done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the edit_done callback."""
    logger.info("Configure done handler started")
    
    try:
        # Get the callback query
        query = update.callback_query
        logger.info(f"Received done callback query: {query.data}")
        
        # Answer the callback query to remove the loading indicator
        await query.answer()
        logger.info("Done callback query answered")
        
        # Get user and chat info
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        logger.info(f"User ID: {user_id}, Chat ID: {chat_id}")
        
        # Clear the configuration state
        old_data = dict(context.user_data)
        context.user_data.clear()
        logger.info(f"Cleared user data. Previous data was: {old_data}")
        
        # Prepare the message text
        message_text = "✅ Configuration complete! Your referral links have been updated.\n\n" \
                       "You can use /configure anytime to edit them again."
        logger.info(f"Prepared done message: {message_text}")
        
        # Send the message
        try:
            sent_message = await context.bot.send_message(
                chat_id=chat_id,
                text=message_text
            )
            logger.info(f"Done message sent with ID: {sent_message.message_id}")
        except Exception as e:
            logger.error(f"Error sending done message: {e}")
            raise
        
        logger.info(f"User {user_id} completed link configuration")
        
    except Exception as e:
        logger.error(f"Error in configure done handler: {e}", exc_info=True)
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred. Your links may have been saved. Use /configure to check."
            )
        except Exception as e2:
            logger.error(f"Error sending done error message: {e2}", exc_info=True)

# Dictionary to cache uploaded photos (gift_name -> file_id)
photo_cache = {}

# Helper function to ensure a card is generated and uploaded
async def ensure_uploaded_card(context, gift_name):
    """Ensure a gift card is generated and uploaded to Telegram servers."""
    global photo_cache
    
    # Check if we already have the file_id cached
    if gift_name in photo_cache:
        return photo_cache[gift_name]
    
    # Generate the card
    card_path = generate_gift_card(gift_name)
    
    if card_path and os.path.exists(card_path):
        try:
            # Upload the photo to Telegram servers
            with open(card_path, 'rb') as photo_file:
                message = await context.bot.send_photo(
                    chat_id=context.bot.id,  # Send to the bot itself
                    photo=photo_file,
                    caption=f"🎁 {gift_name} (Cached for inline mode)"
                )
                
                # Get the file_id from the uploaded photo
                file_id = message.photo[-1].file_id
                
                # Cache the file_id for future use
                photo_cache[gift_name] = file_id
                
                return file_id
        except Exception as e:
            logging.error(f"Error uploading card for {gift_name}: {e}")
            return None
    
    return None

def get_gift_price_card_keyboard(is_premium, mrkt_link, tonnel_link, portal_link, palace_link, user_id=None):
    # Main keyboard: first row [Buy/Sell Gifts] [Premium Active or Get Premium], second row [Delete]
    if is_premium:
        keyboard = [
            [
                InlineKeyboardButton("💰 Buy/Sell Gifts", callback_data="show_markets"),
                InlineKeyboardButton("💫 Premium Active", callback_data="premium_info")
            ],
            [
                InlineKeyboardButton("🗑️ Delete", callback_data="delete")
            ]
        ]
    else:
        # Include user ID in callback data for permission checking
        premium_callback = f"premium_button:{user_id}" if user_id else "premium_button"
        keyboard = [
            [
                InlineKeyboardButton("💰 Buy/Sell Gifts", callback_data="show_markets"),
                InlineKeyboardButton("💫 Get Premium", callback_data=premium_callback)
            ],
            [
                InlineKeyboardButton("🗑️ Delete", callback_data="delete")
            ]
        ]
    return InlineKeyboardMarkup(keyboard)

def get_markets_submenu_keyboard(mrkt_link, tonnel_link, portal_link, palace_link):
    # Submenu: [Portal] [Tonnel] [MRKT] in the first row, [Back] in the second row
    keyboard = []
    
    # Create buttons only for valid links
    first_row = []
    if portal_link:
        first_row.append(InlineKeyboardButton("Portal", url=portal_link))
    if tonnel_link:
        first_row.append(InlineKeyboardButton("Tonnel", url=tonnel_link))
    if mrkt_link:
        first_row.append(InlineKeyboardButton("MRKT", url=mrkt_link))
    
    # Add first row if we have any valid links
    if first_row:
        keyboard.append(first_row)
    
    # Always add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)

# Add the premium status command handler
async def premium_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /premium_status command to show user's premium configuration."""
    # Check if premium system is available
    if handle_premium_status is None:
        await update.message.reply_text(
            "❌ Premium system not available. Please contact support."
        )
        return
    
    # Check if user is in private chat (for privacy)
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "🔒 For privacy, please use /premium_status in a private chat with me."
        )
        return
    
    # Call the premium status handler
    await handle_premium_status(update, context)

# =============================================================================
# INTEGRATED BACKUP SYSTEM
# =============================================================================

# Global variables for backup system
backup_system_running = True
backup_system_thread = None

def start_integrated_backup_system():
    """Start the integrated backup system in a background thread."""
    global backup_system_thread, backup_system_running
    
    backup_system_running = True
    backup_system_thread = threading.Thread(target=backup_system_worker, daemon=True)
    backup_system_thread.start()
    logger.info("🔒 Integrated backup system started successfully")

def stop_integrated_backup_system():
    """Stop the integrated backup system."""
    global backup_system_running
    backup_system_running = False
    logger.info("🔒 Integrated backup system stopped")

def backup_system_worker():
    """Background worker for the backup system."""
    import zipfile
    import sqlite3
    from datetime import datetime, timedelta
    from telegram import Bot
    
    logger.info("🔒 Backup system worker started")
    
    # Create backup bot instance
    backup_bot = Bot(token=BOT_TOKEN)
    

    
    # Paths - using centralized config
    from config.paths import SQLITE_DATA_DIR
    sqlite_data_dir = SQLITE_DATA_DIR
    backup_dir = os.path.join(sqlite_data_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup configuration
    MAX_BACKUP_AGE_DAYS = 7
    MAX_BACKUP_COUNT = 50
    BACKUP_INTERVAL_MINUTES = 60  # PRODUCTION: Hourly backups
    
    async def create_and_send_backup():
        """Create and send backup to admins."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"database_backup_{timestamp}.zip"
            zip_path = os.path.join(backup_dir, zip_filename)
            
            # Get database files
            db_files = []
            total_db_size = 0
            
            if os.path.exists(sqlite_data_dir):
                for filename in os.listdir(sqlite_data_dir):
                    if filename.endswith('.db'):
                        filepath = os.path.join(sqlite_data_dir, filename)
                        if os.path.isfile(filepath):
                            # Verify database integrity
                            try:
                                conn = sqlite3.connect(filepath)
                                cursor = conn.cursor()
                                cursor.execute("PRAGMA integrity_check;")
                                result = cursor.fetchone()
                                conn.close()
                                
                                if result and result[0] == 'ok':
                                    db_files.append(filepath)
                                    total_db_size += os.path.getsize(filepath)
                                else:
                                    logger.error(f"🔒 Database integrity check failed for {filepath}")
                            except Exception as e:
                                logger.error(f"🔒 Error checking database {filepath}: {e}")
            
            if not db_files:
                logger.warning("🔒 No valid database files found for backup")
                return False
            
            # Create backup zip
            backup_info = {
                'timestamp': timestamp,
                'files': [],
                'total_size': 0
            }
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for db_file in db_files:
                    arcname = os.path.basename(db_file)
                    zipf.write(db_file, arcname)
                    
                    file_size = os.path.getsize(db_file)
                    backup_info['files'].append({
                        'name': arcname,
                        'size': file_size,
                        'size_mb': round(file_size / (1024*1024), 2)
                    })
                    backup_info['total_size'] += file_size
                    
                    logger.info(f"🔒 Added {arcname} to backup ({file_size} bytes)")
                
                # Add backup info
                info_content = f"""Database Backup Information
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Files: {len(backup_info['files'])}
Total Size: {round(backup_info['total_size'] / (1024*1024), 2)} MB

Files Included:
"""
                for file_info in backup_info['files']:
                    info_content += f"- {file_info['name']}: {file_info['size_mb']} MB\n"
                
                zipf.writestr("backup_info.txt", info_content)
            
            backup_size = os.path.getsize(zip_path)
            logger.info(f"🔒 Created backup zip: {zip_filename} ({backup_size} bytes)")
            
            # Send to admins
            success_count = 0
            file_size_mb = round(backup_size / (1024*1024), 2)
            
            caption = f"""🔒 **Database Backup Report**
            
📅 **Backup Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 **Files Backed Up**: {len(backup_info['files'])}
💾 **Total Size**: {file_size_mb} MB
🔐 **Backup Status**: ✅ Complete

**Databases Included:**
"""
            
            for file_info in backup_info['files']:
                caption += f"• {file_info['name']}: {file_info['size_mb']} MB\n"
            
            caption += f"\n💡 **Tip**: Extract this zip file to restore your databases if needed."
            
            # Send to group chat instead of individual admins
            GROUP_CHAT_ID = -4944651195  # Your group chat ID
            try:
                with open(zip_path, 'rb') as backup_file:
                    await backup_bot.send_document(
                        chat_id=GROUP_CHAT_ID,
                        document=backup_file,
                        caption=caption,
                        parse_mode='Markdown'
                    )
                logger.info(f"🔒 Successfully sent backup to group chat {GROUP_CHAT_ID}")
                success_count = 1
            except Exception as e:
                logger.error(f"🔒 Failed to send backup to group chat {GROUP_CHAT_ID}: {e}")
                success_count = 0
            
            logger.info(f"🔒 Backup sent to group chat: {'Success' if success_count > 0 else 'Failed'}")
            
            # Cleanup old backups
            cleanup_old_backups(backup_dir, MAX_BACKUP_AGE_DAYS, MAX_BACKUP_COUNT)
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"🔒 Error creating backup: {e}")
            return False
    
    def cleanup_old_backups(backup_dir, max_age_days, max_count):
        """Clean up old backup files."""
        try:
            now = datetime.now()
            deleted_count = 0
            
            # Get all backup files
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.startswith('database_backup_') and filename.endswith('.zip'):
                    filepath = os.path.join(backup_dir, filename)
                    if os.path.isfile(filepath):
                        backup_files.append((filepath, os.path.getmtime(filepath)))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove files older than max_age_days
            for filepath, mtime in backup_files:
                file_age = now - datetime.fromtimestamp(mtime)
                if file_age.days > max_age_days:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(f"🔒 Deleted old backup: {os.path.basename(filepath)}")
            
            # Remove excess files if we have too many
            if len(backup_files) > max_count:
                excess_files = backup_files[max_count:]
                for filepath, _ in excess_files:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        deleted_count += 1
                        logger.info(f"🔒 Deleted excess backup: {os.path.basename(filepath)}")
            
            if deleted_count > 0:
                logger.info(f"🔒 Cleaned up {deleted_count} old backup files")
                
        except Exception as e:
            logger.error(f"🔒 Error during backup cleanup: {e}")
    
    def calculate_next_backup_time(last_backup_time=None):
        """Calculate the next backup time based on interval."""
        now = datetime.now()
        if BACKUP_INTERVAL_MINUTES == 60:
            # Hourly backups - every hour from last backup time
            if last_backup_time:
                next_backup = last_backup_time + timedelta(hours=1)
            else:
                # For first backup, start on the next hour
                next_backup = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            # Testing intervals - every N minutes from last backup
            if last_backup_time:
                next_backup = last_backup_time + timedelta(minutes=BACKUP_INTERVAL_MINUTES)
            else:
                next_backup = now + timedelta(minutes=BACKUP_INTERVAL_MINUTES)
        return next_backup
    
    # Perform initial backup
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Initial backup
        logger.info("🔒 Performing initial backup...")
        loop.run_until_complete(create_and_send_backup())
        last_backup_time = datetime.now()
        
        # Calculate and log next backup time
        next_backup = calculate_next_backup_time(last_backup_time)
        logger.info(f"🔒 Backup system initialized. Next backup scheduled for: {next_backup.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Main backup loop
        while backup_system_running:
            try:
                now = datetime.now()
                next_backup = calculate_next_backup_time(last_backup_time)
                
                # If it's past the next backup time, perform backup
                if now >= next_backup:
                    logger.info(f"🔒 Starting scheduled backup (every {BACKUP_INTERVAL_MINUTES} minutes)...")
                    loop.run_until_complete(create_and_send_backup())
                    last_backup_time = datetime.now()
                    
                    # Calculate next backup time based on new last backup time
                    next_backup = calculate_next_backup_time(last_backup_time)
                    logger.info(f"🔒 Next backup scheduled for: {next_backup.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    # Log when next backup will occur (every 10 minutes)
                    time_until_next = (next_backup - now).total_seconds()
                    if int(time_until_next) % 600 == 0:  # Log every 10 minutes
                        logger.info(f"🔒 Next backup in {int(time_until_next/60)} minutes at {next_backup.strftime('%H:%M:%S')}")
                
                # Sleep for a short time to avoid busy waiting
                sleep_time = min(60, (next_backup - now).total_seconds())
                
                if sleep_time > 0 and backup_system_running:
                    time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"🔒 Error in backup scheduler loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
        
    except Exception as e:
        logger.error(f"🔒 Fatal error in backup system: {e}")
    finally:
        loop.close()
        logger.info("🔒 Backup system worker stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    stop_integrated_backup_system()
    sys.exit(0)

def main() -> None:
    """Start the bot."""
    # Initialize rate limiter database
    try:
        from rate_limiter import ensure_tables_exist
        ensure_tables_exist()
        logger.info("Database tables verified or created")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    
    # Log configuration
    print("=== Telegram Gift Price Bot Configuration ===")
    print(f"Bot username: {BOT_USERNAME}")
    print(f"Respond to all messages in groups: {RESPOND_TO_ALL_MESSAGES}")
    print(f"Special gift name matching: ENABLED")
    print("This bot will respond to gift names like 'tama' in groups even without admin privileges")
    print("============================================")
    
    logger.info(f"Starting bot with username: {BOT_USERNAME}")
    logger.info(f"RESPOND_TO_ALL_MESSAGES: {RESPOND_TO_ALL_MESSAGES}")
    logger.info("Special gift name matching is enabled")
    
    # Create the Application and pass it your bot's token
    # Determine the connection method based on configuration
    connection_pool_size = 8  # Use larger pool for better performance
    http_version = "2"  # Use HTTP/2 for better performance
    connect_timeout = 30.0  # Longer timeout for more stable connections
    read_timeout = 30.0  # Longer timeout for more stable connections
    write_timeout = 30.0  # Longer timeout for more stable connections
    
    # Create the Application and pass it your bot's token.
    token = BOT_TOKEN
    
    # Add network connectivity check
    try:
        # Test connection to Telegram API
        host = "api.telegram.org"
        socket.create_connection((host, 443), timeout=5)
        logger.info("Network connection to Telegram API is available")
    except OSError as e:
        logger.error(f"Network connectivity issue: {e}")
        logger.error("Cannot connect to Telegram API. Please check your internet connection.")
        print("ERROR: Cannot connect to Telegram API. Please check your internet connection.")
        return
    
    # Check if bot token is valid format
    if not token or token == "YOUR_TOKEN_HERE" or len(token.split(":")) != 2:
        logger.error("Invalid bot token. Please check your bot_config.py file.")
        print("ERROR: Invalid bot token. Please check your bot_config.py file.")
        return
    
    # Build the application with base settings
    builder = Application.builder().token(token).pool_timeout(30.0).connection_pool_size(8)
    
    # Build the application
    application = builder.build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("devs", devs_command))
    application.add_handler(CommandHandler("premium", premium_command))
    application.add_handler(CommandHandler("premium_status", premium_status_command))
    application.add_handler(CommandHandler("cancel_premium", cancel_premium_command))
    application.add_handler(CommandHandler("terms", terms_command))
    application.add_handler(CommandHandler("refund", refund_command))
    application.add_handler(CommandHandler("sticker", sticker_command))
    

    
    # Inline mode handler
    application.add_handler(InlineQueryHandler(inline_query))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(CallbackQueryHandler(handle_refund_callback, pattern=r'^(refund_policy|contact_support|refund_request:)'))
    
    # Add payment handlers
    try:
        from premium_system import handle_pre_checkout_query, handle_successful_payment, handle_configure_flow, handle_premium_group_share, handle_premium_setup
        from telegram.ext import PreCheckoutQueryHandler, MessageHandler, filters
        
        # Pre-checkout query handler
        application.add_handler(PreCheckoutQueryHandler(handle_pre_checkout_query))
        
        # Successful payment handler
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, handle_successful_payment))
        
        # Add group share handler for premium flow - use custom filter for chat_shared messages
        class ChatSharedFilter(filters.MessageFilter):
            def filter(self, message):
                return message.chat_shared is not None
        
        application.add_handler(MessageHandler(filters.ChatType.PRIVATE & ChatSharedFilter(), handle_premium_group_share))
        
        # Add configure command handler
        application.add_handler(CommandHandler("configure", configure_command))
        
        # Add configure callback handlers
        application.add_handler(CallbackQueryHandler(configure_callback_handler, pattern=r'^edit_(?!done)'))
        application.add_handler(CallbackQueryHandler(configure_done_handler, pattern=r'^edit_done$'))
        
        logger.info("Premium payment handlers and group share handler registered")
    except ImportError:
        logger.warning("Premium payment handlers not available")
    
    # Check if sticker functionality is available
    try:
        import sticker_integration
        if sticker_integration.is_sticker_functionality_available():
            logger.info("Sticker functionality is available and registered")
        else:
            logger.warning("Sticker functionality is not available (missing files)")
    except ImportError:
        logger.warning("Sticker integration module not available")
    
    # Add message handler (must be last)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Print chat response configuration
    print(f"Bot configured to {'respond to all messages' if RESPOND_TO_ALL_MESSAGES else 'only respond when mentioned'} in group chats")
    logger.info(f"Bot configured to {'respond to all messages' if RESPOND_TO_ALL_MESSAGES else 'only respond when mentioned'} in group chats")
    
    # Start the Bot with error handling
    try:
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Starting bot...")
        
        # Start integrated backup system
        start_integrated_backup_system()
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except NetworkError as e:
        logger.error(f"Network error: {e}")
        print(f"Network error: {e}")
        print("Please check your internet connection and try again later.")
    except ConnectError as e:
        logger.error(f"Connection error: {e}")
        print(f"Connection error: {e}")
        print("Cannot connect to Telegram servers. Please check your internet connection.")
    except ProxyError as e:
        logger.error(f"Proxy error: {e}")
        print(f"Proxy error: {e}")
        print("There was an error with your proxy configuration.")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        print(f"Error running bot: {e}")
        print("Please check the logs for details.")

if __name__ == "__main__":
    main() 