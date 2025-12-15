#!/usr/bin/env python3
"""
Generate price cards for all 29 plus premarket gifts
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_card_design import create_gift_card
from plus_premarket_gifts import PLUS_PREMARKET_GIFT_NAMES

async def generate_all_cards():
    """Generate cards for all plus premarket gifts"""
    print("=" * 80)
    print("Generating Price Cards for All Plus Premarket Gifts")
    print("=" * 80)
    print(f"Total gifts: {len(PLUS_PREMARKET_GIFT_NAMES)}")
    print()
    
    success_count = 0
    fail_count = 0
    
    # Create output directory if it doesn't exist
    output_dir = "new_gift_cards"
    os.makedirs(output_dir, exist_ok=True)
    
    for i, gift_name in enumerate(PLUS_PREMARKET_GIFT_NAMES, 1):
        print(f"[{i}/{len(PLUS_PREMARKET_GIFT_NAMES)}] Generating card for: {gift_name}")
        
        try:
            card = await create_gift_card(gift_name, force_fresh=False)
            
            if card:
                # Save the card
                safe_name = gift_name.replace(" ", "_").replace("/", "_").replace("'", "")
                filename = f"{output_dir}/{safe_name}.webp"
                card.save(filename)
                print(f"  ✅ Saved: {filename}")
                success_count += 1
            else:
                print(f"  ❌ Failed to generate card for {gift_name}")
                fail_count += 1
                
        except Exception as e:
            print(f"  ❌ ERROR: {gift_name} - {str(e)}")
            fail_count += 1
        
        # Small delay to avoid overwhelming the API
        await asyncio.sleep(0.5)
    
    print()
    print("=" * 80)
    print("Generation Complete")
    print("=" * 80)
    print(f"Success: {success_count}/{len(PLUS_PREMARKET_GIFT_NAMES)}")
    print(f"Failed:  {fail_count}/{len(PLUS_PREMARKET_GIFT_NAMES)}")
    print("=" * 80)
    
    if fail_count > 0:
        return 1
    return 0

if __name__ == "__main__":
    exit(asyncio.run(generate_all_cards()))

