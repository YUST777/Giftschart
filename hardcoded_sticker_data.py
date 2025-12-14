#!/usr/bin/env python3
"""
Hardcoded Sticker Data

This module provides hardcoded sale price data for stickers
that may not be available from the API.
"""

# Hardcoded sale prices for various stickers
SALE_PRICES = {
    # Collection: {Sticker: price}
    "Not Pixel": {
        "Cute pack": 50,
        "Diamond Pixel": 75,
        "DOGS Pixel": 100,
        "Error Pixel": 40,
        "Films memes": 30,
        "Grass Pixel": 45,
        "MacPixel": 60,
        "Pixanos": 55,
        "Pixel phrases": 35,
        "Pixioznik": 80,
        "Random memes": 25,
        "Retro Pixel": 70,
        "Smileface pack": 40,
        "SuperPixel": 90,
        "Tournament S1": 120,
        "Vice Pixel": 65,
        "Zompixel": 85,
    },
    "Pudgy Penguins": {
        "Blue Pengu": 200,
        "Cool Blue Pengu": 180,
        "Pengu CNY": 150,
        "Pengu Valentines": 160,
    },
    "Pudgy & Friends": {
        "Pengu x Baby Shark": 220,
        "Pengu x NASCAR": 250,
    },
    "BabyDoge": {
        "Mememania": 100,
    },
    "PUCCA": {
        "PUCCA Moods": 80,
    },
    "Flappy Bird": {
        "Blue Wings": 60,
        "Blush Flight": 55,
        "Frost Flap": 70,
        "Light Glide": 50,
        "Ruby Wings": 75,
    },
    "Lazy & Rich": {
        "Chill or thrill": 90,
        "Sloth Capital": 110,
    },
    "Smeshariki": {
        "Chamomile Valley": 45,
        "The Memes": 40,
    },
    "SUNDOG": {
        "TO THE SUN": 130,
    },
    "Kudai": {
        "GMI": 95,
        "NGMI": 85,
    },
    "Dogs OG": {
        "King": 150,
        "Not Cap": 120,
        "Sheikh": 140,
    },
    "Azuki": {
        "Shao": 180,
    },
    "Blum": {
        "Bunny": 30,
        "Cap": 35,
        "Cat": 40,
        "Cook": 45,
        "Curly": 32,
        "General": 50,
        "No": 25,
        "Worker": 38,
    },
}

def get_sale_price(collection, sticker):
    """
    Get the hardcoded sale price for a sticker.
    
    Args:
        collection (str): Collection name
        sticker (str): Sticker name
        
    Returns:
        int/float/str: Sale price if available, None otherwise
    """
    return SALE_PRICES.get(collection, {}).get(sticker, None)

def has_sale_price(collection, sticker):
    """
    Check if a sticker has a hardcoded sale price.
    
    Args:
        collection (str): Collection name
        sticker (str): Sticker name
        
    Returns:
        bool: True if sale price is available
    """
    return collection in SALE_PRICES and sticker in SALE_PRICES[collection]

def get_all_collections_with_prices():
    """
    Get all collections that have hardcoded sale prices.
    
    Returns:
        list: List of collection names
    """
    return list(SALE_PRICES.keys())

def get_stickers_with_prices(collection):
    """
    Get all stickers in a collection that have hardcoded sale prices.
    
    Args:
        collection (str): Collection name
        
    Returns:
        list: List of sticker names
    """
    return list(SALE_PRICES.get(collection, {}).keys()) 