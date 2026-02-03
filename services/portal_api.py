#!/usr/bin/env python3
"""
Portal API Integration for Telegram Gift Bot

This module provides Portal API integration using aportalsmp library,
with comprehensive authentication token management, rate limiting, 
and error handling according to Portal API documentation.
"""

import os
import sys
import json
import time
import asyncio
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get script directory for cross-platform compatibility
_project_root = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(_project_root) != 'giftschart':
    _project_root = os.path.dirname(_project_root)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Import centralized paths
from config.paths import GIFT_API_RESULTS_LOG, PORTAL_TOKEN_FILE, PORTAL_SESSION_FILE

# Set up detailed logging for API results
api_logger = logging.getLogger("gift_api_results")
api_logger.setLevel(logging.INFO)
api_log_handler = logging.FileHandler(GIFT_API_RESULTS_LOG)
api_log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == api_log_handler.baseFilename for h in api_logger.handlers):
    api_logger.addHandler(api_log_handler)

# Configure main logger
logger = logging.getLogger(__name__)

# Legacy API endpoints for fallback
GIFTS_API = "https://giftcharts-api.onrender.com/gifts"
CHART_API = "https://giftcharts-api.onrender.com/weekChart?name="

# Portal API credentials - loaded from environment
API_ID = os.getenv("PORTAL_API_ID", "")
API_HASH = os.getenv("PORTAL_API_HASH", "")


# Portal API token management
PORTAL_SESSION_STRING_FILE = PORTAL_SESSION_FILE
_portal_auth_token = None
_token_last_refreshed = 0
TOKEN_REFRESH_INTERVAL = 1920  # 32 minutes in seconds

# Rate limiting management
_last_request_time = 0
MIN_REQUEST_INTERVAL = 0.5  # 500ms between requests
_rate_limit_until = 0  # Timestamp until which we should wait due to rate limiting

# Try to import Portal API library
try:
    from aportalsmp.gifts import search as portal_search
    from aportalsmp.auth import update_auth
    from aportalsmp.classes.Exceptions import requestError, authDataError
    PORTAL_API_AVAILABLE = True
    logger.info("Portal API (aportalsmp) loaded successfully")
except ImportError as e:
    PORTAL_API_AVAILABLE = False
    logger.error(f"Portal API (aportalsmp) not available: {e}")
    logger.error("Please install with: pip install aportalsmp")

# Supply data cache for legacy API
_supply_data_cache = {}
_cache_timestamp = 0
CACHE_DURATION = 10 * 60  # 10 minutes

async def load_stored_token() -> Optional[str]:
    """Load Portal API token from file if available."""
    try:
        if os.path.exists(PORTAL_TOKEN_FILE):
            with open(PORTAL_TOKEN_FILE, 'r') as f:
                token = f.read().strip()
                if token:
                    api_logger.info("[Portal Auth] Loaded stored authentication token")
                    return token
    except Exception as e:
        api_logger.warning(f"[Portal Auth] Failed to load stored token: {e}")
    return None

async def save_token(token: str) -> None:
    """Save Portal API token to file."""
    try:
        with open(PORTAL_TOKEN_FILE, 'w') as f:
            f.write(token)
        api_logger.info("[Portal Auth] Authentication token saved to file")
    except Exception as e:
        api_logger.error(f"[Portal Auth] Failed to save token: {e}")

async def load_session_string() -> Optional[str]:
    """Load Portal API session string from file if available."""
    try:
        if os.path.exists(PORTAL_SESSION_STRING_FILE):
            with open(PORTAL_SESSION_STRING_FILE, 'r') as f:
                session_string = f.read().strip()
                if session_string:
                    api_logger.info("[Portal Auth] Loaded stored session string")
                    return session_string
    except Exception as e:
        api_logger.warning(f"[Portal Auth] Failed to load session string: {e}")
    return None

async def get_fresh_auth_token() -> str:
    """Get a fresh authentication token from Portal API."""
    global _portal_auth_token, _token_last_refreshed
    
    try:
        api_logger.info("[Portal Auth] Requesting fresh authentication token...")
        
        # First, try using session string if available (avoids interactive auth)
        session_string = await load_session_string()
        if session_string:
            try:
                api_logger.info("[Portal Auth] Attempting to use session string...")
                token = await update_auth(
                    session_string=session_string,
                    session_path=_project_root,
                    session_name="account"
                )
                if token:
                    _portal_auth_token = token
                    _token_last_refreshed = time.time()
                    await save_token(token)
                    api_logger.info("[Portal Auth] Successfully obtained token using session string")
                    return token
            except Exception as e:
                api_logger.warning(f"[Portal Auth] Session string failed: {e}, trying session file...")
        
        # Fallback: try using session file
        try:
            api_logger.info("[Portal Auth] Attempting to use session file...")
            token = await update_auth(
                api_id=API_ID, 
                api_hash=API_HASH,
                session_path=_project_root,
                session_name="account"
            )
            if token:
                _portal_auth_token = token
                _token_last_refreshed = time.time()
                await save_token(token)
                api_logger.info("[Portal Auth] Successfully obtained token using session file")
                return token
        except (EOFError, KeyboardInterrupt) as e:
            # Session file requires interactive authentication - this won't work in non-interactive environments
            error_msg = f"[Portal Auth] Session file requires interactive authentication (EOF): {e}"
            api_logger.error(error_msg)
            api_logger.error("[Portal Auth] To fix this, run: python3 generate_session_string.py")
            api_logger.error("[Portal Auth] This will create a session string file that works in non-interactive environments")
            # Don't raise - let it fall through to use cached token or legacy API
            raise Exception("Session authentication required. Run 'python3 generate_session_string.py' to create a session string.")
        except Exception as e:
            api_logger.error(f"[Portal Auth] Session file authentication failed: {e}")
            raise
        
        raise Exception("Empty token received from update_auth")
            
    except Exception as e:
        api_logger.error(f"[Portal Auth] Failed to get fresh auth token: {e}")
        raise

async def get_auth_token() -> Optional[str]:
    """Get Portal API authentication token with automatic refresh."""
    global _portal_auth_token, _token_last_refreshed
    
    current_time = time.time()
    
    # Check if we need to refresh the token
    if (_portal_auth_token is None or 
        current_time - _token_last_refreshed > TOKEN_REFRESH_INTERVAL):
        # Try to load from file first
        if _portal_auth_token is None:
            _portal_auth_token = await load_stored_token()
            if _portal_auth_token:
                _token_last_refreshed = current_time - TOKEN_REFRESH_INTERVAL + 300  # Give 5 minutes grace
        # If still no token or it's expired, try to get fresh one
        if (_portal_auth_token is None or 
            current_time - _token_last_refreshed > TOKEN_REFRESH_INTERVAL):
            logger.info("[Portal Auth] Token expired or not found, refreshing token now...")
            try:
                _portal_auth_token = await get_fresh_auth_token()
            except Exception as e:
                # If we can't get a fresh token, try to use the cached one if available
                if _portal_auth_token:
                    api_logger.warning(f"[Portal Auth] Failed to refresh token: {e}, using cached token")
                    # Extend the token age slightly to allow using cached token
                    _token_last_refreshed = current_time - TOKEN_REFRESH_INTERVAL + 600  # Give 10 minutes grace
                else:
                    api_logger.error(f"[Portal Auth] No cached token available and refresh failed: {e}")
                    return None
    return _portal_auth_token

async def handle_rate_limiting(delay_seconds: int = 2):
    """Handle rate limiting by waiting and updating global rate limit state."""
    global _rate_limit_until
    
    wait_until = time.time() + delay_seconds
    _rate_limit_until = wait_until
    
    api_logger.warning(f"[Portal API] Rate limited! Waiting {delay_seconds} seconds...")
    await asyncio.sleep(delay_seconds)

async def apply_request_rate_limiting():
    """Apply rate limiting between requests."""
    global _last_request_time, _rate_limit_until
    
    current_time = time.time()
    
    # Check if we're still under rate limit punishment
    if current_time < _rate_limit_until:
        wait_time = _rate_limit_until - current_time
        api_logger.info(f"[Portal API] Still under rate limit, waiting {wait_time:.1f} more seconds")
        await asyncio.sleep(wait_time)
    
    # Apply minimum interval between requests
    time_since_last = current_time - _last_request_time
    if time_since_last < MIN_REQUEST_INTERVAL:
        wait_time = MIN_REQUEST_INTERVAL - time_since_last
        await asyncio.sleep(wait_time)
    
    _last_request_time = time.time()

def parse_portal_error(error_msg: str) -> Dict[str, Any]:
    """Parse Portal API error message to determine error type and appropriate response."""
    error_lower = error_msg.lower()
    
    # Network/DNS errors - these are usually temporary but may require network fix
    if any(keyword in error_lower for keyword in ['could not resolve host', 'dns', 'connection reset', 'connection error', 'name or service not known']):
        return {
            'type': 'network_error',
            'retry_after': 5,  # Wait longer for network issues
            'should_retry': True,
            'is_network_issue': True
        }
    
    # Rate limiting errors
    if any(keyword in error_lower for keyword in ['429', 'rate limit', 'too many requests', 'too many operations']):
        return {
            'type': 'rate_limit',
            'retry_after': 2,  # Default 2 seconds
            'should_retry': True
        }
    
    # Authentication errors
    if any(keyword in error_lower for keyword in ['401', 'unauthorized', 'invalid auth', 'bad token']):
        return {
            'type': 'auth_error', 
            'retry_after': 1,
            'should_retry': True,
            'refresh_token': True
        }
    
    # Temporary server errors
    if any(keyword in error_lower for keyword in ['500', '502', '503', '504', 'server error', 'timeout']):
        return {
            'type': 'server_error',
            'retry_after': 3,
            'should_retry': True
        }
    
    # Permanent errors (400, 404, etc.)
    return {
        'type': 'permanent_error',
        'retry_after': 0,
        'should_retry': False
    }

async def get_supply_from_legacy_api(gift_name: str) -> Any:
    """Get upgradedSupply data from legacy API for a specific gift, robust to case/whitespace mismatches."""
    global _supply_data_cache, _cache_timestamp
    
    try:
        # Check if cache is still valid
        current_time = time.time()
        if current_time - _cache_timestamp > CACHE_DURATION:
            # Refresh cache
            logger.info("Refreshing supply data cache...")
            response = requests.get(GIFTS_API, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Cache all supply data at once
                _supply_data_cache = {}
                for gift in data:
                    name = gift.get("name", "")
                    supply = gift.get("upgradedSupply", 0)
                    if name:
                        _supply_data_cache[name] = supply
                _cache_timestamp = current_time
                logger.info(f"Cached supply data for {len(_supply_data_cache)} gifts")
            else:
                api_logger.error(f"[Supply API] Failed to refresh cache | Status: {response.status_code}")
        
        # Look for gift in cache with robust matching
        norm = lambda s: s.strip().lower().replace(' ', '')
        target = norm(gift_name)
        
        for cached_name, supply in _supply_data_cache.items():
            if norm(cached_name) == target:
                api_logger.info(f"[Supply API] Gift: {gift_name} | Found supply: {supply}")
                return supply
                
        api_logger.warning(f"[Supply API] Gift: {gift_name} | Not found in legacy API gifts list!")
        return "N/A"
        
    except Exception as e:
        api_logger.error(f"[Supply API] Gift: {gift_name} | Exception: {e}")
        return "N/A"

async def fetch_gift_data_with_retry(gift_name: str, max_retries: int = 3, is_premarket: bool = False) -> Optional[Dict[str, Any]]:
    """
    Fetch gift data using Portal API with comprehensive error handling and retry logic.
    
    Args:
        gift_name: Name of the gift to fetch data for
        max_retries: Maximum number of retry attempts
        is_premarket: Whether this is a premarket gift
        
    Returns:
        dict: Gift data with price information or None if not found
    """
    
    for attempt in range(max_retries + 1):
        try:
            # Apply rate limiting
            await apply_request_rate_limiting()
            
            # Get auth token (refreshes automatically if needed)
            auth_token = await get_auth_token()
            
            if not auth_token:
                api_logger.error(f"[Portal API] Gift: {gift_name} | No auth token available, cannot make request")
                # Break out of retry loop and fall back to legacy API
                break
            
            api_logger.info(f"[Portal API] Gift: {gift_name} | Premarket: {is_premarket} | Attempt {attempt + 1}/{max_retries + 1}")
            
            # Make Portal API request (premarket parameter not supported yet)
            results = await portal_search(gift_name=gift_name, authData=auth_token, sort="price_asc", limit=5)
            
            api_logger.info(f"[Portal API] Gift: {gift_name} | Raw results type: {type(results)}")
            
            # Handle Portal API results correctly
            if results and len(results) > 0:
                api_logger.info(f"[Portal API] Gift: {gift_name} | Results count: {len(results)}")
                
                # Get first result and convert to dict safely
                first_result = results[0]
                api_logger.info(f"[Portal API] Gift: {gift_name} | First result type: {type(first_result)}")
                
                # Try different methods to convert to dict
                if hasattr(first_result, '__dict__'):
                    gift = first_result.__dict__
                    api_logger.info(f"[Portal API] Gift: {gift_name} | Using __dict__")
                elif hasattr(first_result, 'to_dict'):
                    gift = first_result.to_dict()
                    api_logger.info(f"[Portal API] Gift: {gift_name} | Using to_dict()")
                elif hasattr(first_result, 'toDict'):
                    gift = first_result.toDict()
                    api_logger.info(f"[Portal API] Gift: {gift_name} | Using toDict()")
                elif isinstance(first_result, dict):
                    gift = first_result
                    api_logger.info(f"[Portal API] Gift: {gift_name} | Already dict")
                else:
                    # Last resort - try to extract basic info
                    gift = {"name": str(first_result), "price": 0}
                    api_logger.warning(f"[Portal API] Gift: {gift_name} | Using fallback dict creation")
                
                api_logger.info(f"[Portal API] Gift: {gift_name} | Selected: {json.dumps(gift, default=str)}")
                
                # Ensure price is properly cast to float
                price_val = float(gift.get("price", 0))
                
                # Portal API doesn't provide supply data, so we need to get it from legacy API
                supply_data = await get_supply_from_legacy_api(gift_name)
                
                # Get real TON price from CoinMarketCap
                try:
                    from ton_price_utils import get_ton_price_usd
                    ton_price_usd = get_ton_price_usd()
                except ImportError:
                    ton_price_usd = 2.10  # Fallback value
                
                return {
                    "name": gift.get("name"),
                    "priceUsd": price_val * ton_price_usd,
                    "priceTon": price_val,
                    "changePercentage": 0,  # Not available from Portal API
                    "model": gift.get("model", ""),
                    "backdrop": gift.get("backdrop", ""),
                    "symbol": gift.get("symbol", ""),
                    "upgradedSupply": supply_data if isinstance(supply_data, (int, float)) else "N/A"
                }
            else:
                api_logger.warning(f"[Portal API] Gift: {gift_name} | No results found")
                # No results found - this is not an error, return None
                return None
                
        except Exception as e:
            error_msg = str(e)
            api_logger.error(f"[Portal API] Gift: {gift_name} | Attempt {attempt + 1} Exception: {error_msg}")
            
            # Parse error type
            error_info = parse_portal_error(error_msg)
            
            if error_info['should_retry'] and attempt < max_retries:
                # Handle specific error types
                if error_info['type'] == 'network_error':
                    api_logger.warning(f"[Portal API] Gift: {gift_name} | Network/DNS error detected")
                    api_logger.warning(f"[Portal API] Gift: {gift_name} | This may indicate 'portals-market.com' cannot be resolved")
                    api_logger.warning(f"[Portal API] Gift: {gift_name} | Waiting {error_info['retry_after']} seconds before retry...")
                    await asyncio.sleep(error_info['retry_after'])
                
                elif error_info['type'] == 'rate_limit':
                    api_logger.warning(f"[Portal API] Gift: {gift_name} | Rate limited, waiting {error_info['retry_after']} seconds")
                    await handle_rate_limiting(error_info['retry_after'])
                
                elif error_info['type'] == 'auth_error':
                    api_logger.warning(f"[Portal API] Gift: {gift_name} | Auth error, refreshing token")
                    # Force token refresh
                    global _portal_auth_token, _token_last_refreshed
                    _portal_auth_token = None
                    _token_last_refreshed = 0
                    await asyncio.sleep(error_info['retry_after'])
                
                elif error_info['type'] == 'server_error':
                    api_logger.warning(f"[Portal API] Gift: {gift_name} | Server error, waiting {error_info['retry_after']} seconds")
                    await asyncio.sleep(error_info['retry_after'])
                
                # Continue to next attempt
                continue
            else:
                # Either permanent error or max retries reached
                api_logger.error(f"[Portal API] Gift: {gift_name} | Giving up after {attempt + 1} attempts")
                break
    
    # All retries failed, fallback to legacy API
    api_logger.info(f"[Portal API] Gift: {gift_name} | All attempts failed, falling back to legacy API")
    return await _fetch_from_legacy_api(gift_name)

async def fetch_gift_data(gift_name: str, is_premarket: bool = False) -> Optional[Dict[str, Any]]:
    """
    Fetch gift data using Portal API, with auth refresh and cache fallback.
    
    Args:
        gift_name: Name of the gift to fetch data for
        is_premarket: Whether this is a premarket gift
        
    Returns:
        dict: Gift data with price information or None if not found
    """
    if not PORTAL_API_AVAILABLE:
        logger.warning("Portal API not available, falling back to legacy API")
        return await _fetch_from_legacy_api(gift_name)
    
    return await fetch_gift_data_with_retry(gift_name, is_premarket=is_premarket)

async def _fetch_from_legacy_api(gift_name: str) -> Optional[Dict[str, Any]]:
    """Fetch gift data from legacy API as fallback."""
    try:
        response = requests.get(GIFTS_API, timeout=10)
        api_logger.info(f"[Legacy API] Gift: {gift_name} | Status: {response.status_code} | Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            for gift in data:
                if gift["name"] == gift_name:
                    # Ensure upgradedSupply is properly extracted from the legacy API
                    upgraded_supply = gift.get("upgradedSupply", 0)
                    api_logger.info(f"[Legacy API] Gift: {gift_name} | Selected: {json.dumps(gift, default=str)}")
                    return gift
            api_logger.warning(f"[Legacy API] Gift: {gift_name} | Not found in response data.")
        else:
            api_logger.error(f"[Legacy API] Gift: {gift_name} | HTTP {response.status_code}")
            
    except Exception as e:
        api_logger.error(f"[Legacy API] Gift: {gift_name} | Exception: {e}")
        logger.error(f"Error fetching gift data for {gift_name} from legacy API: {e}")
    
    # Premarket mock handling disabled: all these gifts are now regular market
    
    # Final fallback - return None if all APIs fail
    api_logger.error(f"[FINAL FALLBACK] Gift: {gift_name} | All APIs failed, returning None")
    return None

async def fetch_chart_data(gift_name: str) -> Optional[list]:
    """
    Fetch chart data for a gift, using legacy API as Portal doesn't provide chart data.
    
    Args:
        gift_name: Name of the gift to fetch chart data for
        
    Returns:
        list: Chart data points or mock data if not available
    """
    try:
        # Portal API doesn't provide chart data, so use legacy API
        from urllib.parse import quote
        encoded_name = quote(gift_name)
        url = f"{CHART_API}{encoded_name}"
        
        response = requests.get(url, timeout=10)
        api_logger.info(f"[Chart API] Gift: {gift_name} | Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if len(data) >= 24:
                return data[-24:]  # Return last 24 data points
            elif len(data) > 0:
                return data
            else:
                return _generate_mock_chart_data(gift_name)
        else:
            api_logger.warning(f"[Chart API] Gift: {gift_name} | HTTP {response.status_code}, using mock data")
            return _generate_mock_chart_data(gift_name)
            
    except Exception as e:
        api_logger.error(f"[Chart API] Gift: {gift_name} | Exception: {e}")
        logger.error(f"Error fetching chart data for {gift_name}: {e}")
        return _generate_mock_chart_data(gift_name)

def _generate_mock_gift_data(gift_name: str) -> Dict[str, Any]:
    """Generate realistic mock gift data for new premarket gifts."""
    # Generate deterministic but varied pricing based on gift name
    base_price = (hash(gift_name) % 500 + 100) / 100  # 1.00 to 6.00 TON
    # Get real TON price from CoinMarketCap
    try:
        from ton_price_utils import get_ton_price_usd
        ton_price_usd = get_ton_price_usd()
    except ImportError:
        ton_price_usd = 2.10  # Fallback value
    usd_price = base_price * ton_price_usd
    
    # Generate supply data
    base_supply = (hash(gift_name) % 10000 + 5000)  # 5,000 to 15,000 supply
    
    mock_data = {
        "_id": f"mock_{hash(gift_name)}",
        "name": gift_name,
        "image": gift_name.lower().replace(" ", ""),
        "supply": base_supply,
        "initSupply": base_supply + 1000,
        "releaseDate": "09-09-2024",
        "starsPrice": 25,
        "upgradePrice": 25,
        "initTonPrice": base_price * 0.8,
        "initUsdPrice": usd_price * 0.8,
        "upgradedSupply": base_supply - 500,
        "tonPrice24hAgo": base_price * 0.95,
        "usdPrice24hAgo": usd_price * 0.95,
        "tonPriceWeekAgo": base_price * 0.9,
        "usdPriceWeekAgo": usd_price * 0.9,
        "tonPriceMonthAgo": base_price * 0.85,
        "usdPriceMonthAgo": usd_price * 0.85,
        "priceTon": base_price,
        "priceUsd": usd_price
    }
    
    api_logger.info(f"[Mock Data] Gift: {gift_name} | Generated mock data: {base_price:.2f} TON, {usd_price:.2f} USD")
    return mock_data

def _generate_mock_chart_data(gift_name: str) -> list:
    """Generate realistic mock chart data for a gift."""
    # Generate 24 data points with some variation
    base_value = hash(gift_name) % 1000 + 500  # Deterministic but varied base
    data_points = []
    
    # Get real TON price from CoinMarketCap (once, outside the loop for efficiency)
    try:
        from ton_price_utils import get_ton_price_usd
        ton_price_usd = get_ton_price_usd()
    except ImportError:
        ton_price_usd = 2.10  # Fallback value
    
    for i in range(24):
        # Add some realistic price movement
        variation = (hash(f"{gift_name}_{i}") % 200 - 100) / 10  # ±10% variation
        value = max(1, base_value + variation)
        usd_value = value * ton_price_usd
        
        # Generate time string for the chart
        import datetime
        time_obj = datetime.datetime.now() - datetime.timedelta(hours=24-i)
        time_str = time_obj.strftime("%H:%M")
        
        data_points.append({
            "price": value, 
            "priceUsd": usd_value,
            "timestamp": int(time.time()) - (24-i) * 3600,
            "time": time_str
        })
    
    api_logger.info(f"[Mock Data] Gift: {gift_name} | Generated {len(data_points)} chart points")
    return data_points

def calculate_percentage_change(chart_data: list) -> float:
    """Calculate percentage change from chart data."""
    if not chart_data or len(chart_data) < 2:
        return 0.0
    
    try:
        # Get first and last prices (try both "price" and "priceUsd" fields)
        first_price = float(chart_data[0].get("price", chart_data[0].get("priceUsd", 0)))
        last_price = float(chart_data[-1].get("price", chart_data[-1].get("priceUsd", 0)))
        
        if first_price == 0:
            return 0.0
            
        change_pct = ((last_price - first_price) / first_price) * 100
        return round(change_pct, 2)
        
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error calculating percentage change: {e}")
        return 0.0

# Initialize the module
def initialize_portal_api():
    """Initialize Portal API module."""
    logger.info("Portal API module initialized")
    if PORTAL_API_AVAILABLE:
        logger.info("Portal API ready for use")
    else:
        logger.warning("Portal API not available, legacy fallback only")

# Auto-initialize when module is imported
initialize_portal_api()

# Market Auth Token Management Functions
async def create_market_auth_token() -> Dict[str, Any]:
    """
    Create a market authentication token in the format expected by the Portal marketplace.
    
    Returns:
        dict: Token data including token string, isFirstTime flag, and other metadata
    """
    try:
        # Get fresh Portal API authentication
        portal_auth = await get_auth_token()
        
        # Generate a market-specific token (this is the format the user mentioned)
        import uuid
        market_token = str(uuid.uuid4())
        
        # Create token data structure
        token_data = {
            "token": market_token,
            "isFirstTime": False,
            "giftId": None,
            "stickerId": None,
            "portalAuth": portal_auth,
            "timestamp": int(time.time()),
            "valid_until": int(time.time()) + TOKEN_REFRESH_INTERVAL
        }
        
        api_logger.info(f"[Market Auth] Created market token: {market_token[:8]}...")
        return token_data
        
    except Exception as e:
        api_logger.error(f"[Market Auth] Failed to create market token: {e}")
        raise

async def refresh_market_auth_token() -> Dict[str, Any]:
    """
    Refresh the market authentication token and underlying Portal auth.
    
    Returns:
        dict: Refreshed token data
    """
    try:
        # Force refresh of Portal auth token
        global _portal_auth_token, _token_last_refreshed
        _portal_auth_token = None
        _token_last_refreshed = 0
        
        # Create new market token
        return await create_market_auth_token()
        
    except Exception as e:
        api_logger.error(f"[Market Auth] Failed to refresh market token: {e}")
        raise

async def get_market_auth_token(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get market authentication token, creating or refreshing as needed.
    
    Args:
        force_refresh: Force creation of a new token
        
    Returns:
        dict: Market token data
    """
    static_token = getattr(get_market_auth_token, '_cached_token', None)
    
    # Check if we need to create/refresh token
    if (force_refresh or 
        static_token is None or 
        time.time() > static_token.get('valid_until', 0)):
        
        if force_refresh:
            api_logger.info("[Market Auth] Force refreshing market token")
            static_token = await refresh_market_auth_token()
        else:
            api_logger.info("[Market Auth] Creating new market token")
            static_token = await create_market_auth_token()
        
        # Cache the token
        get_market_auth_token._cached_token = static_token
    
    return static_token

# Utility functions for token validation and management
def is_token_valid(token_data: Dict[str, Any]) -> bool:
    """Check if a token is still valid based on timestamp."""
    if not token_data or 'valid_until' not in token_data:
        return False
    return time.time() < token_data['valid_until']

def get_token_ttl(token_data: Dict[str, Any]) -> int:
    """Get time-to-live for a token in seconds."""
    if not token_data or 'valid_until' not in token_data:
        return 0
    return max(0, int(token_data['valid_until'] - time.time()))

async def validate_and_refresh_portal_connection():
    """
    Validate Portal API connection and refresh if necessary.
    This function can be called periodically to ensure connection health.
    """
    try:
        api_logger.info("[Portal Validation] Testing Portal API connection...")
        
        # Try a simple search to validate connection
        auth_token = await get_auth_token()
        test_results = await portal_search(gift_name="gift", authData=auth_token, limit=1)
        
        api_logger.info("[Portal Validation] Portal API connection is healthy")
        return True
        
    except Exception as e:
        error_msg = str(e)
        error_info = parse_portal_error(error_msg)
        
        if error_info['type'] == 'auth_error':
            api_logger.warning("[Portal Validation] Auth error detected, refreshing token...")
            try:
                # Force token refresh
                global _portal_auth_token, _token_last_refreshed
                _portal_auth_token = None
                _token_last_refreshed = 0
                await get_fresh_auth_token()
                api_logger.info("[Portal Validation] Token refreshed successfully")
                return True
            except Exception as refresh_e:
                api_logger.error(f"[Portal Validation] Failed to refresh token: {refresh_e}")
                return False
        else:
            api_logger.error(f"[Portal Validation] Connection test failed: {error_msg}")
            return False

# Enhanced logging function for debugging
async def log_portal_api_status():
    """Log current Portal API status for debugging."""
    try:
        global _portal_auth_token, _token_last_refreshed, _rate_limit_until
        
        current_time = time.time()
        token_age = current_time - _token_last_refreshed if _token_last_refreshed > 0 else "Never"
        rate_limit_remaining = max(0, _rate_limit_until - current_time) if _rate_limit_until > 0 else 0
        
        status_info = {
            "portal_api_available": PORTAL_API_AVAILABLE,
            "has_auth_token": _portal_auth_token is not None,
            "token_age_seconds": token_age,
            "rate_limit_remaining_seconds": rate_limit_remaining,
            "supply_cache_entries": len(_supply_data_cache),
            "cache_age_seconds": current_time - _cache_timestamp if _cache_timestamp > 0 else "Never"
        }
        
        api_logger.info(f"[Portal Status] {json.dumps(status_info, default=str)}")
        return status_info
        
    except Exception as e:
        api_logger.error(f"[Portal Status] Failed to get status: {e}")
        return {"error": str(e)} 