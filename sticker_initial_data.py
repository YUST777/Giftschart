#!/usr/bin/env python3
"""
Sticker Initial Data Module

This module provides access to initial supply and price data for all stickers,
including data from stickers.tools API and manual research.
"""

import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Path to the initial data JSON file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INITIAL_DATA_FILE = os.path.join(SCRIPT_DIR, "sticker_initial_data.json")

# Cache for loaded data
_cached_data = None

def load_initial_data() -> Dict[str, Any]:
    """Load initial sticker data from JSON file."""
    global _cached_data
    
    if _cached_data is not None:
        return _cached_data
    
    try:
        with open(INITIAL_DATA_FILE, 'r', encoding='utf-8') as f:
            _cached_data = json.load(f)
        logger.info(f"Loaded initial data for {_cached_data['metadata']['total_stickers']} stickers")
        return _cached_data
    except FileNotFoundError:
        logger.error(f"Initial data file not found: {INITIAL_DATA_FILE}")
        return {"metadata": {"total_stickers": 0}, "sticker_data": {}}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing initial data JSON: {e}")
        return {"metadata": {"total_stickers": 0}, "sticker_data": {}}
    except Exception as e:
        logger.error(f"Error loading initial data: {e}")
        return {"metadata": {"total_stickers": 0}, "sticker_data": {}}

def get_initial_supply(collection: str, sticker: str) -> Optional[int]:
    """
    Get initial supply for a specific sticker.
    
    Args:
        collection: Collection name
        sticker: Sticker name
        
    Returns:
        Initial supply count or None if not found
    """
    data = load_initial_data()
    sticker_data = data.get("sticker_data", {})
    
    collection_data = sticker_data.get(collection, {})
    sticker_info = collection_data.get(sticker, {})
    
    return sticker_info.get("initial_supply")

def get_initial_price_usd(collection: str, sticker: str) -> Optional[float]:
    """
    Get initial USD price for a specific sticker.
    
    Args:
        collection: Collection name
        sticker: Sticker name
        
    Returns:
        Initial USD price or None if not found
    """
    data = load_initial_data()
    sticker_data = data.get("sticker_data", {})
    
    collection_data = sticker_data.get(collection, {})
    sticker_info = collection_data.get(sticker, {})
    
    return sticker_info.get("initial_price_usd")

def get_initial_price_ton(collection: str, sticker: str) -> Optional[float]:
    """
    Get initial TON price for a specific sticker.
    
    Args:
        collection: Collection name
        sticker: Sticker name
        
    Returns:
        Initial TON price or None if not found
    """
    data = load_initial_data()
    sticker_data = data.get("sticker_data", {})
    
    collection_data = sticker_data.get(collection, {})
    sticker_info = collection_data.get(sticker, {})
    
    return sticker_info.get("initial_price_ton")

def get_sticker_initial_data(collection: str, sticker: str) -> Dict[str, Any]:
    """
    Get all initial data for a specific sticker.
    
    Args:
        collection: Collection name
        sticker: Sticker name
        
    Returns:
        Dictionary with initial supply and prices, or empty dict if not found
    """
    data = load_initial_data()
    sticker_data = data.get("sticker_data", {})
    
    collection_data = sticker_data.get(collection, {})
    return collection_data.get(sticker, {})

def has_initial_data(collection: str, sticker: str) -> bool:
    """
    Check if initial data exists for a specific sticker.
    
    Args:
        collection: Collection name
        sticker: Sticker name
        
    Returns:
        True if initial data exists, False otherwise
    """
    data = load_initial_data()
    sticker_data = data.get("sticker_data", {})
    
    return collection in sticker_data and sticker in sticker_data[collection]

def get_all_collections() -> list:
    """
    Get list of all collections with initial data.
    
    Returns:
        List of collection names
    """
    data = load_initial_data()
    sticker_data = data.get("sticker_data", {})
    return list(sticker_data.keys())

def get_stickers_in_collection(collection: str) -> list:
    """
    Get list of all stickers in a collection with initial data.
    
    Args:
        collection: Collection name
        
    Returns:
        List of sticker names
    """
    data = load_initial_data()
    sticker_data = data.get("sticker_data", {})
    
    collection_data = sticker_data.get(collection, {})
    return list(collection_data.keys())

def get_total_stickers() -> int:
    """
    Get total number of stickers with initial data.
    
    Returns:
        Total number of stickers
    """
    data = load_initial_data()
    return data.get("metadata", {}).get("total_stickers", 0)

def calculate_supply_percentage(current_supply: int, collection: str, sticker: str) -> Optional[float]:
    """
    Calculate what percentage of initial supply remains.
    
    Args:
        current_supply: Current supply count
        collection: Collection name
        sticker: Sticker name
        
    Returns:
        Percentage of initial supply remaining, or None if no initial data
    """
    initial_supply = get_initial_supply(collection, sticker)
    if initial_supply is None or initial_supply == 0:
        return None
    
    percentage = (current_supply / initial_supply) * 100
    return round(percentage, 1)

def get_metadata() -> Dict[str, Any]:
    """
    Get metadata about the initial data.
    
    Returns:
        Metadata dictionary
    """
    data = load_initial_data()
    return data.get("metadata", {})

# Example usage and testing
if __name__ == "__main__":
    # Test the functions
    print("Testing Sticker Initial Data Module")
    print("=" * 40)
    
    # Test getting initial supply
    supply = get_initial_supply("Blum", "General")
    print(f"Blum General initial supply: {supply}")
    
    # Test getting initial price
    price_usd = get_initial_price_usd("Blum", "General")
    price_ton = get_initial_price_ton("Blum", "General")
    print(f"Blum General initial prices: ${price_usd} USD, {price_ton} TON")
    
    # Test supply percentage calculation
    current_supply = 2002  # From the image
    percentage = calculate_supply_percentage(current_supply, "Blum", "General")
    print(f"Blum General supply percentage: {percentage}%")
    
    # Test getting all data
    all_data = get_sticker_initial_data("Blum", "General")
    print(f"Blum General all data: {all_data}")
    
    # Test collections
    collections = get_all_collections()
    print(f"Total collections: {len(collections)}")
    
    # Test total stickers
    total = get_total_stickers()
    print(f"Total stickers with initial data: {total}")
