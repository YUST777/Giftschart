#!/usr/bin/env python3
"""
Regenerate missing plus premarket gift cards
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_card_design import create_gift_card
from plus_premarket_gifts import PLUS_PREMARKET_GIFT_NAMES

async def regenerate_missing():
    """Regenerate cards for missing gifts"""
    # Cards that failed or are missing
    missing_gifts = ["1 May", "Durov's Statuette", "T-shirt"]
    
    print("=" * 80)
    print("Regenerating Missing Plus Premarket Gift Cards")
    print("=" * 80)
    print()
    
    output_dir = "new_gift_cards"
    os.makedirs(output_dir, exist_ok=True)
    
    for gift_name in missing_gifts:
        print(f"Generating: {gift_name}")
        try:
            # Wait a bit to avoid database locks
            await asyncio.sleep(2)
            
            card = await create_gift_card(gift_name, force_fresh=True)
            
            if card:
                safe_name = gift_name.replace(" ", "_").replace("-", "_").replace("'", "").replace("/", "_")
                filename = f"{output_dir}/{safe_name}.png"
                card.save(filename)
                print(f"  ✅ Saved: {filename}")
            else:
                print(f"  ❌ Failed to generate card for {gift_name}")
        except Exception as e:
            print(f"  ❌ ERROR: {gift_name} - {str(e)}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 80)
    print("Regeneration Complete")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(regenerate_missing())

