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
SPECIAL_GROUPS = {
    # Group ID: {referral_configs}
    -1002155968676: {
        "buy_sell_link": "https://t.me/Tonnel_Network_bot/gifts?startapp=ref_1251203296",
        "portal_link": "https://t.me/portals/market?startapp=1251203296"
    },
    -1001891015899: {
        "buy_sell_link": "https://t.me/tonnel_network_bot/gifts?startapp=ref_1109811477",
        "portal_link": "https://t.me/portals/market?startapp=1109811477"
    }
}

# Default referral links for non-premium groups
DEFAULT_BUY_SELL_LINK = "https://t.me/tonnel_network_bot/gifts?startapp=ref_7660176383"
DEFAULT_TONNEL_LINK = "https://t.me/tonnel_network_bot/gifts?startapp=ref_7660176383"
DEFAULT_PALACE_LINK = "https://t.me/palacenftbot/app?startapp=zOyJPdbc9t"
DEFAULT_PORTAL_LINK = "https://t.me/portals/market?startapp=q7iu6i"
DEFAULT_MRKT_LINK = "https://t.me/mrkt/app?startapp=7660176383"

# Help system configuration
HELP_IMAGE_PATH = os.path.join(ASSETS_DIR, "help.jpg")

# CDN Configuration
CDN_BASE_URL = "https://giftschart.the01studio.xyz/api"
