#!/usr/bin/env python3
"""
View Sticker Price Cards

This script displays a sample of the generated sticker price cards.
"""

import os
import sys
import random
import argparse
import subprocess
from PIL import Image

# Get script directory for cross-platform compatibility
script_dir = os.path.dirname(os.path.abspath(__file__))

# Constants - use os.path.join for cross-platform compatibility
PRICE_CARDS_DIR = os.path.join(script_dir, "Sticker_Price_Cards")

def list_price_cards(directory):
    """List all price cards in the directory"""
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return []
        
    return [f for f in os.listdir(directory) if f.endswith('_price_card.png')]

def view_random_cards(directory, count=5):
    """View a random sample of price cards"""
    cards = list_price_cards(directory)
    
    if not cards:
        print("No price cards found.")
        return
        
    # Select random cards
    sample_size = min(count, len(cards))
    sample = random.sample(cards, sample_size)
    
    print(f"\nViewing {sample_size} random price cards:\n")
    
    # Display each card
    for i, card in enumerate(sample, 1):
        card_path = os.path.join(directory, card)
        print(f"{i}. {card}")
        
        # Try to display the image using system viewer
        try:
            # For Linux
            if sys.platform.startswith('linux'):
                subprocess.run(['xdg-open', card_path], check=False)
            # For macOS
            elif sys.platform == 'darwin':
                subprocess.run(['open', card_path], check=False)
            # For Windows
            elif sys.platform == 'win32':
                os.startfile(card_path)
            else:
                # Fallback to PIL
                img = Image.open(card_path)
                img.show()
        except Exception as e:
            print(f"Failed to display image: {e}")

def view_specific_card(directory, card_name):
    """View a specific price card"""
    cards = list_price_cards(directory)
    
    # Find matching cards
    matches = [c for c in cards if card_name.lower() in c.lower()]
    
    if not matches:
        print(f"No cards found matching '{card_name}'")
        return
        
    print(f"\nFound {len(matches)} cards matching '{card_name}':\n")
    
    # Display each matching card
    for i, card in enumerate(matches, 1):
        card_path = os.path.join(directory, card)
        print(f"{i}. {card}")
        
        # Try to display the image
        try:
            # For Linux
            if sys.platform.startswith('linux'):
                subprocess.run(['xdg-open', card_path], check=False)
            # For macOS
            elif sys.platform == 'darwin':
                subprocess.run(['open', card_path], check=False)
            # For Windows
            elif sys.platform == 'win32':
                os.startfile(card_path)
            else:
                # Fallback to PIL
                img = Image.open(card_path)
                img.show()
        except Exception as e:
            print(f"Failed to display image: {e}")

def view_top_cards(directory, count=10):
    """View the top most valuable sticker cards"""
    # Top stickers by price (hardcoded for simplicity)
    top_stickers = [
        "Dogs_rewards_Gold_bone",
        "Dogs_OG_Not_Cap",
        "Pudgy_and_Friends_Pengu_x_Baby_Shark",
        "Dogs_OG_Sheikh",
        "Notcoin_flags",
        "Pudgy_Penguins_Cool_Blue_Pengu",
        "Pudgy_and_Friends_Pengu_x_NASCAR",
        "Not_Pixel_Cute_pack",
        "Bored_Stickers_3278",
        "Not_Pixel_Random_memes"
    ]
    
    print(f"\nViewing top {min(count, len(top_stickers))} most valuable sticker cards:\n")
    
    # Display each top card
    for i, sticker in enumerate(top_stickers[:count], 1):
        card_name = f"{sticker}_price_card.png"
        card_path = os.path.join(directory, card_name)
        
        if os.path.exists(card_path):
            print(f"{i}. {card_name}")
            
            # Try to display the image
            try:
                # For Linux
                if sys.platform.startswith('linux'):
                    subprocess.run(['xdg-open', card_path], check=False)
                # For macOS
                elif sys.platform == 'darwin':
                    subprocess.run(['open', card_path], check=False)
                # For Windows
                elif sys.platform == 'win32':
                    os.startfile(card_path)
                else:
                    # Fallback to PIL
                    img = Image.open(card_path)
                    img.show()
            except Exception as e:
                print(f"Failed to display image: {e}")
        else:
            print(f"{i}. {card_name} - File not found")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="View sticker price cards")
    parser.add_argument("--dir", default=PRICE_CARDS_DIR, help="Directory containing price cards")
    parser.add_argument("--random", type=int, help="View a random sample of price cards")
    parser.add_argument("--search", help="Search for specific price cards")
    parser.add_argument("--top", action="store_true", help="View top 10 most valuable sticker cards")
    
    args = parser.parse_args()
    
    if args.random:
        view_random_cards(args.dir, args.random)
    elif args.search:
        view_specific_card(args.dir, args.search)
    elif args.top:
        view_top_cards(args.dir)
    else:
        # Default: list all cards
        cards = list_price_cards(args.dir)
        print(f"\nFound {len(cards)} price cards in {args.dir}:\n")
        for i, card in enumerate(sorted(cards), 1):
            print(f"{i}. {card}")

if __name__ == "__main__":
    main() 