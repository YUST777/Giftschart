#!/usr/bin/env python3
"""
TON Price Utility
Fetches real-time TON price from CoinMarketCap and provides caching
"""

import os
import time
import re
import json
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

# Cache for TON price
_ton_price_cache: Optional[float] = None
_ton_price_timestamp: float = 0
TON_PRICE_CACHE_DURATION: int = 300  # Cache TON price for 5 minutes
FALLBACK_TON_PRICE: float = 2.10  # Fallback value (updated to current approximate)

def get_ton_price_usd() -> float:
    """
    Fetch real-time TON price from CoinMarketCap.
    Returns cached value if available and fresh, otherwise fetches new price.
    
    Returns:
        float: TON price in USD
    """
    global _ton_price_cache, _ton_price_timestamp
    
    # Check cache first
    current_time = time.time()
    if _ton_price_cache and (current_time - _ton_price_timestamp) < TON_PRICE_CACHE_DURATION:
        return _ton_price_cache
    
    try:
        # Fetch TON price from CoinMarketCap
        ton_url = "https://coinmarketcap.com/currencies/toncoin/"
        response = requests.get(ton_url, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Extract price from statistics JSON
            match = re.search(r'"statistics":(\{.*?\})', content)
            if match:
                try:
                    statistics_json = match.group(1)
                    statistics_dict = json.loads(statistics_json)
                    price = statistics_dict.get("price", None)
                    
                    if price and price != "N/A" and price != 0:
                        try:
                            ton_price = float(price)
                            _ton_price_cache = ton_price
                            _ton_price_timestamp = current_time
                            logger.info(f"Fetched TON price from CoinMarketCap: ${ton_price:.2f}")
                            return ton_price
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid TON price format: {price}")
                except json.JSONDecodeError:
                    logger.warning("Error parsing TON statistics JSON from CoinMarketCap")
        else:
            logger.warning(f"CoinMarketCap request failed: {response.status_code}")
    except Exception as e:
        logger.warning(f"Error fetching TON price from CoinMarketCap: {e}")
    
    # Return cached value or fallback
    if _ton_price_cache:
        logger.info(f"Using cached TON price: ${_ton_price_cache:.2f}")
        return _ton_price_cache
    
    logger.warning(f"Using fallback TON price: ${FALLBACK_TON_PRICE:.2f}")
    return FALLBACK_TON_PRICE

def clear_ton_price_cache():
    """Clear the TON price cache to force a fresh fetch"""
    global _ton_price_cache, _ton_price_timestamp
    _ton_price_cache = None
    _ton_price_timestamp = 0
    logger.info("TON price cache cleared")

