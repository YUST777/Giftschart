#!/usr/bin/env python3
"""Extract gifts that have numeric IDs as names"""

import json

def extract_id_gifts():
    """Find all gifts where name is a numeric ID"""
    
    # Load the JSON file
    with open('gifts_collections.json', 'r', encoding='utf-8') as f:
        gifts = json.load(f)
    
    # Find gifts with numeric IDs as names
    id_gifts = []
    for gift in gifts:
        name = gift.get('name', '')
        # Check if name is all digits (numeric ID)
        if name.isdigit():
            id_gifts.append({
                'id': name,
                'title': gift.get('title', 'N/A')
            })
    
    # Display results
    print(f"🔍 Found {len(id_gifts)} gifts with numeric IDs as names:\n")
    print("=" * 80)
    
    for item in id_gifts:
        print(f"ID:    {item['id']}")
        print(f"Title: {item['title']}")
        print("-" * 80)
    
    # Save to a separate file
    output_file = 'id_gifts_mapping.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(id_gifts, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved mapping to {output_file}")
    
    return id_gifts

if __name__ == '__main__':
    extract_id_gifts()
