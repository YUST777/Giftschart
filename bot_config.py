# Telegram Bot Configuration

import os
import sys
import traceback

# File paths - using the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(script_dir, "bot_config.py")

# Default values
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "7896040752:AAHTM8jlCSe227r7MchVqKnHeOfVn6OLRns")
BOT_USERNAME = "@giftsChartBot"
RESPOND_TO_ALL_MESSAGES = True
USE_DIRECT_IP = False
API_TELEGRAM_IP = "149.154.167.220"
SKIP_SSL_VERIFY = False

# Admin user IDs - list of Telegram user IDs allowed to access the admin panel
ADMIN_USER_IDS = [800092886, 6529233780]  # Add your user IDs here

# Portal API configuration (replaces Tonnel API)
# Portal API credentials are now handled in portal_api.py
# No additional configuration needed here

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
HELP_IMAGE_PATH = os.path.join(script_dir, "assets", "help.jpg")

# Try to load custom configuration from environment
try:
    # Check if token is provided in environment
    if "TELEGRAM_BOT_TOKEN" in os.environ:
        BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
        print("Using bot token from environment variable")
    
    # Check if username is provided in environment
    if "TELEGRAM_BOT_USERNAME" in os.environ:
        BOT_USERNAME = os.environ["TELEGRAM_BOT_USERNAME"]
        print(f"Using bot username from environment: {BOT_USERNAME}")
        
    # Portal API configuration is handled in portal_api.py
    # No environment variables needed for Portal API
        
except Exception as e:
    print(f"Error loading environment configuration: {e}")
    traceback.print_exc()
