#!/usr/bin/env python3
"""
Create Sticker Data from Directory Structure

This script reads the sticker_collections directory structure and creates
a new sticker_price_results.json file with all collections and stickers
found in the folders.
"""

import os
import json
import re
from datetime import datetime

def normalize_name(name):
    """Normalize name for file operations"""
    name = name.strip().lower()
    name = re.sub(r'[^a-z0-9]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

def prettify_name(name):
    """Convert folder name to display name"""
    # Replace underscores with spaces and capitalize each word
    return ' '.join(word.capitalize() for word in name.replace('_', ' ').split())

def get_collection_display_name(folder_name):
    """Convert folder name to proper collection display name"""
    # Special mappings for collection names
    collection_mappings = {
        'azuki': 'Azuki',
        'babydoge': 'BabyDoge',
        'baby_shark': 'Baby Shark',
        'blum': 'Blum',
        'bored_ape_yacht_club': 'Bored Ape Yacht Club',
        'bored_stickers': 'Bored Stickers',
        'cattea_life': 'Cattea Life',
        'chimpers': 'Chimpers',
        'claynosaurz': 'Claynosaurz',
        'cyberkongz': 'CyberKongz',
        'dogs_og': 'Dogs OG',
        'dogs_rewards': 'Dogs Rewards',
        'dogs_unleashed': 'Dogs Unleashed',
        'doodles': 'Doodles',
        'flappy_bird': 'Flappy Bird',
        'imaginary_ones': 'Imaginary Ones',
        'kudai': 'Kudai',
        'lazy_rich': 'Lazy & Rich',
        'lil_pudgys': 'Lil Pudgys',
        'lost_dogs': 'Lost Dogs',
        'moonbirds': 'Moonbirds',
        'notcoin': 'Notcoin',
        'not_pixel': 'Not Pixel',
        'ponke': 'Ponke',
        'project_soap': 'Project Soap',
        'pucca': 'PUCCA',
        'pudgy_friends': 'Pudgy & Friends',
        'pudgy_penguins': 'Pudgy Penguins',
        'ric_flair': 'Ric Flair',
        'sappy': 'Sappy',
        'smeshariki': 'Smeshariki',
        'sticker_pack': 'Sticker Pack',
        'sundog': 'SUNDOG',
        'wagmi_hub': 'WAGMI HUB'
    }
    
    return collection_mappings.get(folder_name, prettify_name(folder_name))

def get_sticker_display_name(folder_name):
    """Convert folder name to proper sticker display name"""
    # Special mappings for sticker names
    sticker_mappings = {
        'raizan': 'Raizan',
        'shao': 'Shao',
        'mememania': 'Mememania',
        'doo_doo_moods': 'Doo Doo Moods',
        'bunny': 'Bunny',
        'cap': 'Cap',
        'cat': 'Cat',
        'cook': 'Cook',
        'curly': 'Curly',
        'general': 'General',
        'no': 'No',
        'worker': 'Worker',
        'bored_ape_originals': 'Bored Ape Originals',
        '3151': '3151',
        '3278': '3278',
        '4017': '4017',
        '5824': '5824',
        '6527': '6527',
        '9287': '9287',
        '9765': '9765',
        '9780': '9780',
        'cny_2092': 'CNY 2092',
        'cattea_chaos': 'Cattea Chaos',
        'genesis_energy': 'Genesis Energy',
        'red_rex_pack': 'Red Rex Pack',
        'wilson': 'Wilson',
        'alien': 'Alien',
        'alumni': 'Alumni',
        'anime_ears': 'Anime Ears',
        'asterix': 'Asterix',
        'baseball_bat': 'Baseball Bat',
        'baseball_cap': 'Baseball Cap',
        'blue_eyes_hat': 'Blue Eyes Hat',
        'bodyguard': 'Bodyguard',
        'bow_tie': 'Bow Tie',
        'cherry_glasses': 'Cherry Glasses',
        'cyclist': 'Cyclist',
        'diver': 'Diver',
        'dogtor': 'Dogtor',
        'dog_tyson': 'Dog Tyson',
        'duck': 'Duck',
        'emo_boy': 'Emo Boy',
        'extra_eyes': 'Extra Eyes',
        'frog_glasses': 'Frog Glasses',
        'frog_hat': 'Frog Hat',
        'gentleman': 'Gentleman',
        'gnome': 'Gnome',
        'google_intern_hat': 'Google Intern Hat',
        'green_hair': 'Green Hair',
        'hello_kitty': 'Hello Kitty',
        'hypnotist': 'Hypnotist',
        'ice_cream': 'Ice Cream',
        'jester': 'Jester',
        'kamikaze': 'Kamikaze',
        'kfc': 'KFC',
        'king': 'King',
        'og_king': 'OG King',
        'knitted_hat': 'Knitted Hat',
        'nerd': 'Nerd',
        'newsboy_cap': 'Newsboy Cap',
        'noodles': 'Noodles',
        'nose_glasses': 'Nose Glasses',
        'not_cap': 'Not Cap',
        'og_not_cap': 'OG Not Cap',
        'not_coin': 'Not Coin',
        'one_piece_sanji': 'One Piece Sanji',
        'orange_hat': 'Orange Hat',
        'panama_hat': 'Panama Hat',
        'pilot': 'Pilot',
        'pink_bob': 'Pink Bob',
        'princess': 'Princess',
        'robber': 'Robber',
        'santa_dogs': 'Santa Dogs',
        'scarf': 'Scarf',
        'scary_eyes': 'Scary Eyes',
        'shaggy': 'Shaggy',
        'sharky_dog': 'Sharky Dog',
        'sheikh': 'Sheikh',
        'og_sheikh': 'OG Sheikh',
        'sherlock_holmes': 'Sherlock Holmes',
        'smile': 'Smile',
        'sock_head': 'Sock Head',
        'strawberry_hat': 'Strawberry Hat',
        'tank_driver': 'Tank Driver',
        'tattoo_artist': 'Tattoo Artist',
        'teletubby': 'Teletubby',
        'termidogtor': 'Termidogtor',
        'tin_foil_hat': 'Tin Foil Hat',
        'toast_bread': 'Toast Bread',
        'toddler': 'Toddler',
        'tubeteyka': 'Tubeteyka',
        'unicorn': 'Unicorn',
        'ushanka': 'Ushanka',
        'van_dogh': 'Van Dogh',
        'viking': 'Viking',
        'witch': 'Witch',
        'full_dig': 'Full Dig',
        'gold_bone': 'Gold Bone',
        'silver_bone': 'Silver Bone',
        'bones': 'Bones',
        'doodles_dark_mode': 'Doodles Dark Mode',
        'og_icons': 'OG Icons',
        'blue_wings': 'Blue Wings',
        'blush_flight': 'Blush Flight',
        'frost_flap': 'Frost Flap',
        'light_glide': 'Light Glide',
        'ruby_wings': 'Ruby Wings',
        'panda_warrior': 'Panda Warrior',
        'gmi': 'GMI',
        'ngmi': 'NGMI',
        'chill_or_thrill': 'Chill or Thrill',
        'sloth_capital': 'Sloth Capital',
        'lil_pudgys_x_baby_shark': 'Lil Pudgys x Baby Shark',
        'lost_memeries': 'Lost Memeries',
        'magic_of_the_way': 'Magic of the Way',
        'moonbirds_originals': 'Moonbirds Originals',
        'flags': 'Flags',
        'not_memes': 'Not Memes',
        'cute_pack': 'Cute Pack',
        'diamond_pixel': 'Diamond Pixel',
        'dogs_pixel': 'DOGS Pixel',
        'error_pixel': 'Error Pixel',
        'films_memes': 'Films Memes',
        'grass_pixel': 'Grass Pixel',
        'macpixel': 'MacPixel',
        'pixanos': 'Pixanos',
        'pixel_phrases': 'Pixel Phrases',
        'pixioznik': 'Pixioznik',
        'random_memes': 'Random Memes',
        'retro_pixel': 'Retro Pixel',
        'smileface_pack': 'Smileface Pack',
        'superpixel': 'SuperPixel',
        'tournament_s1': 'Tournament S1',
        'vice_pixel': 'Vice Pixel',
        'zompixel': 'Zompixel',
        'ponke_day_ones': 'Ponke Day Ones',
        'tyler_mode_on': 'Tyler Mode: On',
        'pucca_moods': 'Pucca Moods',
        'pengu_x_baby_shark': 'Pengu x Baby Shark',
        'pengu_x_nascar': 'Pengu x NASCAR',
        'blue_pengu': 'Blue Pengu',
        'cool_blue_pengu': 'Cool Blue Pengu',
        'pengu_cny': 'Pengu CNY',
        'pengu_valentines': 'Pengu Valentines',
        'ric_flair': 'Ric Flair',
        'sappy_originals': 'Sappy Originals',
        'chamomile_valley': 'Chamomile Valley',
        'the_memes': 'The Memes',
        'freedom': 'Freedom',
        'to_the_sun': 'To the Sun',
        'egg_hammer': 'Egg & Hammer',
        'wagmi_ai_agent': 'WAGMI AI Agent'
    }
    
    return sticker_mappings.get(folder_name, prettify_name(folder_name))

def scan_sticker_collections():
    """Scan the sticker_collections directory and create data structure"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    collections_dir = os.path.join(script_dir, "sticker_collections")
    
    if not os.path.exists(collections_dir):
        print(f"Error: {collections_dir} not found")
        return None
    
    stickers_data = []
    
    # Scan all collection folders
    for collection_folder in os.listdir(collections_dir):
        collection_path = os.path.join(collections_dir, collection_folder)
        
        if not os.path.isdir(collection_path):
            continue
            
        collection_display_name = get_collection_display_name(collection_folder)
        
        # Scan all sticker folders within the collection
        for sticker_folder in os.listdir(collection_path):
            sticker_path = os.path.join(collection_path, sticker_folder)
            
            if not os.path.isdir(sticker_path):
                continue
                
            sticker_display_name = get_sticker_display_name(sticker_folder)
            
            # Create sticker entry
            sticker_entry = {
                "collection": collection_display_name,
                "sticker": sticker_display_name,
                "price": 0.0,  # Default price, will be updated by API
                "supply": 0,   # Default supply, will be updated by API
                "is_real_data": False,
                "price_change_percent": 0.0,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            stickers_data.append(sticker_entry)
    
    return stickers_data

def main():
    """Main function to create the sticker data file"""
    print("Scanning sticker collections directory...")
    
    stickers_data = scan_sticker_collections()
    
    if not stickers_data:
        print("No sticker data found")
        return
    
    # Create the data structure
    data = {
        "timestamp": datetime.now().timestamp(),
        "human_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_templates": len(stickers_data),
        "successful": len(stickers_data),
        "failed": 0,
        "stickers_with_prices": stickers_data
    }
    
    # Save to file
    output_file = "sticker_price_results.json"
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Created {output_file} with {len(stickers_data)} stickers from {len(set(s['collection'] for s in stickers_data))} collections")
    
    # Show collections
    collections = sorted(set(s['collection'] for s in stickers_data))
    print(f"\nCollections found:")
    for collection in collections:
        count = len([s for s in stickers_data if s['collection'] == collection])
        print(f"  {collection}: {count} stickers")

if __name__ == "__main__":
    main() 