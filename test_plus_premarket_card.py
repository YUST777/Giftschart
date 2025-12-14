#!/usr/bin/env python3
"""
Test script to generate a price card for a plus premarket gift
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_plus_premarket_card():
    """Test generating a card for a plus premarket gift"""
    from new_card_design import create_gift_card
    from plus_premarket_gifts import PLUS_PREMARKET_GIFT_NAMES
    
    print("=" * 80)
    print("Testing Plus Premarket Gift Card Generation")
    print("=" * 80)
    print()
    
    # Test with first few gifts
    test_gifts = ["Coffin", "Mask", "Backpack", "Book", "Eagle"]
    
    for gift_name in test_gifts:
        if gift_name in PLUS_PREMARKET_GIFT_NAMES:
            print(f"\n{'='*80}")
            print(f"Testing: {gift_name}")
            print(f"{'='*80}")
            
            try:
                result = await create_gift_card(gift_name, force_fresh=True)
                
                # Check if result is an Image object or dict
                if result:
                    if hasattr(result, 'size'):
                        # It's a PIL Image object
                        print(f"✅ SUCCESS: Card generated for {gift_name}")
                        print(f"   Image size: {result.size}")
                        print(f"   Image mode: {result.mode}")
                        
                        # Save the image to verify
                        output_path = f"new_gift_cards/{gift_name.replace(' ', '_')}.png"
                        try:
                            result.save(output_path)
                            print(f"   Saved to: {output_path}")
                        except Exception as save_error:
                            print(f"   Could not save: {save_error}")
                    elif isinstance(result, dict):
                        # It's a dict with metadata
                        print(f"✅ SUCCESS: Card generated for {gift_name}")
                        print(f"   Image path: {result.get('image_path', 'N/A')}")
                        print(f"   Price TON: {result.get('price_ton', 'N/A')}")
                        print(f"   Price USD: {result.get('price_usd', 'N/A')}")
                        print(f"   Change %: {result.get('change_percentage', 'N/A')}")
                    else:
                        print(f"✅ Card generated for {gift_name} (type: {type(result)})")
                else:
                    print(f"❌ FAILED: Could not generate card for {gift_name}")
                    
            except Exception as e:
                print(f"❌ ERROR: {gift_name} - {str(e)}")
                import traceback
                traceback.print_exc()
            
            print()
    
    print("=" * 80)
    print("Test Complete")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_plus_premarket_card())

