#!/usr/bin/env python3
"""
Generate All Sticker Price Cards

This script fetches all stickers from the stickers.tools API and generates
price cards for each one.
"""

import os
import sys
import json
import time

# Add project root to path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import services.stickers_tools_api as sticker_api
from generators.sticker_price_card_generator import generate_price_card

def main():
    print("Fetching all stickers from stickers.tools API...")
    
    try:
        stats = sticker_api.get_sticker_stats(force_refresh=True)
    except Exception as e:
        print(f"Error fetching sticker stats: {e}")
        return
    
    collections = stats.get('collections', {})
    print(f"Found {len(collections)} collections")
    
    # Create output directory
    output_dir = os.path.join(_project_root, "Sticker_Price_Cards")
    os.makedirs(output_dir, exist_ok=True)
    
    # Store all sticker data for the JSON file
    all_sticker_data = []
    
    total_stickers = 0
    generated = 0
    failed = 0
    
    for collection_id, collection_data in collections.items():
        collection_name = collection_data.get('name', 'Unknown')
        stickers = collection_data.get('stickers', [])
        
        print(f"\nProcessing collection: {collection_name} ({len(stickers)} stickers)")
        
        for sticker in stickers:
            # Skip invalid entries
            if not isinstance(sticker, dict) or 'name' not in sticker:
                continue
            
            sticker_name = sticker.get('name', '')
            if not sticker_name:
                continue
            
            total_stickers += 1
            
            try:
                # Get price data
                floor_price_ton = float(sticker.get('floor_price_ton', 0))
                floor_price_usd = float(sticker.get('floor_price_usd', 0))
                supply = sticker.get('supply', 0)
                initial_supply = sticker.get('initial_supply', 0)
                init_price_usd = float(sticker.get('init_price_usd', 0))
                
                # Store sticker data
                sticker_data = {
                    'collection': collection_name,
                    'sticker': sticker_name,
                    'floor_price_ton': floor_price_ton,
                    'floor_price_usd': floor_price_usd,
                    'supply': supply,
                    'initial_supply': initial_supply,
                    'init_price_usd': init_price_usd
                }
                all_sticker_data.append(sticker_data)
                
                # Generate card
                print(f"  Generating: {sticker_name} (${floor_price_usd:.2f})")
                
                # Create normalized filename
                safe_collection = collection_name.replace(' ', '_').replace('/', '_')
                safe_sticker = sticker_name.replace(' ', '_').replace('/', '_')
                output_path = os.path.join(output_dir, f"{safe_collection}_{safe_sticker}_card.webp")
                
                # Generate the card
                result = generate_price_card(
                    collection=collection_name,
                    sticker=sticker_name,
                    price=floor_price_ton,
                    output_dir=output_dir
                )
                
                if result:
                    generated += 1
                else:
                    failed += 1
                    print(f"    ❌ Failed to generate card")
                
                # Small delay to avoid overwhelming the system
                time.sleep(0.1)
                
            except Exception as e:
                failed += 1
                print(f"    ❌ Error: {e}")
    
    # Save sticker data to JSON
    data_dir = os.path.join(_project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    json_path = os.path.join(data_dir, "sticker_price_results.json")
    
    with open(json_path, 'w') as f:
        json.dump(all_sticker_data, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Generation Complete!")
    print(f"{'='*60}")
    print(f"Total stickers: {total_stickers}")
    print(f"Successfully generated: {generated}")
    print(f"Failed: {failed}")
    print(f"Output directory: {output_dir}")
    print(f"Data file: {json_path}")

if __name__ == "__main__":
    main()
