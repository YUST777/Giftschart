#!/usr/bin/env python3
"""
MRKT API Integration - Improved Version

This module integrates with the MRKT API to fetch real sticker price data
with improved name matching between our sticker names and MRKT character names.
"""

import os
import logging
import requests
import json
import time
import re
from datetime import datetime
from fuzzywuzzy import fuzz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mrkt_api_improved")

# Global variables for caching
STICKER_PRICE_CACHE = {}
CHARACTER_CACHE = []
CHARACTER_CACHE_EXPIRY = 0
DATA_CACHE = {}
CACHE_DURATION = 1920  # 32 minutes in seconds (changed from 3600)

# Configure API base URL and endpoints
API_BASE_URL = "https://api.tgmrkt.io"
AUTH_ENDPOINT = f"{API_BASE_URL}/api/v1/auth"
CHARACTERS_ENDPOINT = f"{API_BASE_URL}/api/v1/characters"
PRICES_ENDPOINT = f"{API_BASE_URL}/api/v1/prices"

# API base URL
BASE_URL = "https://api.tgmrkt.io/api/v1"
STICKER_SETS_ENDPOINT = f"{BASE_URL}/sticker-sets/saling"
CHARACTERS_ENDPOINT = f"{BASE_URL}/sticker-sets/characters"

# Default headers for API requests
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Content-Type": "application/json",
    "Origin": "https://cdn.tgmrkt.io",
    "Referer": "https://cdn.tgmrkt.io/",
    "Sec-Ch-Ua": "\"Google Chrome\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Linux\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site"
}

# Working API tokens - try multiple tokens in case some expire
API_TOKENS = [
    "a7b292ee-72f2-4afa-a5fe-21680eb910ed",  # 🆕 FRESH TOKEN from user - July 2025
    "44cddd0c-e3f4-42c2-955a-7e7de2e59f56",  # Fresh token from api.tgmrkt.io/api/v1/auth
    "8a9be577-5768-4893-a25d-58351da1f970",  # Fresh token generated on 2025-06-20
    "07880302-21fb-46f0-8075-cf3b93e37e60",  # Token from mrkt_auth_token.txt
    "a6fa611a-9003-403c-803f-45ada1881445",  # Original working token
    "72079899-3c67-4d0f-8279-36fb8fdb1348",  # New hardcoded token
    "35d4925e-0f4a-4bb2-a8c2-ab2d00f8102d"   # Token from status file
]

# Auth data from captured request for direct authentication
AUTH_DATA = {
    "data": "user=%7B%22id%22%3A7660176383%2C%22first_name%22%3A%22Afsado%22%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22Afsado%22%2C%22language_code%22%3A%22en%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2F42a5aspTdutRS8KbBc1zWKx5ZYpgjr2PXp5bKEDI91diLJxdTzXtvUussQcWf6g0.svg%22%7D&chat_instance=-6007791381635729774&chat_type=sender&auth_date=1750674849&signature=CDISSs-YDzfpoMgecsazM_9OVMnS0jpRH1Ad-47BXB4Jwh98T3PmrjlKPUzhqTbRA6JXHSNPznbxkkN80sboBQ&hash=97a53412aba54fd0830fcc6d6fc5e470808b9d61b3aa949cf5ce4d92d90223f3",
    "photo": "https://t.me/i/userpic/320/42a5aspTdutRS8KbBc1zWKx5ZYpgjr2PXp5bKEDI91diLJxdTzXtvUussQcWf6g0.svg",
    "appId": None
}

# Collection IDs from the API payload
COLLECTION_IDS = [24, 11, 23, 4, 3, 19, 22, 25, 1, 9, 18, 5, 12, 15, 17, 7, 6, 8, 10, 16, 2, 21, 14, 13, 20]

# TON to USD conversion rate (approximate)
# Import TON price utility
try:
    from ton_price_utils import get_ton_price_usd
except ImportError:
    def get_ton_price_usd():
        return 2.10  # Fallback value

# Collection name to ID mapping (from the API data)
COLLECTION_ID_MAPPING = {
    # Direct mappings from collection names to IDs
    "Pudgy Penguins": 2,      # Blue Pengu, Cool Blue Pengu, Pengu CNY, Pengu Valentines
    "Pudgy & Friends": 16,    # Pengu x Baby Shark, Pengu x NASCAR
    "BabyDoge": 11,           # Mememania
    "PUCCA": 10,              # PUCCA Moods
    "Flappy Bird": 5,         # Blue Wings, Blush Flight, Frost Flap, Light Glide, Ruby Wings
    "Lazy & Rich": 15,        # Chill or thrill, Sloth Capital
    "Smeshariki": 14,         # Chamomile Valley, The Memes
    "SUNDOG": 13,             # TO THE SUN
    "Kudai": 12,              # GMI, NGMI
    "Dogs OG": 1,             # Many characters (Cook, Teletubby, etc.)
    "Azuki": 24,              # Shao
    "Blum": 4,                # Bunny, Cap, Cat, Cook, Curly, General, No, Worker
    "Bored Stickers": 3,      # 2092, 3151, 3278, 4017, 5824, 6527, 9287, 9765, 9780, CNY 2092
    "Dogs rewards": 9,        # Full dig, Gold bone, Silver bone
    "Not Pixel": 8,           # Many pixel characters
    "Notcoin": 6,             # Flags, Not Memes
    "Doodles": 18,            # Doodles Dark Mode, OG Icons
    "Lil Pudgys": 17,         # Lil Pudgys x Baby Shark
    "WAGMI HUB": 20,          # EGG & HAMMER, WAGMI AI AGENT
    "Cattea Life": 19,        # Cattea Chaos
    "Lost Dogs": 7            # Lost Memeries, Magic of the Way
}

# Name mapping for improved matching
# Maps our sticker names to MRKT character names
NAME_MAPPING = {
    # Direct mappings
    "Blue_Pengu": "Blue Pengu",
    "Flags": "Flags",
    "Not_Memes": "Not Memes",
    "Notcoin": "Not Coin",
    "PUCCA": "PUCCA Moods",
    "Ric Flair": "Ric Flair",
    "WAGMI HUB": "GMI",
    "Lil Pudgys": "Lil Pudgys x Baby Shark",
    "Doodles": "Doodles Dark Mode",
    "Cattea Life": "Cattea Chaos",
    "Not Pixel": "No",
    "Pudgy Penguins": "Blue Pengu",
    "Pudgy & Friends": "Pengu x Baby Shark",
    "BabyDoge": "Mememania",
    "Flappy Bird": "Blue Wings",
    "Lazy & Rich": "Sloth Capital",
    "Smeshariki": "Chamomile Valley",
    "SUNDOG": "TO THE SUN",
    "Kudai": "GMI",
    "Dogs OG": "King",
    "Azuki": "Shao",
    "Blum": "Bunny",
    "Bored Stickers": "3151",
    "Dogs rewards": "Gold bone",
    "Lost Dogs": "Lost Memeries",
    
    # Specific character mappings
    "Blue Wings": "Blue Wings",
    "Blush Flight": "Blush Flight",
    "Frost Flap": "Frost Flap",
    "Light Glide": "Light Glide",
    "Ruby Wings": "Ruby Wings",
    "Bunny": "Bunny",
    "Cap": "Cap",
    "Cat": "Cat",
    "Cook": "Cook",
    "Curly": "Curly",
    "General": "General",
    "No": "No",
    "Worker": "Worker",
    "GMI": "GMI",
    "NGMI": "NGMI",
    "Chill or thrill": "Chill or thrill",
    "Sloth Capital": "Sloth Capital",
    "Lost Memeries": "Lost Memeries",
    "Magic of the Way": "Magic of the Way",
    "Cute pack": "Cute pack",
    "Diamond Pixel": "Diamond Pixel",
    "DOGS Pixel": "DOGS Pixel",
    "Error Pixel": "Error Pixel",
    "Films memes": "Films memes",
    "Grass Pixel": "Grass Pixel",
    "MacPixel": "MacPixel",
    "Pixanos": "Pixanos",
    "Pixel phrases": "Pixel phrases",
    "Pixioznik": "Pixioznik",
    "Random memes": "Random memes",
    "Retro Pixel": "Retro Pixel",
    "Smileface pack": "Smileface pack",
    "SuperPixel": "SuperPixel",
    "Tournament S1": "Tournament S1",
    "Vice Pixel": "Vice Pixel",
    "Zompixel": "Zompixel",
    "Pengu x Baby Shark": "Pengu x Baby Shark",
    "Pengu x NASCAR": "Pengu x NASCAR",
    "Cool Blue Pengu": "Cool Blue Pengu",
    "Pengu CNY": "Pengu CNY",
    "Pengu Valentines": "Pengu Valentines",
    "Chamomile Valley": "Chamomile Valley",
    "The Memes": "The Memes",
    "EGG & HAMMER": "EGG & HAMMER",
    "WAGMI AI AGENT": "WAGMI AI AGENT",
}

# Character ID mapping
# Maps character names to (collection_id, character_id) tuples for direct lookup
CHARACTER_ID_MAPPING = {
    "Shao": (24, 1),
    "Mememania": (11, 1),
    "Doo Doo Moods": (23, 1),
    "Bunny": (4, 26),
    "Cap": (4, 27),
    "Cat": (4, 28),
    "Cook": (4, 1),
    "Curly": (4, 3),
    "General": (4, 9),
    "No": (4, 15),
    "Worker": (4, 20),
    "2092": (3, 1),
    "3151": (3, 3),
    "3278": (3, 4),
    "4017": (3, 5),
    "5824": (3, 6),
    "6527": (3, 7),
    "9287": (3, 8),
    "9765": (3, 9),
    "9780": (3, 10),
    "CNY 2092": (3, 11),
    "Cattea Chaos": (19, 2),
    "GENESIS ENERGY": (22, 1),
    "Red Rex Pack": (25, 1),
    "Blue Wings": (5, 2),
    "Blush Flight": (5, 5),
    "Frost Flap": (5, 4),
    "Light Glide": (5, 3),
    "Ruby Wings": (5, 6),
    "GMI": (12, 1),
    "NGMI": (12, 2),
    "Chill or thrill": (15, 2),
    "Sloth Capital": (15, 3),
    "Lil Pudgys x Baby Shark": (17, 1),
    "Lost Memeries": (7, 2),
    "Magic of the Way": (7, 1),
    "Flags": (6, 1),
    "Not Memes": (6, 2),
    "Cute pack": (8, 3),
    "Diamond Pixel": (8, 8),
    "DOGS Pixel": (8, 4),
    "Error Pixel": (8, 11),
    "Films memes": (8, 16),
    "Grass Pixel": (8, 5),
    "MacPixel": (8, 6),
    "Pixanos": (8, 9),
    "Pixel phrases": (8, 15),
    "Pixioznik": (8, 13),
    "Random memes": (8, 2),
    "Retro Pixel": (8, 10),
    "Smileface pack": (8, 17),
    "SuperPixel": (8, 7),
    "Tournament S1": (8, 18),
    "Vice Pixel": (8, 12),
    "Zompixel": (8, 14),
    "PUCCA Moods": (10, 1),
    "Pengu x Baby Shark": (16, 1),
    "Pengu x NASCAR": (16, 2),
    "Blue Pengu": (2, 1),
    "Cool Blue Pengu": (2, 2),
    "Pengu CNY": (2, 3),
    "Pengu Valentines": (2, 4),
    "Ric Flair": (21, 1),
    "Chamomile Valley": (14, 1),
    "The Memes": (14, 2),
    "TO THE SUN": (13, 1),
    "EGG & HAMMER": (20, 1),
    "WAGMI AI AGENT": (20, 2),
    "Full dig": (9, 12),
    "Gold bone": (9, 5),
    "Silver bone": (9, 6),
    "Doodles Dark Mode": (18, 1),
    "OG Icons": (18, 2)
}

class MRKTApiException(Exception):
    """Exception raised for MRKT API errors."""
    pass

def authenticate():
    """
    Authenticate with the MRKT API.
    
    Returns:
        str: Authentication token if successful, None if failed
    """
    try:
        logger.info("Authenticating with MRKT API")
        
        response = requests.post(
            AUTH_ENDPOINT,
            headers=DEFAULT_HEADERS,
            json=AUTH_DATA,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info("Authentication successful")
            
            # Check if token is in response
            if "token" in data:
                token = data["token"]
                logger.info(f"Got fresh token: {token[:10]}...")
                return token
            else:
                logger.warning("Auth successful but no token in response")
                return None
        else:
            logger.warning(f"Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Authentication error: {e}")
        return None

def get_working_token():
    """
    Try to get a working API token using multiple methods:
    1. Direct authentication
    2. Try each token in the list until one works
    
    Returns:
        str: Working API token or None if all fail
    """
    # First try direct authentication
    auth_token = authenticate()
    if auth_token:
        return auth_token
        
    # If direct auth fails, try each hardcoded token
    logger.info("Direct authentication failed, trying hardcoded tokens")
    for token in API_TOKENS:
        try:
            headers = DEFAULT_HEADERS.copy()
            headers["Authorization"] = token
            
            # Make a simple request to test the token
            response = requests.post(
                STICKER_SETS_ENDPOINT,
                headers=headers,
                json={"count": 1},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"Found working API token: {token[:10]}...")
                return token
        except:
            pass
    
    logger.error("All API tokens failed")
    return None

def get_auth_headers():
    """
    Get headers with authentication token
    
    Returns:
        dict: Headers with authentication token
    """
    token = get_working_token()
    if not token:
        raise MRKTApiException("No working API token available")
        
    headers = DEFAULT_HEADERS.copy()
    headers["Authorization"] = token
    return headers

def fetch_characters(use_cache=True):
    """
    Fetch all characters from the API
    
    Args:
        use_cache (bool): Whether to use cached data
        
    Returns:
        list: List of characters
    """
    # Check cache first
    current_time = time.time()
    
    if use_cache and "characters" in DATA_CACHE:
        cache_entry = DATA_CACHE["characters"]
        if current_time < cache_entry.get("expires_at", 0):
            logger.info("Using cached character data")
            return cache_entry["data"]
    
    logger.info("Fetching character data from API")
    
    # Authenticate
    token = authenticate()
    if not token:
        logger.error("Failed to authenticate")
        return []
    
    # Make API request
    try:
        # Use the correct endpoint with collection IDs
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Use the collection IDs from the payload
        payload = {
            "collections": COLLECTION_IDS
        }
        
        response = requests.post(
            CHARACTERS_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            characters = response.json()
            logger.info(f"Successfully fetched {len(characters)} characters")
            
            # Cache the data
            DATA_CACHE["characters"] = {
                "data": characters,
                "expires_at": current_time + CACHE_DURATION
            }
            
            return characters
        else:
            logger.error(f"Failed to fetch characters: {response.status_code} {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error fetching characters: {e}")
        return []

def convert_nano_ton(nano_ton):
    """
    Convert nano TON to TON.
    1 TON = 1,000,000,000 nano TON
    
    Args:
        nano_ton (int): Value in nano TON
        
    Returns:
        float: Value in TON
    """
    if not nano_ton:
        return 0.0
    return nano_ton / 1_000_000_000

def normalize_name(name):
    """
    Normalize a name for comparison
    
    Args:
        name (str): The name to normalize
        
    Returns:
        str: Normalized name
    """
    if not name:
        return ""
    
    # Replace underscores and hyphens with spaces
    name = name.replace('_', ' ').replace('-', ' ')
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove special characters and extra spaces
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

def find_character_by_direct_id(sticker_name):
    """
    Find a character by direct ID lookup
    
    Args:
        sticker_name (str): The sticker name to look up
        
    Returns:
        dict: Character data if found, None otherwise
    """
    # Check if we have a direct ID mapping
    if sticker_name in CHARACTER_ID_MAPPING:
        collection_id, character_id = CHARACTER_ID_MAPPING[sticker_name]
        logger.info(f"Using direct ID mapping: {sticker_name} -> ({collection_id}, {character_id})")
        
        # Get all characters
        characters = fetch_characters()
        if not characters:
            return None
        
        # Find the character with matching collection_id and character_id
        for char in characters:
            if (char.get('stickerCollectionId') == collection_id and 
                char.get('id') == character_id):
                return char
    
    return None

def find_character_by_name(sticker_name):
    """
    Find a character by name in the API data using improved matching
    
    Args:
        sticker_name (str): The sticker name to search for
        
    Returns:
        dict: Character data if found, None otherwise
    """
    # First try direct ID lookup
    direct_match = find_character_by_direct_id(sticker_name)
    if direct_match:
        return direct_match
    
    # Get all characters
    characters = fetch_characters()
    if not characters:
        return None
    
    # Check if we have a direct mapping for this sticker
    if sticker_name in NAME_MAPPING:
        mapped_name = NAME_MAPPING[sticker_name]
        logger.info(f"Using direct name mapping: {sticker_name} -> {mapped_name}")
        
        # First try direct ID lookup for the mapped name
        direct_match = find_character_by_direct_id(mapped_name)
        if direct_match:
            return direct_match
        
        # Look for the mapped name in characters
        for char in characters:
            if char.get('name', '') == mapped_name:
                return char
    
    # Check if we have a collection ID mapping
    collection_id = COLLECTION_ID_MAPPING.get(sticker_name)
    if collection_id:
        logger.info(f"Using collection ID mapping: {sticker_name} -> Collection {collection_id}")
        
        # Find characters in this collection
        collection_chars = [c for c in characters if c.get('stickerCollectionId') == collection_id]
        
        # If we found characters in this collection, return the first one
        if collection_chars:
            # Sort by price (highest first) to get the most valuable character
            collection_chars.sort(key=lambda x: x.get('floorPriceNanoTons', 0), reverse=True)
            return collection_chars[0]
    
    # If no direct mapping, try fuzzy matching
    normalized_name = normalize_name(sticker_name)
    
    # Try to find a match
    best_match = None
    best_match_score = 0
    
    for char in characters:
        # Check character name
        char_name = normalize_name(char.get('name', ''))
        
        # Calculate match score (simple contains check)
        score = 0
        if char_name in normalized_name or normalized_name in char_name:
            # Length of the matching part / length of the longer string
            score = len(min(char_name, normalized_name, key=len)) / len(max(char_name, normalized_name, key=len))
            
            if score > best_match_score:
                best_match_score = score
                best_match = char
        
        # Check collection name (if available in the character data)
        collection_name = normalize_name(char.get('collectionName', ''))
        if collection_name and (collection_name in normalized_name or normalized_name in collection_name):
            # Length of the matching part / length of the longer string
            score = len(min(collection_name, normalized_name, key=len)) / len(max(collection_name, normalized_name, key=len))
            
            if score > best_match_score:
                best_match_score = score
                best_match = char
    
    # Only return a match if the score is above a threshold
    if best_match_score >= 0.5:
        logger.info(f"Found fuzzy match for {sticker_name} with score {best_match_score:.2f}: {best_match.get('name')}")
        return best_match
    
    return None

def get_sticker_price(search_term, use_cache=True):
    """
    Get price data for a sticker.
    
    Args:
        search_term (str): Search term for the sticker
        use_cache (bool): Whether to use cache
        
    Returns:
        dict: Price data for the sticker
    """
    # Check cache first
    cache_key = search_term.lower()
    current_time = time.time()
    
    if use_cache and cache_key in STICKER_PRICE_CACHE:
        cache_entry = STICKER_PRICE_CACHE[cache_key]
        if current_time < cache_entry.get("expires_at", 0):
            logger.info(f"Using cached price data for {search_term}")
            print(f"🔄 CACHE: Using cached price data for {search_term}")
            return cache_entry["data"]
    
    logger.info(f"Fetching price data for {search_term}")
    print(f"🌐 LIVE API: Fetching fresh price data for {search_term} from MRKT API")
    
    try:
        # Special cases for specific stickers
        special_cases = {
            "Pudgy and Friends Pengu x NASCAR": "Pengu x NASCAR",
            "Pudgy and Friends Friends Pengu x NASCAR": "Pengu x NASCAR"
        }
        
        # Check if search term is in special cases
        search_query = search_term
        if search_term in special_cases:
            search_query = special_cases[search_term]
            logger.info(f"Using special case mapping: {search_query}")
        
        # Fetch character data
        characters = fetch_characters(use_cache=use_cache)
        
        # Search for character
        best_match = None
        best_score = 0
        
        # First try exact match
        for character in characters:
            if character['name'].lower() == search_query.lower():
                logger.info(f"Found exact match for {search_query}: {character['name']}")
                best_match = character
                break
        
        # If no exact match, try fuzzy matching
        if not best_match:
            for character in characters:
                score = fuzz.ratio(character['name'].lower(), search_query.lower())
                if score > best_score and score >= 50:  # Minimum score threshold
                    best_score = score
                    best_match = character
            
            if best_match:
                logger.info(f"Found fuzzy match for {search_query} with score {best_score}: {best_match['name']}")
        
        if best_match:
            # Extract price data
            price_nano_ton = best_match.get('floorPriceNanoTons', 0)
            price_ton = convert_nano_ton(price_nano_ton)
            ton_price_usd = get_ton_price_usd()
            price_usd = price_ton * ton_price_usd
            
            # Create response
            price_data = {
                "name": best_match.get('name', search_term),
                "collection_id": best_match.get('stickerCollectionId'),
                "character_id": best_match.get('id'),
                "price": price_ton,
                "price_usd": price_usd,
                "supply": best_match.get('supply', 0),
                "description": best_match.get('description', ''),
                "last_updated": datetime.now().isoformat(),
                "is_real_data": True
            }
            
            # Cache the data
            STICKER_PRICE_CACHE[cache_key] = {
                "data": price_data,
                "expires_at": current_time + CACHE_DURATION
            }
            
            logger.info(f"Found price data for {search_term}: {price_ton} TON")
            return price_data
        else:
            logger.warning(f"No matching character found for {search_query}")
            
            # Return a response indicating no match found
            response = {
                "name": search_term,
                "message": "No matching sticker found in MRKT API",
                "last_updated": datetime.now().isoformat(),
                "auth_success": True,
                "is_real_data": False
            }
            
            # Cache the response
            STICKER_PRICE_CACHE[cache_key] = {
                "data": response,
                "expires_at": current_time + CACHE_DURATION
            }
            
            return response
    except Exception as e:
        logger.error(f"Error getting sticker price: {e}")
        
        # Return error response
        return {
            "name": search_term,
            "error": str(e),
            "last_updated": datetime.now().isoformat(),
            "is_real_data": False
        }

def clear_cache():
    """Clear all caches."""
    global STICKER_PRICE_CACHE, CHARACTER_CACHE, CHARACTER_CACHE_EXPIRY
    STICKER_PRICE_CACHE = {}
    CHARACTER_CACHE = None
    CHARACTER_CACHE_EXPIRY = 0
    logger.info("All caches cleared")

def test():
    """
    Test the MRKT API integration with real data
    
    Returns:
        dict: Test results
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "auth_successful": False,
        "characters_fetched": 0,
        "sample_prices": []
    }
    
    try:
        # Test authentication
        token = get_working_token()
        if token:
            results["auth_successful"] = True
            results["token"] = token[:10] + "..."
            
            # Test character data
            characters = fetch_characters()
            results["characters_fetched"] = len(characters)
            
            if characters:
                # Get sample character names
                sample_characters = []
                for i in range(min(5, len(characters))):
                    char = characters[i]
                    sample_characters.append(f"{char.get('name', 'Unknown')}")
                
                results["sample_characters"] = sample_characters
                
                # Test price data for a few examples
                test_stickers = list(NAME_MAPPING.keys())[:5]
                for sticker in test_stickers:
                    data = get_sticker_price(sticker, use_cache=False)
                    if data:
                        results["sample_prices"].append({
                            "sticker_name": sticker,
                            "api_name": data.get("name"),
                            "price": data.get("price", 0),
                            "price_usd": data.get("price_usd", 0),
                            "is_real_data": data.get("is_real_data", False)
                        })
    except Exception as e:
        results["error"] = str(e)
    
    return results

if __name__ == "__main__":
    # Run test and print results
    print("Testing improved MRKT API integration...")
    test_results = test()
    print(json.dumps(test_results, indent=2)) 