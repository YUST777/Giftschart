import logging
import asyncio
import time
import random
import json
import sqlite3
import os
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import urllib.parse

# Multiple HTTP libraries for maximum bypass potential
try:
    import curl_cffi.requests as curl_requests
    from curl_cffi.requests import BrowserType
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

import requests
from fake_useragent import UserAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudFlareBypass:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.stats_db = os.path.join(self.script_dir, "sqlite_data", "bypass_stats.db")
        self.ua = UserAgent()
        self.init_stats_db()
        
        # Multiple browser fingerprints for curl_cffi
        self.browser_types = [
            "chrome110", "chrome109", "chrome108", "chrome107",
            "firefox110", "firefox109", "safari15_5", "safari15_3"
        ] if CURL_CFFI_AVAILABLE else []
        
        # Proxy lists (you can add your own proxy services here)
        self.free_proxies = []  # Add free proxies if available
        self.premium_proxies = []  # Add premium proxies for better success rate
        
        # Request timing strategies
        self.timing_strategies = {
            "conservative": (3, 5),  # 3-5 seconds between requests
            "moderate": (1, 3),      # 1-3 seconds
            "aggressive": (0.5, 1),  # 0.5-1 second
            "burst": (0.1, 0.3)      # 0.1-0.3 seconds (risky)
        }
        
        # Success tracking
        self.method_stats = {}
    
    def init_stats_db(self):
        """Initialize database for tracking bypass success rates."""
        os.makedirs(os.path.dirname(self.stats_db), exist_ok=True)
        
        conn = sqlite3.connect(self.stats_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bypass_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                response_code INTEGER,
                response_time REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_attempt(self, method: str, url: str, success: bool, 
                   response_code: int = None, response_time: float = None, 
                   error_message: str = None):
        """Log bypass attempt for statistics."""
        try:
            # Handle None URL for direct API calls
            if url is None:
                url = "direct_api_call"
            
            conn = sqlite3.connect(self.stats_db, timeout=10.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bypass_attempts 
                (method, url, success, response_code, response_time, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (method, url, success, response_code, response_time, error_message))
            
            conn.commit()
            conn.close()
        except Exception as e:
            # Don't spam logs with database errors, just skip logging
            pass
    
    def get_success_rates(self, hours: int = 24) -> Dict[str, float]:
        """Get success rates for each method in the last N hours."""
        try:
            conn = sqlite3.connect(self.stats_db)
            cursor = conn.cursor()
            
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute('''
                SELECT method, 
                       COUNT(*) as total,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes
                FROM bypass_attempts 
                WHERE timestamp > ?
                GROUP BY method
            ''', (cutoff,))
            
            stats = {}
            for method, total, successes in cursor.fetchall():
                stats[method] = (successes / total * 100) if total > 0 else 0
            
            conn.close()
            return stats
        except Exception as e:
            logger.error(f"Failed to get success rates: {e}")
            return {}
    
    def get_random_headers(self) -> Dict[str, str]:
        """Generate randomized headers."""
        return {
            "User-Agent": self.ua.random,
            "Accept": random.choice([
                "application/json, text/plain, */*",
                "application/json",
                "*/*"
            ]),
            "Accept-Language": random.choice([
                "en-US,en;q=0.9",
                "en-GB,en;q=0.9",
                "en-US,en;q=0.5"
            ]),
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Cache-Control": random.choice(["no-cache", "max-age=0"]),
            "Origin": "https://market.tonnel.network",
            "Referer": "https://market.tonnel.network/"
        }
    
    async def method_1_curl_cffi_rotation(self, url: str, payload: dict = None) -> Tuple[bool, Any]:
        """Method 1: curl_cffi with browser rotation."""
        if not CURL_CFFI_AVAILABLE:
            return False, "curl_cffi not available"
        
        method = "curl_cffi_rotation"
        start_time = time.time()
        
        for browser in random.sample(self.browser_types, min(3, len(self.browser_types))):
            try:
                headers = self.get_random_headers()
                
                if payload:
                    response = curl_requests.post(
                        url, 
                        json=payload, 
                        headers=headers,
                        impersonate=browser,
                        timeout=15,
                        allow_redirects=True
                    )
                else:
                    response = curl_requests.get(
                        url,
                        headers=headers,
                        impersonate=browser,
                        timeout=15,
                        allow_redirects=True
                    )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_attempt(f"{method}_{browser}", url, True, 
                                   response.status_code, response_time)
                    return True, response.json()
                elif response.status_code in [403, 429]:
                    self.log_attempt(f"{method}_{browser}", url, False, 
                                   response.status_code, response_time, "CloudFlare blocked")
                    continue
                else:
                    self.log_attempt(f"{method}_{browser}", url, False, 
                                   response.status_code, response_time)
                    continue
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_attempt(f"{method}_{browser}", url, False, 
                               None, response_time, str(e))
                continue
        
        return False, "All curl_cffi browsers failed"
    
    async def method_2_httpx_async(self, url: str, payload: dict = None) -> Tuple[bool, Any]:
        """Method 2: httpx with async support."""
        if not HTTPX_AVAILABLE:
            return False, "httpx not available"
        
        method = "httpx_async"
        start_time = time.time()
        
        try:
            headers = self.get_random_headers()
            
            async with httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers=headers
            ) as client:
                if payload:
                    response = await client.post(url, json=payload)
                else:
                    response = await client.get(url)
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_attempt(method, url, True, 
                                   response.status_code, response_time)
                    return True, response.json()
                else:
                    self.log_attempt(method, url, False, 
                                   response.status_code, response_time)
                    return False, f"Status code: {response.status_code}"
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.log_attempt(method, url, False, None, response_time, str(e))
            return False, str(e)
    
    async def method_3_aiohttp_session(self, url: str, payload: dict = None) -> Tuple[bool, Any]:
        """Method 3: aiohttp with session persistence."""
        if not AIOHTTP_AVAILABLE:
            return False, "aiohttp not available"
        
        method = "aiohttp_session"
        start_time = time.time()
        
        try:
            headers = self.get_random_headers()
            
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=15)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            ) as session:
                if payload:
                    async with session.post(url, json=payload) as response:
                        response_time = time.time() - start_time
                        
                        if response.status == 200:
                            data = await response.json()
                            self.log_attempt(method, url, True, 
                                           response.status, response_time)
                            return True, data
                        else:
                            self.log_attempt(method, url, False, 
                                           response.status, response_time)
                            return False, f"Status code: {response.status}"
                else:
                    async with session.get(url) as response:
                        response_time = time.time() - start_time
                        
                        if response.status == 200:
                            data = await response.json()
                            self.log_attempt(method, url, True, 
                                           response.status, response_time)
                            return True, data
                        else:
                            self.log_attempt(method, url, False, 
                                           response.status, response_time)
                            return False, f"Status code: {response.status}"
                            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_attempt(method, url, False, None, response_time, str(e))
            return False, str(e)
    
    async def method_4_requests_session(self, url: str, payload: dict = None) -> Tuple[bool, Any]:
        """Method 4: Standard requests with session and retries."""
        method = "requests_session"
        start_time = time.time()
        
        try:
            session = requests.Session()
            headers = self.get_random_headers()
            session.headers.update(headers)
            
            # Add retry logic
            for attempt in range(3):
                try:
                    if payload:
                        response = session.post(url, json=payload, timeout=15)
                    else:
                        response = session.get(url, timeout=15)
                    
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        self.log_attempt(f"{method}_attempt_{attempt+1}", url, True, 
                                       response.status_code, response_time)
                        return True, response.json()
                    elif response.status_code in [403, 429]:
                        # Wait longer between CloudFlare blocked attempts
                        if attempt < 2:
                            await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        self.log_attempt(f"{method}_attempt_{attempt+1}", url, False, 
                                       response.status_code, response_time)
                        if attempt < 2:
                            await asyncio.sleep(1)
                        continue
                        
                except requests.exceptions.RequestException as e:
                    response_time = time.time() - start_time
                    self.log_attempt(f"{method}_attempt_{attempt+1}", url, False, 
                                   None, response_time, str(e))
                    if attempt < 2:
                        await asyncio.sleep(1)
                    continue
            
            return False, "All requests attempts failed"
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_attempt(method, url, False, None, response_time, str(e))
            return False, str(e)
    
    async def method_5_tonnelmp_direct(self, gift_name: str) -> Tuple[bool, Any]:
        """Method 5: Direct tonnelmp library calls."""
        method = "tonnelmp_direct"
        start_time = time.time()
        
        try:
            import tonnelmp
            
            # Try getGifts first (no auth)
            gifts = tonnelmp.getGifts(
                gift_name=gift_name,
                premarket=True,
                limit=5,
                sort="price_asc"
            )
            
            response_time = time.time() - start_time
            
            if gifts and len(gifts) > 0:
                price = float(gifts[0].get('price', 0))
                if price > 0:
                    self.log_attempt(f"{method}_getGifts", "tonnelmp_api", True, 
                                   200, response_time)
                    return True, {"price": price, "source": "getGifts"}
            
            self.log_attempt(f"{method}_getGifts", "tonnelmp_api", False, 
                           200, response_time, "No price found")
            return False, "No price in tonnelmp response"
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_attempt(method, "tonnelmp_api", False, None, response_time, str(e))
            return False, str(e)
    
    async def bypass_request(self, url: str, payload: dict = None, 
                           gift_name: str = None) -> Tuple[bool, Any, str]:
        """Execute all bypass methods and return the first successful result."""
        
        # Randomize method order to distribute load
        methods = [
            ("curl_cffi_rotation", self.method_1_curl_cffi_rotation),
            ("httpx_async", self.method_2_httpx_async),
            ("aiohttp_session", self.method_3_aiohttp_session),
            ("requests_session", self.method_4_requests_session),
        ]
        
        # Add tonnelmp method if gift_name provided
        if gift_name:
            methods.append(("tonnelmp_direct", self.method_5_tonnelmp_direct))
        
        # Randomize order
        random.shuffle(methods)
        
        for method_name, method_func in methods:
            try:
                logger.info(f"🔄 Trying {method_name}...")
                
                if method_name == "tonnelmp_direct" and gift_name:
                    success, result = await method_func(gift_name)
                else:
                    success, result = await method_func(url, payload)
                
                if success:
                    logger.info(f"✅ {method_name} succeeded!")
                    return True, result, method_name
                else:
                    logger.warning(f"⚠️ {method_name} failed: {result}")
                
                # Add delay between methods to avoid rate limiting
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                logger.error(f"❌ {method_name} crashed: {e}")
                continue
        
        return False, "All bypass methods failed", "none"

# Integration with existing tonnel_api.py
class AdvancedTonnelAPI:
    def __init__(self):
        self.bypass = CloudFlareBypass()
        self.auth_data = "user=%7B%22id%22%3A800092886%2C%22first_name%22%3A%22yousef%22%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22yousefmsm1%22%2C%22language_code%22%3A%22en%22%2C%22is_premium%22%3Atrue%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FvW4ZMqGc0pJ1sAO-BL4aeGmw-htmCoB9KpXawTUm5Hc.svg%22%7D&chat_instance=2929340433951865428&chat_type=sender&auth_date=1749783179&signature=va4HJiOi5NBEnL56xNrMpzROa7UqVR1BNM9pzupjj0t6t4DKlKpuddnWkJJDU-3DrGZnHnLEoY6cX-EzoYriDw&hash=c4efb47fd0ac6286ef004aabfbf4da92963ac854fed79b867186ff99fd1a3f43"
        
        # Premarket gifts mapping
        self.premarket_gifts = {
            # New premarket gifts (2025 releases)
            "Happy_Brownie": "Happy Brownie",
            "Spring_Basket": "Spring Basket",
            "Instant_Ramen": "Instant Ramen",
            "Faith_Amulet": "Faith Amulet",
            "Mousse_Cake": "Mousse Cake",
            "Ice_Cream": "Ice Cream"
        }
    
    async def get_gift_price_advanced(self, gift_name: str) -> Optional[float]:
        """Get gift price using advanced CloudFlare bypass."""
        
        api_gift_name = self.premarket_gifts.get(gift_name)
        if not api_gift_name:
            return None
        
        # Method 1: Direct tonnelmp bypass
        success, result, method = await self.bypass.bypass_request(
            None, None, api_gift_name
        )
        
        if success and isinstance(result, dict) and "price" in result:
            logger.info(f"🎯 Advanced bypass success via {method}: {result['price']} TON")
            return float(result["price"])
        
        # Method 2: Manual API endpoint bypass
        url = "https://gifts2.tonnel.network/api/pageGifts"
        payload = {
            "filter": json.dumps({
                "price": {"$exists": True},
                "buyer": {"$exists": False},
                "asset": "TON",
                "premarket": True,
                "gift_name": api_gift_name
            }),
            "limit": 5,
            "page": 1,
            "sort": "{\"price\":1,\"gift_id\":-1}",
            "ref": 0,
            "user_auth": ""
        }
        
        success, result, method = await self.bypass.bypass_request(url, payload)
        
        if success and isinstance(result, list) and len(result) > 0:
            price = float(result[0].get('price', 0))
            if price > 0:
                logger.info(f"🎯 Manual API bypass success via {method}: {price} TON")
                return price
        
        # Method 3: Authenticated filterStats
        url = "https://gifts3.tonnel.network/api/filterStats"
        payload = {
            "authData": self.auth_data
        }
        
        success, result, method = await self.bypass.bypass_request(url, payload)
        
        if success and isinstance(result, dict):
            # Parse filterStats result for our gift
            data = result.get('data', {})
            for gift_key, gift_data in data.items():
                if api_gift_name.lower() in gift_key.lower():
                    floor_price = gift_data.get('data', {}).get('floorPrice')
                    if floor_price and floor_price > 0:
                        logger.info(f"🎯 FilterStats bypass success via {method}: {floor_price} TON")
                        return float(floor_price)
        
        logger.error(f"❌ All advanced bypass methods failed for {gift_name}")
        return None
    
    def get_success_statistics(self) -> Dict[str, Any]:
        """Get comprehensive success statistics."""
        stats = self.bypass.get_success_rates(24)
        
        # Calculate overall success rate
        if stats:
            total_attempts = sum(1 for _ in stats.keys())
            successful_methods = sum(1 for rate in stats.values() if rate > 0)
            overall_rate = (successful_methods / total_attempts * 100) if total_attempts > 0 else 0
        else:
            overall_rate = 0
        
        return {
            "overall_success_rate": overall_rate,
            "method_success_rates": stats,
            "available_libraries": {
                "curl_cffi": CURL_CFFI_AVAILABLE,
                "httpx": HTTPX_AVAILABLE,
                "aiohttp": AIOHTTP_AVAILABLE,
                "requests": True
            }
        }

# Export for easy usage
advanced_api = AdvancedTonnelAPI()

async def get_advanced_price(gift_name: str) -> Optional[float]:
    """Simple function to get price with advanced bypass."""
    return await advanced_api.get_gift_price_advanced(gift_name)

def get_bypass_stats() -> Dict[str, Any]:
    """Get bypass success statistics."""
    return advanced_api.get_success_statistics() 