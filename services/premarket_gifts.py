#!/usr/bin/env python3
"""
Premarket Gifts Configuration
These gifts use the same sticker-style design as +premarket gifts
but transition to normal market gifts after 21 days from release
"""

from datetime import datetime

# Premarket gifts that transition to market after 21 days
# Format: normalized_name -> {name, supply, first_sale_price_stars, release_date}
PREMARKET_GIFTS = {
    "Bling_Binky": {
        "name": "Bling Binky",
        "supply": 10000,
        "first_sale_price_stars": 5000,
        "release_date": "03/11"  # November 3, 2025
    },
    "Money_Pot": {
        "name": "Money Pot",
        "supply": 120000,
        "first_sale_price_stars": 250,
        "release_date": "03/11"  # November 3, 2025
    },
    "Pretty_Posy": {
        "name": "Pretty Posy",
        "supply": 200000,
        "first_sale_price_stars": 150,
        "release_date": "03/11"  # November 3, 2025
    }
}

# Star to USD conversion: 1 Star = $0.016
STAR_TO_USD = 0.016

# Days until transition to market (21 days)
TRANSITION_DAYS = 21

def is_premarket_gift(gift_name):
    """Check if a gift is a premarket gift (not +premarket)"""
    normalized = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
    if normalized in PREMARKET_GIFTS:
        return True
    
    # Check by display name
    for value in PREMARKET_GIFTS.values():
        if value["name"].lower() == gift_name.lower():
            return True
    
    return False

def get_premarket_supply(gift_name):
    """Get supply for a premarket gift"""
    normalized = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
    if normalized in PREMARKET_GIFTS:
        return PREMARKET_GIFTS[normalized].get("supply")
    
    for value in PREMARKET_GIFTS.values():
        if value["name"].lower() == gift_name.lower():
            return value.get("supply")
    
    return None

def get_premarket_first_sale_price_stars(gift_name):
    """Get first sale price in stars for a premarket gift"""
    normalized = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
    if normalized in PREMARKET_GIFTS:
        return PREMARKET_GIFTS[normalized].get("first_sale_price_stars")
    
    for value in PREMARKET_GIFTS.values():
        if value["name"].lower() == gift_name.lower():
            return value.get("first_sale_price_stars")
    
    return None

def get_premarket_release_date(gift_name):
    """Get release date for a premarket gift (format: DD/MM)"""
    normalized = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
    if normalized in PREMARKET_GIFTS:
        return PREMARKET_GIFTS[normalized].get("release_date")
    
    for value in PREMARKET_GIFTS.values():
        if value["name"].lower() == gift_name.lower():
            return value.get("release_date")
    
    return None

def calculate_days_since_release(gift_name):
    """Calculate number of days since release date"""
    release_date_str = get_premarket_release_date(gift_name)
    if not release_date_str:
        return None
    
    try:
        day, month = release_date_str.split("/")
        release_date = datetime(2025, int(month), int(day))
        current_date = datetime.now()
        time_diff = current_date - release_date
        
        if time_diff.total_seconds() < 0:
            return None
        
        return time_diff.days
    except Exception:
        return None

def is_transitioned_to_market(gift_name):
    """Check if premarket gift has transitioned to market (21+ days since release)"""
    days = calculate_days_since_release(gift_name)
    if days is None:
        return False
    return days >= TRANSITION_DAYS

def get_transition_date(gift_name):
    """Get the date when gift transitions to market (release_date + 21 days)"""
    release_date_str = get_premarket_release_date(gift_name)
    if not release_date_str:
        return None
    
    try:
        day, month = release_date_str.split("/")
        release_date = datetime(2025, int(month), int(day))
        from datetime import timedelta
        transition_date = release_date + timedelta(days=TRANSITION_DAYS)
        return transition_date
    except Exception:
        return None

