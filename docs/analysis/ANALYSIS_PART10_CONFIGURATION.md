# Part 10: Configuration & Environment

## ⚙️ ENVIRONMENT VARIABLES (.env)

### Required Variables:
```bash
# Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_USERNAME=@giftsChartBot

# Portal API (Primary Data Source)
PORTAL_API_ID=22307634
PORTAL_API_HASH=7ab906fc6d065a2047a84411c1697593

# Telethon API (Same as Portal)
TELEGRAM_API_ID=22307634
TELEGRAM_API_HASH=7ab906fc6d065a2047a84411c1697593

# Session Configuration
TELEGRAM_SESSION_NAME=gifts_session
```

### Optional Variables:
```bash
# CDN Configuration
CDN_BASE_URL=https://giftschart.the01studio.xyz/api

# Rate Limiting
REQUESTS_PER_MINUTE=5

# Logging Level
LOG_LEVEL=INFO
```

## 📝 BOT CONFIGURATION (bot_config.py)

### Core Settings:
```python
# Bot Identity
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "@giftsChartBot")

# Behavior
RESPOND_TO_ALL_MESSAGES = True
USE_DIRECT_IP = False
API_TELEGRAM_IP = "149.154.167.220"
SKIP_SSL_VERIFY = False
```

### Special Groups:
```python
SPECIAL_GROUPS = {
    -1002155968676: {
        "buy_sell_link": "https://t.me/Tonnel_Network_bot/gifts?startapp=ref_1251203296",
        "portal_link": "https://t.me/portals/market?startapp=1251203296"
    },
    -1001891015899: {
        "buy_sell_link": "https://t.me/tonnel_network_bot/gifts?startapp=ref_1109811477",
        "portal_link": "https://t.me/portals/market?startapp=1109811477"
    }
}
```

### Default Links:
```python
DEFAULT_BUY_SELL_LINK = "https://t.me/tonnel_network_bot/gifts?startapp=ref_7660176383"
DEFAULT_TONNEL_LINK = "https://t.me/tonnel_network_bot/gifts?startapp=ref_7660176383"
DEFAULT_PALACE_LINK = "https://t.me/palacenftbot/app?startapp=zOyJPdbc9t"
DEFAULT_PORTAL_LINK = "https://t.me/portals/market?startapp=q7iu6i"
DEFAULT_MRKT_LINK = "https://t.me/mrkt/app?startapp=7660176383"
```

### CDN Configuration:
```python
CDN_BASE_URL = "https://giftschart.the01studio.xyz/api"
```

## 📂 PATH CONFIGURATION (config/paths.py)

### Project Structure:
```python
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data Directories
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

# Asset Directories
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
DOWNLOADED_IMAGES_DIR = os.path.join(PROJECT_ROOT, "downloaded_images")

# Card Generation
CARD_TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "card_templates")
CARD_METADATA_DIR = os.path.join(PROJECT_ROOT, "card_metadata")
GIFT_CARDS_DIR = os.path.join(PROJECT_ROOT, "new_gift_cards")

# Sticker Directories
STICKER_COLLECTIONS_DIR = os.path.join(PROJECT_ROOT, "sticker_collections")
STICKER_METADATA_DIR = os.path.join(PROJECT_ROOT, "sticker_metadata")
STICKER_PRICE_CARDS_DIR = os.path.join(PROJECT_ROOT, "Sticker_Price_Cards")

# Database Files
SQLITE_DATA_DIR = os.path.join(PROJECT_ROOT, "sqlite_data")
PREMIUM_DB_FILE = os.path.join(SQLITE_DATA_DIR, "premium_system.db")
USER_REQUESTS_DB_FILE = os.path.join(SQLITE_DATA_DIR, "user_requests.db")

# Auth Files
PORTAL_TOKEN_FILE = os.path.join(PROJECT_ROOT, "portal_auth_token.txt")
PORTAL_SESSION_FILE = os.path.join(PROJECT_ROOT, "portal_session_string.txt")
ACCOUNT_SESSION_FILE = os.path.join(PROJECT_ROOT, "account.session")
```

## 🔧 STARTUP CONFIGURATION (start_bot.py)

### Initialization Sequence:
```python
def main():
    # 1. Check Python version (>= 3.8)
    check_python_version()
    
    # 2. Check dependencies
    check_dependencies()
    
    # 3. Check file structure
    check_file_structure()
    
    # 4. Clean up cache
    cleanup_cache()
    
    # 5. Initialize databases
    initialize_databases()
    
    # 6. Start backup process
    start_backup_process()
    
    # 7. Start bot
    start_bot()
```

### Required Dependencies:
```python
required_packages = [
    'telegram',      # python-telegram-bot
    'PIL',           # Pillow
    'matplotlib',
    'numpy',
    'requests',
    'httpx',
    'yaml',
    'schedule'
]
```
