#!/usr/bin/env python3
"""Example usage of Quant API client"""

import asyncio
from auth import get_init_data
from api import QuantAPI


async def example():
    """Example: Fetch and filter gifts data"""
    
    # Authenticate
    init_data = await get_init_data()
    
    # Create API client
    api = QuantAPI(init_data)
    
    # Get all data
    data = api.get_gifts()
    
    # Filter expensive gifts (floor price > $100)
    expensive_gifts = [
        g for g in data['gifts']
        if float(g['floor_price']) > 100
    ]
    
    print(f"Found {len(expensive_gifts)} expensive gifts:\n")
    for gift in sorted(expensive_gifts, key=lambda x: float(x['floor_price']), reverse=True):
        print(f"  {gift['full_name']}: ${gift['floor_price']}")


if __name__ == '__main__':
    asyncio.run(example())
