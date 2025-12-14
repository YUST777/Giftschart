"""
Centralized Path Configuration for GiftsChart Project

All paths are defined relative to PROJECT_ROOT to enable proper folder structure.
Import paths from this module instead of using os.path.dirname(__file__).
"""

import os

# Project root directory (one level up from config/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =============================================================================
# Data Directories
# =============================================================================
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

# =============================================================================
# Asset Directories
# =============================================================================
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
DOWNLOADED_IMAGES_DIR = os.path.join(PROJECT_ROOT, "downloaded_images")
PREGENERATED_BACKGROUNDS_DIR = os.path.join(PROJECT_ROOT, "pregenerated_backgrounds")

# =============================================================================
# Card Generation Directories
# =============================================================================
CARD_TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "card_templates")
CARD_METADATA_DIR = os.path.join(PROJECT_ROOT, "card_metadata")
GIFT_CARDS_DIR = os.path.join(PROJECT_ROOT, "new_gift_cards")
NEW_GIFT_CARDS_DIR = GIFT_CARDS_DIR

# =============================================================================
# Sticker Directories
# =============================================================================
STICKER_COLLECTIONS_DIR = os.path.join(PROJECT_ROOT, "sticker_collections")
STICKER_METADATA_DIR = os.path.join(PROJECT_ROOT, "sticker_metadata")
STICKER_PRICES_DIR = os.path.join(PROJECT_ROOT, "sticker_prices")
STICKER_PRICE_CARDS_DIR = os.path.join(PROJECT_ROOT, "Sticker_Price_Cards")

# =============================================================================
# Database Files
# =============================================================================
SQLITE_DATA_DIR = os.path.join(PROJECT_ROOT, "sqlite_data")
PREMIUM_DB_FILE = os.path.join(SQLITE_DATA_DIR, "premium_system.db")
USER_REQUESTS_DB_FILE = os.path.join(SQLITE_DATA_DIR, "user_requests.db")
ANALYTICS_DB_FILE = os.path.join(SQLITE_DATA_DIR, "analytics.db")
HISTORICAL_PRICES_DB_FILE = os.path.join(SQLITE_DATA_DIR, "historical_prices.db")

# =============================================================================
# Config and Auth Files
# =============================================================================
ENV_FILE = os.path.join(PROJECT_ROOT, ".env")
PORTAL_TOKEN_FILE = os.path.join(PROJECT_ROOT, "portal_auth_token.txt")
PORTAL_SESSION_FILE = os.path.join(PROJECT_ROOT, "portal_session_string.txt")
ACCOUNT_SESSION_FILE = os.path.join(PROJECT_ROOT, "account.session")

# =============================================================================
# Cache/Result Files
# =============================================================================
STICKER_PRICE_RESULTS_FILE = os.path.join(CACHE_DIR, "sticker_price_results.json")
ALL_STATS_FILE = os.path.join(CACHE_DIR, "all_stats.json")
STATS_FILE = os.path.join(CACHE_DIR, "stats.json")
MRKT_COLLECTIONS_FILE = os.path.join(CACHE_DIR, "full_mrkt_collections.json")

# =============================================================================
# Font Files
# =============================================================================
MAIN_FONT_PATH = os.path.join(FONTS_DIR, "Typekiln - EloquiaDisplay-ExtraBold.otf")

# =============================================================================
# Log Files
# =============================================================================
TELEGRAM_BOT_LOG = os.path.join(LOGS_DIR, "telegram_bot.log")
PREGENERATE_CARDS_LOG = os.path.join(LOGS_DIR, "pregenerate_cards.log")
GIFT_API_RESULTS_LOG = os.path.join(LOGS_DIR, "gift_api_results.log")

# =============================================================================
# Timestamp Files
# =============================================================================
LAST_GENERATION_TIME_FILE = os.path.join(DATA_DIR, "last_generation_time.txt")

# =============================================================================
# API Directory
# =============================================================================
API_DIR = os.path.join(PROJECT_ROOT, "api")
MRKT_API_DIR = os.path.join(API_DIR, "mrkt")

# =============================================================================
# Helper function for legacy compatibility
# =============================================================================
def get_project_root():
    """Return the project root directory."""
    return PROJECT_ROOT

# Ensure required directories exist
def ensure_directories():
    """Create all required directories if they don't exist."""
    dirs = [
        DATA_DIR, CACHE_DIR, LOGS_DIR, ASSETS_DIR, FONTS_DIR,
        CARD_TEMPLATES_DIR, CARD_METADATA_DIR, GIFT_CARDS_DIR,
        STICKER_COLLECTIONS_DIR, STICKER_METADATA_DIR, STICKER_PRICES_DIR,
        STICKER_PRICE_CARDS_DIR, SQLITE_DATA_DIR, DOWNLOADED_IMAGES_DIR,
        PREGENERATED_BACKGROUNDS_DIR
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Create directories on import
ensure_directories()
