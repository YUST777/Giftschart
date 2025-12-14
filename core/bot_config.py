# Telegram Bot Configuration

import os
import sys

# Add project root to path for config imports
_project_root = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(_project_root) != 'giftschart':
    _project_root = os.path.dirname(_project_root)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars

# Import centralized paths
from config.paths import PROJECT_ROOT, ASSETS_DIR

# Bot configuration - loaded from environment
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set! Create a .env file with your token.")

BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "@giftsChartBot")
RESPOND_TO_ALL_MESSAGES = True
USE_DIRECT_IP = False
API_TELEGRAM_IP = "149.154.167.220"
SKIP_SSL_VERIFY = False

# Special groups configuration
# These groups will have custom buttons with specific referral links
# Load from environment or use empty dict
SPECIAL_GROUPS = {}

# Try to load special groups from environment
special_group_1_id = os.environ.get("SPECIAL_GROUP_1_ID")
special_group_1_ref = os.environ.get("SPECIAL_GROUP_1_REF")
special_group_2_id = os.environ.get("SPECIAL_GROUP_2_ID")
special_group_2_ref = os.environ.get("SPECIAL_GROUP_2_REF")

if special_group_1_id and special_group_1_ref:
    SPECIAL_GROUPS[int(special_group_1_id)] = {
        "buy_sell_link": f"https://t.me/Tonnel_Network_bot/gifts?startapp=ref_{special_group_1_ref}",
        "portal_link": f"https://t.me/portals/market?startapp={special_group_1_ref}"
    }

if special_group_2_id and special_group_2_ref:
    SPECIAL_GROUPS[int(special_group_2_id)] = {
        "buy_sell_link": f"https://t.me/tonnel_network_bot/gifts?startapp=ref_{special_group_2_ref}",
        "portal_link": f"https://t.me/portals/market?startapp={special_group_2_ref}"
    }

# Default referral links for non-premium groups
DEFAULT_REFERRAL_ID = os.environ.get("DEFAULT_REFERRAL_ID", "7660176383")
DEFAULT_BUY_SELL_LINK = f"https://t.me/tonnel_network_bot/gifts?startapp=ref_{DEFAULT_REFERRAL_ID}"
DEFAULT_TONNEL_LINK = f"https://t.me/tonnel_network_bot/gifts?startapp=ref_{DEFAULT_REFERRAL_ID}"
DEFAULT_PALACE_LINK = os.environ.get("DEFAULT_PALACE_LINK", "https://t.me/palacenftbot/app?startapp=zOyJPdbc9t")
DEFAULT_PORTAL_LINK = os.environ.get("DEFAULT_PORTAL_LINK", "https://t.me/portals/market?startapp=q7iu6i")
DEFAULT_MRKT_LINK = f"https://t.me/mrkt/app?startapp={DEFAULT_REFERRAL_ID}"

# Help system configuration
HELP_IMAGE_PATH = os.path.join(ASSETS_DIR, "help.jpg")

# CDN Configuration
CDN_BASE_URL = os.environ.get("CDN_BASE_URL", "https://giftschart.the01studio.xyz/api")

# Community Configuration
COMMUNITY_CHANNEL = os.environ.get("COMMUNITY_CHANNEL", "@The01Studio")
SUPPORT_CHANNEL = os.environ.get("SUPPORT_CHANNEL", "@GiftsChart_Support")
DONATION_ADDRESS = os.environ.get("DONATION_ADDRESS", "UQCFRqB2vZnGZRh3ZoZAItNidk8zpkN0uRHlhzrnwweU3mos")
TERMS_URL = os.environ.get("TERMS_URL", "https://telegra.ph/GiftsChart-07-06")
