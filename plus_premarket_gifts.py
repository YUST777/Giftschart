#!/usr/bin/env python3
"""
Plus Premarket Gifts Configuration
Defines the 29 gifts in the "+premarket" category with their IDs and display names
"""

# Plus premarket gifts mapping
# Key: normalized filename, Value: dict with name, gift ID, supply, first sale price in stars, and release date
# 1 Star = $0.016
# Release dates are in format "DD/MM" (day/month) - year is assumed to be 2025
PLUS_PREMARKET_GIFTS = {
    "1_May": {"name": "1 May", "id": "5807641025165919973", "supply": 500000, "first_sale_price_stars": 100, "release_date": "01/05"},
    "Backpack": {"name": "Backpack", "id": "5886756255493523118", "supply": 200000, "first_sale_price_stars": 500, "release_date": "01/09"},
    "Bird_Mark": {"name": "Bird Mark", "id": "5832325860073407546", "supply": 250000, "first_sale_price_stars": 150, "release_date": "08/05"},
    "Book": {"name": "Book", "id": "5886387158889005864", "supply": 100000, "first_sale_price_stars": 1000, "release_date": "01/09"},
    "Case": {"name": "Case", "id": "5884080014126745057", "supply": 25000, "first_sale_price_stars": 5000, "release_date": "01/09"},
    "Coconut_Drink": {"name": "Coconut Drink", "id": "5832371318007268701", "supply": 500000, "first_sale_price_stars": 150, "release_date": "15/08"},
    "Coffin": {"name": "Coffin", "id": "5776227780391864916", "supply": 40000, "first_sale_price_stars": 5000, "release_date": "31/10"},
    "Cone_IceCream": {"name": "Cone IceCream", "id": "5898012527257715797", "supply": 500000, "first_sale_price_stars": 75, "release_date": "01/06"},
    "Cream_IceCream": {"name": "Cream IceCream", "id": "5897607679345427347", "supply": 250000, "first_sale_price_stars": 150, "release_date": "01/06"},
    "Durov_Glasses": {"name": "Durov Glasses", "id": "5834651202612102354", "supply": 5000, "first_sale_price_stars": 30000, "release_date": "15/08"},
    "Durovs_Statuette": {"name": "Durov's Statuette", "id": "6003477390536213997", "supply": 4100, "first_sale_price_stars": 41000, "release_date": "10/10"},
    "Eagle": {"name": "Eagle", "id": "5999116401002939514", "supply": 15000, "first_sale_price_stars": 5000, "release_date": "04/07"},
    "Easter_Cake": {"name": "Easter Cake", "id": "5773791997064119815", "supply": 500000, "first_sale_price_stars": 75, "release_date": "19/04"},
    "Eight_Roses": {"name": "Eight Roses", "id": "5933770397739647689", "supply": 150000, "first_sale_price_stars": 200, "release_date": "07/03"},
    "Golden_Medal": {"name": "Golden Medal", "id": "5830340739074097859", "supply": 150000, "first_sale_price_stars": 300, "release_date": "09/05"},
    "Grave": {"name": "Grave", "id": "5775955135867913556", "supply": 10000, "first_sale_price_stars": 15000, "release_date": "31/10"},
    "Heart_Pendant": {"name": "Heart Pendant", "id": "5872744075014177223", "supply": 80000, "first_sale_price_stars": 500, "release_date": "14/02"},
    "Lamp_Candle": {"name": "Lamp Candle", "id": "5913351908466098791", "supply": 300000, "first_sale_price_stars": 100, "release_date": "28/02"},
    "Mask": {"name": "Mask", "id": "5775966332847654507", "supply": 250000, "first_sale_price_stars": 500, "release_date": "31/10"},
    "Pencil": {"name": "Pencil", "id": "5882129648002794519", "supply": 50000, "first_sale_price_stars": 2500, "release_date": "01/09"},
    "Pink_Flamingo": {"name": "Pink Flamingo", "id": "5832644211639321671", "supply": 250000, "first_sale_price_stars": 300, "release_date": "15/08"},
    "REDO": {"name": "REDO", "id": "5832279504491381684", "supply": 20000, "first_sale_price_stars": 5000, "release_date": "15/08"},
    "Red_Star": {"name": "Red Star", "id": "5830323722413671504", "supply": 500000, "first_sale_price_stars": 100, "release_date": "08/05"},
    "Sand_Castle": {"name": "Sand Castle", "id": "5834918435477259676", "supply": 150000, "first_sale_price_stars": 500, "release_date": "15/08"},
    "Sneakers": {"name": "Sneakers", "id": "6001229799790478558", "supply": 10000, "first_sale_price_stars": 10000, "release_date": "10/10"},
    "Statue": {"name": "Statue", "id": "5999298447486747746", "supply": 300000, "first_sale_price_stars": 250, "release_date": "04/07"},
    "Surfboard": {"name": "Surfboard", "id": "5832497899283415733", "supply": 40000, "first_sale_price_stars": 2500, "release_date": "15/08"},
    "T_shirt": {"name": "T-shirt", "id": "6001425315291727333", "supply": 10000, "first_sale_price_stars": 10000, "release_date": "10/10"},
    "Torch": {"name": "Torch", "id": "5999277561060787166", "supply": 500000, "first_sale_price_stars": 150, "release_date": "04/07"},
    "Airplane": {"name": "Airplane", "id": "5818708013426410448", "supply": 1000, "first_sale_price_stars": 335000, "release_date": "15/11"},
}

# Star to USD conversion: 1 Star = $0.016
STAR_TO_USD = 0.016

# Special gifts with numeric IDs (from MRKT API)
# These 6 gifts are available on MRKT marketplace
MRKT_SPECIAL_GIFTS = {
    "5775955135867913556",  # Grave
    "5776227780391864916",  # Coffin
    "5775966332847654507",  # Mask
    "6001229799790478558",  # Sneakers
    "6003477390536213997",  # Durov's Statuette
    "6001425315291727333",  # T-shirt
    "5818708013426410448",  # Airplane
}

# Create reverse mapping: gift_id -> normalized_name
ID_TO_NAME = {v["id"]: k for k, v in PLUS_PREMARKET_GIFTS.items()}

# Create display name mapping: normalized_name -> display_name
NAME_MAPPING = {k: v["name"] for k, v in PLUS_PREMARKET_GIFTS.items()}

# List of all plus premarket gift display names
PLUS_PREMARKET_GIFT_NAMES = [v["name"] for v in PLUS_PREMARKET_GIFTS.values()]

def get_gift_id(gift_name):
    """Get gift ID from display name or normalized name"""
    # Try direct lookup with normalized name
    normalized = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
    if normalized in PLUS_PREMARKET_GIFTS:
        return PLUS_PREMARKET_GIFTS[normalized]["id"]
    
    # Try lookup by display name
    for key, value in PLUS_PREMARKET_GIFTS.items():
        if value["name"].lower() == gift_name.lower():
            return value["id"]
    
    return None

def is_plus_premarket_gift(gift_name):
    """Check if a gift is a plus premarket gift"""
    normalized = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
    if normalized in PLUS_PREMARKET_GIFTS:
        return True
    
    # Check by display name
    for value in PLUS_PREMARKET_GIFTS.values():
        if value["name"].lower() == gift_name.lower():
            return True
    
    return False

def is_mrkt_gift(gift_id):
    """Check if a gift is available on MRKT marketplace"""
    return gift_id in MRKT_SPECIAL_GIFTS

def get_gift_supply(gift_name):
    """Get supply for a plus premarket gift"""
    normalized = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
    if normalized in PLUS_PREMARKET_GIFTS:
        return PLUS_PREMARKET_GIFTS[normalized].get("supply")
    
    # Try lookup by display name
    for value in PLUS_PREMARKET_GIFTS.values():
        if value["name"].lower() == gift_name.lower():
            return value.get("supply")
    
    return None

def get_first_sale_price_stars(gift_name):
    """Get first sale price in stars for a plus premarket gift"""
    normalized = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
    if normalized in PLUS_PREMARKET_GIFTS:
        return PLUS_PREMARKET_GIFTS[normalized].get("first_sale_price_stars")
    
    # Try lookup by display name
    for value in PLUS_PREMARKET_GIFTS.values():
        if value["name"].lower() == gift_name.lower():
            return value.get("first_sale_price_stars")
    
    return None

def get_release_date(gift_name):
    """Get release date for a plus premarket gift (format: DD/MM)"""
    normalized = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
    if normalized in PLUS_PREMARKET_GIFTS:
        return PLUS_PREMARKET_GIFTS[normalized].get("release_date")
    
    # Try lookup by display name
    for value in PLUS_PREMARKET_GIFTS.values():
        if value["name"].lower() == gift_name.lower():
            return value.get("release_date")
    
    return None

def calculate_days_since_release(gift_name):
    """Calculate number of days since release date and return the number of days"""
    from datetime import datetime
    
    release_date_str = get_release_date(gift_name)
    if not release_date_str:
        return None
    
    try:
        # Parse release date (DD/MM format, year is 2025)
        day, month = release_date_str.split("/")
        release_date = datetime(2025, int(month), int(day))
        current_date = datetime.now()
        
        # Calculate time difference
        time_diff = current_date - release_date
        
        # If release date is in the future, return None
        if time_diff.total_seconds() < 0:
            return None
        
        days = time_diff.days
        return days
    except Exception as e:
        return None

