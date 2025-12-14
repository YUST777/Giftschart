import logging
import asyncio
from typing import Optional, Dict, Any, List
try:
    import tonnelmp  # Optional: only used when available
    TONNEL_AVAILABLE = True
except Exception:
    tonnelmp = None
    TONNEL_AVAILABLE = False
import time
import os
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Legacy API endpoints for chart and supply data
LEGACY_GIFTS_API = "https://giftcharts-api.onrender.com/gifts"
LEGACY_CHART_API = "https://giftcharts-api.onrender.com/weekChart?name="

# Auth data provided by user
AUTH_DATA = "user=%7B%22id%22%3A800092886%2C%22first_name%22%3A%22yousef%22%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22yousefmsm1%22%2C%22language_code%22%3A%22en%22%2C%22is_premium%22%3Atrue%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FvW4ZMqGc0pJ1sAO-BL4aeGmw-htmCoB9KpXawTUm5Hc.svg%22%7D&chat_instance=2929340433951865428&chat_type=sender&auth_date=1749783179&signature=va4HJiOi5NBEnL56xNrMpzROa7UqVR1BNM9pzupjj0t6t4DKlKpuddnWkJJDU-3DrGZnHnLEoY6cX-EzoYriDw&hash=c4efb47fd0ac6286ef004aabfbf4da92963ac854fed79b867186ff99fd1a3f43"

# Premarket gifts mapping
# Key: filename/internal name, Value: API name
PREMARKET_GIFTS = {
    # New premarket gifts (2025 releases)
    "Happy_Brownie": "Happy Brownie",      # 1.97 TON
    "Spring_Basket": "Spring Basket",      # 2.75 TON
    "Instant_Ramen": "Instant Ramen",      # 1.29 TON
    "Faith_Amulet": "Faith Amulet",        # 1.60 TON
    "Mousse_Cake": "Mousse Cake",          # 2.30 TON
    "Ice_Cream": "Ice Cream",              # 1.30 TON
    # Premarket gifts that transition to market after 21 days
    "Bling_Binky": "Bling Binky",
    "Money_Pot": "Money Pot",
    "Pretty_Posy": "Pretty Posy"
}

# Supply data cache
_supply_cache = {}
_supply_cache_timestamp = 0
SUPPLY_CACHE_DURATION = 10 * 60  # 10 minutes

# Chart data cache
_chart_cache = {}
_chart_cache_expiry = {}
CHART_CACHE_DURATION = 5 * 60  # 5 minutes

# Rate limiting
last_request_time = 0
MIN_REQUEST_INTERVAL = 2.0  # Increased to 2 seconds between requests

# Short-term caching (for immediate repeated requests)
_gift_cache = {}
_cache_expiry = {}
CACHE_DURATION = 10 * 60  # 10 minutes

# Cache clearing functions
def clear_all_caches():
    """Clear all price caches to force fresh API calls."""
    global _gift_cache, _cache_expiry, _supply_cache, _chart_cache, _chart_cache_expiry
    _gift_cache.clear()
    _cache_expiry.clear()
    _supply_cache.clear()
    _chart_cache.clear()
    _chart_cache_expiry.clear()
    logger.info("🧹 CLEARED: All caches cleared to force fresh API calls")

def clear_price_cache():
    """Clear only the price cache."""
    global _gift_cache, _cache_expiry
    _gift_cache.clear()
    _cache_expiry.clear()
    logger.info("🧹 CLEARED: Price cache cleared")

# Historical price database setup
script_dir = os.path.dirname(os.path.abspath(__file__))
PRICE_DB_FILE = os.path.join(script_dir, "sqlite_data", "historical_prices.db")

def get_legacy_supply_data(gift_name: str) -> Any:
    """Get supply data from Legacy API (kept for compatibility)."""
    global _supply_cache, _supply_cache_timestamp
    
    try:
        # Check if cache is still valid
        current_time = time.time()
        if current_time - _supply_cache_timestamp > SUPPLY_CACHE_DURATION:
            # Refresh cache
            logger.info("🔄 Refreshing premarket supply data cache...")
            response = requests.get(LEGACY_GIFTS_API, timeout=15)
            if response.status_code == 200:
                data = response.json()
                # Cache all supply data at once
                _supply_cache = {}
                for gift in data:
                    name = gift.get("name", "")
                    supply = gift.get("upgradedSupply", 0)
                    if name:
                        _supply_cache[name] = supply
                _supply_cache_timestamp = current_time
                logger.info(f"📊 Cached supply data for {len(_supply_cache)} gifts")
            else:
                logger.error(f"❌ Failed to refresh supply cache | Status: {response.status_code}")
        
        # Direct lookup by provided gift_name
        if gift_name in _supply_cache:
            supply = _supply_cache[gift_name]
            logger.info(f"📦 Supply for {gift_name}: {supply} pieces")
            return supply
        
        # Fuzzy matching as fallback
        norm = lambda s: s.strip().lower().replace(' ', '')
        target = norm(gift_name)
        
        for cached_name, supply in _supply_cache.items():
            if norm(cached_name) == target:
                logger.info(f"📦 Supply for {gift_name} (fuzzy match): {supply} pieces")
                return supply
                
        logger.warning(f"⚠️ Supply for {gift_name} not found in legacy API!")
        return "N/A"
        
    except Exception as e:
        logger.error(f"❌ Error fetching supply for {gift_name}: {e}")
        return "N/A"

def get_legacy_chart_data(gift_name: str) -> List[Dict]:
    """Get chart data from Legacy API for a specific premarket gift."""
    try:
        # Check cache first
        if gift_name in _chart_cache and gift_name in _chart_cache_expiry:
            if time.time() < _chart_cache_expiry[gift_name]:
                logger.info(f"⚡ Using cached chart data for {gift_name}")
                return _chart_cache[gift_name]
            else:
                # Cache expired
                del _chart_cache[gift_name]
                del _chart_cache_expiry[gift_name]
        
        # Apply rate limiting
        apply_rate_limiting()
        
        # Fetch chart data from Legacy API
        encoded_name = quote(gift_name)
        url = f"{LEGACY_CHART_API}{encoded_name}"
        
        logger.info(f"📈 Fetching chart data for {gift_name} from Legacy API...")
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Get the last 24 data points (24 hours) or all if less
                chart_data = data[-24:] if len(data) >= 24 else data
                
                # Cache the data
                _chart_cache[gift_name] = chart_data
                _chart_cache_expiry[gift_name] = time.time() + CHART_CACHE_DURATION
                
                logger.info(f"✅ Retrieved {len(chart_data)} chart points for {gift_name}")
                return chart_data
            else:
                logger.warning(f"⚠️ No chart data available for {gift_name}")
                return []
        else:
            logger.error(f"❌ Chart API error for {gift_name} | Status: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"❌ Error fetching chart data for {gift_name}: {e}")
        return []

def calculate_premarket_percentage_change(chart_data: List[Dict]) -> float:
    """Calculate percentage change from chart data (legacy format)."""
    try:
        if not chart_data or len(chart_data) < 2:
            return 0.0
            
        # Get first and last price points
        start_price = float(chart_data[0].get("priceUsd", 0))
        end_price = float(chart_data[-1].get("priceUsd", 0))
        
        if start_price > 0:
            change_percent = ((end_price - start_price) / start_price) * 100
            logger.info(f"📊 Price change: ${start_price:.2f} → ${end_price:.2f} ({change_percent:+.2f}%)")
            return change_percent
        else:
            return 0.0
            
    except Exception as e:
        logger.error(f"❌ Error calculating percentage change: {e}")
        return 0.0

def init_price_database():
    """Initialize the historical price database."""
    # Ensure sqlite_data directory exists
    os.makedirs(os.path.dirname(PRICE_DB_FILE), exist_ok=True)
    
    conn = sqlite3.connect(PRICE_DB_FILE)
    cursor = conn.cursor()
    
    # Create table for historical prices (simplified schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gift_name TEXT NOT NULL,
            price_ton REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            success_count INTEGER DEFAULT 1
        )
    ''')
    
    # Create index for faster lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_gift_timestamp ON price_history(gift_name, timestamp DESC)')
    
    conn.commit()
    conn.close()

def store_successful_price(gift_name: str, price_ton: float, source: str):
    """Store a successful price fetch in the historical database."""
    try:
        conn = sqlite3.connect(PRICE_DB_FILE)
        cursor = conn.cursor()
        
        # Check if we already have a price for today for this gift
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT id FROM price_history 
            WHERE gift_name = ? AND DATE(timestamp) = ? 
            LIMIT 1
        ''', (gift_name, today))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing entry
            cursor.execute('''
                UPDATE price_history 
                SET price_ton = ?, source = ?, timestamp = ?, success_count = success_count + 1
                WHERE id = ?
            ''', (price_ton, source, datetime.now().isoformat(), existing[0]))
        else:
            # Insert new entry
            cursor.execute('''
                INSERT INTO price_history (gift_name, price_ton, source, timestamp) 
                VALUES (?, ?, ?, ?)
            ''', (gift_name, price_ton, source, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        logger.info(f"💾 Stored price for {gift_name}: {price_ton} TON (source: {source})")
    except Exception as e:
        logger.error(f"Failed to store price history: {e}")

def get_historical_price(gift_name: str, max_age_days: int = 7) -> Optional[float]:
    """Get the most recent historical price for a gift within max_age_days."""
    try:
        conn = sqlite3.connect(PRICE_DB_FILE)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()
        
        cursor.execute('''
            SELECT price_ton, timestamp, source FROM price_history 
            WHERE gift_name = ? AND timestamp > ? 
            ORDER BY timestamp DESC LIMIT 1
        ''', (gift_name, cutoff_date))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            price, timestamp, source = result
            age_hours = (datetime.now() - datetime.fromisoformat(timestamp)).total_seconds() / 3600
            logger.info(f"📚 Using historical price for {gift_name}: {price} TON (age: {age_hours:.1f}h, source: {source})")
            return price
            
        return None
    except Exception as e:
        logger.error(f"Failed to get historical price: {e}")
        return None

def apply_rate_limiting():
    """Apply rate limiting to API requests."""
    global last_request_time
    current_time = time.time()
    time_since_last = current_time - last_request_time
    
    if time_since_last < MIN_REQUEST_INTERVAL:
        sleep_time = MIN_REQUEST_INTERVAL - time_since_last
        time.sleep(sleep_time)
    
    last_request_time = time.time()

def get_cached_price(gift_name: str) -> Optional[float]:
    """Get cached price if available and not expired."""
    if gift_name in _gift_cache and gift_name in _cache_expiry:
        if time.time() < _cache_expiry[gift_name]:
            logger.info(f"⚡ Using cached price for {gift_name}: {_gift_cache[gift_name]} TON")
            return _gift_cache[gift_name]
        else:
            # Cache expired
            del _gift_cache[gift_name]
            del _cache_expiry[gift_name]
    return None

def cache_price(gift_name: str, price: float):
    """Cache a price with expiration."""
    _gift_cache[gift_name] = price
    _cache_expiry[gift_name] = time.time() + CACHE_DURATION

async def get_tonnel_gift_price(gift_name: str, force_fresh: bool = False) -> Optional[float]:
    """
    Get gift price from Tonnel API with multi-strategy approach and historical fallback.
    Returns None only if absolutely no price data is available.
    
    Args:
        gift_name: The gift name to fetch price for
        force_fresh: If True, bypass all caches and force fresh API calls
    """
    start_time = time.time()
    
    # Initialize database if needed
    init_price_database()
    
    # If tonnelmp is unavailable, skip live fetch methods
    if not TONNEL_AVAILABLE:
        logger.warning("tonnelmp module not available; skipping Tonnel live methods")
        if not force_fresh:
            historical = get_historical_price(gift_name, max_age_days=30)
            if historical is not None:
                cache_price(gift_name, historical)
            return historical
        return None

    # Check short-term cache first (only if not forcing fresh)
    if not force_fresh:
        cached_price = get_cached_price(gift_name)
        if cached_price is not None:
            return cached_price
    else:
        logger.info(f"🔥 FORCE FRESH: Bypassing cache for {gift_name}")
    
    # Check if this is a premarket gift and get the correct API name
    is_premarket = gift_name in PREMARKET_GIFTS
    api_gift_name = PREMARKET_GIFTS.get(gift_name, gift_name)
    
    # Strategy 1: No-auth getGifts() (most reliable against CloudFlare)
    try:
        apply_rate_limiting()
        logger.info(f"🔍 METHOD 1: Fetching {api_gift_name} via no-auth getGifts (premarket={is_premarket})...")
        
        gifts = tonnelmp.getGifts(
            gift_name=api_gift_name,
            premarket=is_premarket,
            limit=5,
            sort="price_asc"
        )
        
        if gifts and len(gifts) > 0:
            price = float(gifts[0].get('price', 0))
            if price > 0:
                logger.info(f"✅ METHOD 1 SUCCESS: {api_gift_name} = {price} TON")
                store_successful_price(gift_name, price, "getGifts_premarket" if is_premarket else "getGifts_no_auth")
                if not force_fresh:  # Only cache if not forcing fresh
                    cache_price(gift_name, price)
                return price
        
        logger.warning(f"⚠️ METHOD 1: No valid price found for {api_gift_name}")
        
    except Exception as e:
        if "CloudFlare" in str(e):
            logger.warning(f"☁️ METHOD 1: CloudFlare blocked request for {api_gift_name}")
        else:
            logger.error(f"❌ METHOD 1: Error for {api_gift_name}: {e}")
    
    # Strategy 2: With auth filterStatsPretty() (for floor prices when available)
    # Skip this for premarket gifts as they don't have floor prices
    if not is_premarket:
        try:
            apply_rate_limiting()
            logger.info(f"🔍 METHOD 2: Fetching {api_gift_name} via filterStatsPretty...")
            
            stats = tonnelmp.filterStatsPretty(AUTH_DATA)
            
            if stats and 'status' in stats and stats['status'] == 'success':
                data = stats.get('data', {})
                for gift_key, gift_data in data.items():
                    if api_gift_name.lower() in gift_key.lower():
                        floor_price = gift_data.get('data', {}).get('floorPrice')
                        if floor_price and floor_price > 0:
                            logger.info(f"✅ METHOD 2 SUCCESS: {api_gift_name} = {floor_price} TON (floor)")
                            store_successful_price(gift_name, floor_price, "filterStatsPretty")
                            if not force_fresh:  # Only cache if not forcing fresh
                                cache_price(gift_name, floor_price)
                            return floor_price
            
            logger.warning(f"⚠️ METHOD 2: No floor price found for {api_gift_name}")
                
        except Exception as e:
            if "CloudFlare" in str(e):
                logger.warning(f"☁️ METHOD 2: CloudFlare blocked request for {api_gift_name}")
            else:
                logger.error(f"❌ METHOD 2: Error for {api_gift_name}: {e}")
    else:
        logger.info(f"⏭️ METHOD 2: Skipped for premarket gift {api_gift_name}")
    
    # Skip historical fallbacks when forcing fresh data
    if force_fresh:
        logger.info(f"🔥 FORCE FRESH: Skipping all historical fallbacks for {gift_name}")
        logger.info(f"💥 No fresh price available for {gift_name} after {time.time() - start_time:.2f}s")
        return None
    
    # Strategy 3: Historical price fallback (7 days)
    logger.info(f"🔍 METHOD 3: Checking historical prices for {gift_name}...")
    historical_price = get_historical_price(gift_name, max_age_days=7)
    if historical_price:
        cache_price(gift_name, historical_price)
        return historical_price
    
    # Strategy 4: Extended historical fallback (30 days)
    logger.info(f"🔍 METHOD 4: Checking extended historical prices for {gift_name}...")
    extended_historical = get_historical_price(gift_name, max_age_days=30)
    if extended_historical:
        logger.warning(f"⚠️ Using 30-day old price for {gift_name}: {extended_historical} TON")
        cache_price(gift_name, extended_historical)
        return extended_historical
    
    # Final fallback - log failure
    logger.error(f"💥 ALL METHODS FAILED for {gift_name} after {time.time() - start_time:.2f}s")
    return None

# Export all important functions
__all__ = [
    'get_tonnel_gift_price', 
    'get_legacy_chart_data', 
    'get_legacy_supply_data', 
    'calculate_premarket_percentage_change', 
    'clear_all_caches',
    'clear_price_cache',
    'PREMARKET_GIFTS'
]

if __name__ == "__main__":
    # Test the API
    print("Testing Tonnel API integration...")
    
    # Test fetching specific premarket gift
    test_gift = "SnoopDogg"
    result = asyncio.run(get_tonnel_gift_price(test_gift))
    print(f"\nTest result for {test_gift}:")
    print(f"Price: {result} TON")
    
    # Test chart data
    chart_data = get_legacy_chart_data(test_gift)
    print(f"Chart data points: {len(chart_data)}")
    if chart_data:
        change_percent = calculate_premarket_percentage_change(chart_data)
        print(f"Price change: {change_percent:+.2f}%")
    
    # Test supply data
    supply = get_legacy_supply_data(test_gift)
    print(f"Supply: {supply} pieces") 