#!/usr/bin/env python3
"""
Sticker Integration for Telegram Bot

This module integrates sticker price cards into the main Telegram bot,
providing the same functionality as gift cards but for stickers.
"""

import os
import json
import logging
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from difflib import get_close_matches
from premium_system import premium_system
from bot_config import DEFAULT_MRKT_LINK, DEFAULT_PALACE_LINK
import stickers_tools_api as sticker_api

# Configure logging
logger = logging.getLogger(__name__)

# Path to sticker price data and cards
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STICKER_PRICE_DATA_FILE = os.path.join(SCRIPT_DIR, "sticker_price_results.json")
STICKER_CARDS_DIR = os.path.join(SCRIPT_DIR, "Sticker_Price_Cards")

# Sticker keyword mappings for better matching
STICKER_KEYWORDS = {
    # Natural language mappings
    "smile": ["Smileface pack"],
    "smile face": ["Smileface pack"],
    "smileface": ["Smileface pack"],
    "happy": ["Smileface pack"],
    "cute": ["Cute pack"],
    "cute pack": ["Cute pack"],
    "cute stickers": ["Cute pack"],
    
    # Pixel-related mappings
    "pixel": [
        "Pixel phrases",
        "MacPixel",
        "Vice Pixel", 
        "Pixioznik",
        "Zompixel",
        "Grass Pixel",
        "SuperPixel",
        "DOGS Pixel",
        "Diamond Pixel",
        "Pixanos",
        "Retro Pixel",
        "Error Pixel"
    ],
    "pixels": [
        "Pixel phrases",
        "MacPixel",
        "Vice Pixel", 
        "Pixioznik",
        "Zompixel",
        "Grass Pixel",
        "SuperPixel",
        "DOGS Pixel",
        "Diamond Pixel",
        "Pixanos",
        "Retro Pixel",
        "Error Pixel"
    ],
    "pixel art": [
        "Pixel phrases",
        "MacPixel",
        "Vice Pixel", 
        "Pixioznik",
        "Zompixel",
        "Grass Pixel",
        "SuperPixel",
        "DOGS Pixel",
        "Diamond Pixel",
        "Pixanos",
        "Retro Pixel",
        "Error Pixel"
    ],
    "8bit": [
        "Pixel phrases",
        "MacPixel",
        "Vice Pixel", 
        "Pixioznik",
        "Zompixel",
        "Grass Pixel",
        "SuperPixel",
        "DOGS Pixel",
        "Diamond Pixel",
        "Pixanos",
        "Retro Pixel",
        "Error Pixel"
    ],
    "retro": ["Retro Pixel"],
    "vintage": ["Retro Pixel"],
    "old school": ["Retro Pixel"],
    "classic": ["Retro Pixel"],
    "diamond": ["Diamond Pixel"],
    "crystal": ["Diamond Pixel"],
    "shiny": ["Diamond Pixel"],
    "grass": ["Grass Pixel"],
    "nature": ["Grass Pixel"],
    "green": ["Grass Pixel"],
    "error": ["Error Pixel"],
    "bug": ["Error Pixel"],
    "glitch": ["Error Pixel"],
    "broken": ["Error Pixel"],
    "super": ["SuperPixel"],
    "power": ["SuperPixel"],
    "strong": ["SuperPixel"],
    "zombie": ["Zompixel"],
    "undead": ["Zompixel"],
    "horror": ["Zompixel"],
    "scary": ["Zompixel"],
    "dogs": ["DOGS Pixel"],
    "dog": ["Dogs OG"],
    "dogs og": ["Dogs OG"],
    "puppy": ["Dogs OG"],
    "canine": ["Dogs OG"],
    "pet": ["Dogs OG"],
    "mac": ["MacPixel"],
    "apple": ["MacPixel"],
    "computer": ["MacPixel"],
    "vice": ["Vice Pixel"],
    "crime": ["Vice Pixel"],
    "gangster": ["Vice Pixel"],
    "cool": ["Vice Pixel"],
    
    # Penguin-related mappings
    "pengu": [
        "Pengu x Baby Shark",
        "Pengu x NASCAR", 
        "Pengu Valentines",
        "Pengu CNY",
        "Blue Pengu",
        "Cool Blue Pengu"
    ],
    "penguin": [
        "Pengu x Baby Shark",
        "Pengu x NASCAR", 
        "Pengu Valentines",
        "Pengu CNY",
        "Blue Pengu",
        "Cool Blue Pengu"
    ],
    "penguins": [
        "Pengu x Baby Shark",
        "Pengu x NASCAR", 
        "Pengu Valentines",
        "Pengu CNY",
        "Blue Pengu",
        "Cool Blue Pengu"
    ],
    "baby shark": [
        "Pengu x Baby Shark",
        "Lil Pudgys x Baby Shark"
    ],
    "shark": [
        "Pengu x Baby Shark",
        "Lil Pudgys x Baby Shark"
    ],
    "nascar": ["Pengu x NASCAR"],
    "racing": ["Pengu x NASCAR"],
    "car": ["Pengu x NASCAR"],
    "valentine": ["Pengu Valentines"],
    "valentines": ["Pengu Valentines"],
    "love": ["Pengu Valentines"],
    "heart": ["Pengu Valentines"],
    "romance": ["Pengu Valentines"],
    "cny": ["Pengu CNY"],
    "chinese": ["Pengu CNY"],
    "new year": ["Pengu CNY"],
    "lunar": ["Pengu CNY"],
    "blue": ["Blue Pengu", "Cool Blue Pengu"],
    "cool blue": ["Cool Blue Pengu"],
    
    # Meme-related mappings
    "memes": [
        "Films memes",
        "Random memes", 
        "Not Memes",
        "The Memes"
    ],
    "meme": [
        "Films memes",
        "Random memes", 
        "Not Memes",
        "The Memes"
    ],
    "funny": [
        "Films memes",
        "Random memes", 
        "Not Memes",
        "The Memes"
    ],
    "humor": [
        "Films memes",
        "Random memes", 
        "Not Memes",
        "The Memes"
    ],
    "joke": [
        "Films memes",
        "Random memes", 
        "Not Memes",
        "The Memes"
    ],
    "film": ["Films memes"],
    "movie": ["Films memes"],
    "cinema": ["Films memes"],
    "random": ["Random memes"],
    "random memes": ["Random memes"],
    
    # Bone-related mappings
    "bone": [
        "Gold bone",
        "Silver bone"
    ],
    "bones": [
        "Gold bone",
        "Silver bone"
    ],
    "gold": ["Gold bone"],
    "silver": ["Silver bone"],
    "precious": ["Gold bone", "Silver bone"],
    "metal": ["Gold bone", "Silver bone"],
    
    # Ape-related mappings
    "ape": [
        "Bored Stickers"
    ],
    "monkey": [
        "Bored Stickers"
    ],
    "board sticker": [
        "Bored Stickers"
    ],
    "byac": [
        "Bored Stickers"
    ],
    "bored": [
        "Bored Stickers"
    ],
    "bored ape": [
        "Bored Stickers"
    ],
    "bored stickers": [
        "Bored Stickers"
    ],
    "bayc": [
        "Bored Stickers"
    ],
    "yacht club": [
        "Bored Stickers"
    ],
    "yacht": [
        "Bored Stickers"
    ],
    
    # Blum-related mappings
    "blum": [
        "Blum"
    ],
    "blum bunny": ["Blum"],
    "blum cat": ["Blum"],
    "blum cook": ["Blum"],
    "blum worker": ["Blum"],
    "bunny": ["Blum"],
    "rabbit": ["Blum"],
    "cat": ["Blum"],
    "kitty": ["Blum"],
    "feline": ["Blum"],
    "cook": ["Blum"],
    "chef": ["Blum"],
    "kitchen": ["Blum"],
    "worker": ["Blum"],
    "work": ["Blum"],
    "job": ["Blum"],
    
    # Flappy Bird mappings
    "flappy": [
        "Flappy Bird"
    ],
    "bird": [
        "Flappy Bird"
    ],
    "birds": [
        "Flappy Bird"
    ],
    "flying": [
        "Flappy Bird"
    ],
    "wing": [
        "Flappy Bird"
    ],
    "wings": [
        "Flappy Bird"
    ],
    "flight": [
        "Flappy Bird"
    ],
    "glide": [
        "Flappy Bird"
    ],
    "frost": [
        "Flappy Bird"
    ],
    "ice": [
        "Flappy Bird"
    ],
    "cold": [
        "Flappy Bird"
    ],
    "ruby": [
        "Flappy Bird"
    ],
    "red": [
        "Flappy Bird"
    ],
    "blue wing": [
        "Flappy Bird"
    ],
    "blush": [
        "Flappy Bird"
    ],
    "light": [
        "Flappy Bird"
    ],
    
    # Pudgy-related mappings
    "pudgy": [
        "Pudgy Penguins",
        "Pudgy & Friends",
        "Lil Pudgys"
    ],
    "pudgys": [
        "Pudgy Penguins",
        "Pudgy & Friends",
        "Lil Pudgys"
    ],
    "pudgy penguin": [
        "Pudgy Penguins"
    ],
    "pudgy penguins": [
        "Pudgy Penguins"
    ],
    "lil pudgy": [
        "Lil Pudgys"
    ],
    "lil pudgys": [
        "Lil Pudgys"
    ],
    "little pudgy": [
        "Lil Pudgys"
    ],
    "baby pudgy": [
        "Lil Pudgys"
    ],
    "friends": [
        "Pudgy & Friends"
    ],
    "pudgy friends": [
        "Pudgy & Friends"
    ],
    
    # Not-related mappings
    "not": [
        "Not Pixel",
        "Notcoin"
    ],
    "not pixel": [
        "Not Pixel"
    ],
    "notcoin": [
        "Notcoin"
    ],
    "coin": [
        "Notcoin"
    ],
    "crypto": [
        "Notcoin"
    ],
    "token": [
        "Notcoin"
    ],
    "currency": [
        "Notcoin"
    ],
    
    # Lost Dogs mappings
    "lost": [
        "Lost Dogs"
    ],
    "lost dog": [
        "Lost Dogs"
    ],
    "lost dogs": [
        "Lost Dogs"
    ],
    "missing": [
        "Lost Dogs"
    ],
    "search": [
        "Lost Dogs"
    ],
    "find": [
        "Lost Dogs"
    ],
    
    # Lazy & Rich mappings
    "lazy": [
        "Lazy & Rich"
    ],
    "rich": [
        "Lazy & Rich"
    ],
    "lazy rich": [
        "Lazy & Rich"
    ],
    "lazy and rich": [
        "Lazy & Rich"
    ],
    "money": [
        "Lazy & Rich"
    ],
    "wealth": [
        "Lazy & Rich"
    ],
    "chill": [
        "Lazy & Rich"
    ],
    "relax": [
        "Lazy & Rich"
    ],
    "sloth": [
        "Lazy & Rich"
    ],
    "capital": [
        "Lazy & Rich"
    ],
    
    # Cattea mappings
    "cattea": [
        "Cattea Life"
    ],
    "cat tea": [
        "Cattea Life"
    ],
    "cat": [
        "Cattea Life",
        "Blum"
    ],
    "tea": [
        "Cattea Life"
    ],
    "chaos": [
        "Cattea Life"
    ],
    "cattea chaos": [
        "Cattea Life"
    ],
    
    # Doodles mappings
    "doodles": [
        "Doodles"
    ],
    "doodle": [
        "Doodles"
    ],
    "draw": [
        "Doodles"
    ],
    "art": [
        "Doodles"
    ],
    "sketch": [
        "Doodles"
    ],
    "dark": [
        "Doodles"
    ],
    "dark mode": [
        "Doodles"
    ],
    
    # Kudai mappings
    "kudai": [
        "Kudai"
    ],
    "gmi": [
        "Kudai"
    ],
    "ngmi": [
        "Kudai"
    ],
    "gonna make it": [
        "Kudai"
    ],
    "not gonna make it": [
        "Kudai"
    ],
    "success": [
        "Kudai"
    ],
    "failure": [
        "Kudai"
    ],
    
    # BabyDoge mappings
    "babydoge": [
        "BabyDoge"
    ],
    "baby doge": [
        "BabyDoge"
    ],
    "doge": [
        "BabyDoge"
    ],
    "shiba": [
        "BabyDoge"
    ],
    "meme coin": [
        "BabyDoge"
    ],
    "mememania": [
        "BabyDoge"
    ],
    
    # PUCCA mappings
    "pucca": [
        "PUCCA"
    ],
    "mood": [
        "PUCCA"
    ],
    "moods": [
        "PUCCA"
    ],
    "emotion": [
        "PUCCA"
    ],
    "feeling": [
        "PUCCA"
    ],
    "expression": [
        "PUCCA"
    ],
    
    # Azuki mappings
    "azuki": [
        "Azuki"
    ],
    "shao": [
        "Azuki"
    ],
    "anime": [
        "Azuki"
    ],
    "japanese": [
        "Azuki"
    ],
    "manga": [
        "Azuki"
    ],
    
    # Ric Flair mappings
    "ric": [
        "Ric Flair"
    ],
    "flair": [
        "Ric Flair"
    ],
    "ric flair": [
        "Ric Flair"
    ],
    "wrestling": [
        "Ric Flair"
    ],
    "wrestler": [
        "Ric Flair"
    ],
    "wrestle": [
        "Ric Flair"
    ],
    "woo": [
        "Ric Flair"
    ],
    
    # Smeshariki mappings
    "smeshariki": [
        "Smeshariki"
    ],
    "chamomile": [
        "Smeshariki"
    ],
    "valley": [
        "Smeshariki"
    ],
    "chamomile valley": [
        "Smeshariki"
    ],
    "russian": [
        "Smeshariki"
    ],
    "cartoon": [
        "Smeshariki"
    ],
    
    # SUNDOG mappings
    "sundog": [
        "SUNDOG"
    ],
    "sun": [
        "SUNDOG"
    ],
    "solar": [
        "SUNDOG"
    ],
    "to the sun": [
        "SUNDOG"
    ],
    "space": [
        "SUNDOG"
    ],
    "cosmic": [
        "SUNDOG"
    ],
    
    # WAGMI HUB mappings
    "wagmi": [
        "WAGMI HUB"
    ],
    "hub": [
        "WAGMI HUB"
    ],
    "wagmi hub": [
        "WAGMI HUB"
    ],
    "egg": [
        "WAGMI HUB"
    ],
    "hammer": [
        "WAGMI HUB"
    ],
    "egg and hammer": [
        "WAGMI HUB"
    ],
    "ai": [
        "WAGMI HUB"
    ],
    "agent": [
        "WAGMI HUB"
    ],
    "ai agent": [
        "WAGMI HUB"
    ],
    "artificial intelligence": [
        "WAGMI HUB"
    ]
}

def load_sticker_price_data():
    """Load sticker price data from JSON file."""
    try:
        if os.path.exists(STICKER_PRICE_DATA_FILE):
            with open(STICKER_PRICE_DATA_FILE, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded sticker price data with {len(data.get('stickers_with_prices', []))} entries")
                return data
        else:
            logger.warning(f"Sticker price data file not found: {STICKER_PRICE_DATA_FILE}")
            return {"stickers_with_prices": []}
    except Exception as e:
        logger.error(f"Error loading sticker price data: {e}")
        return {"stickers_with_prices": []}

def get_sticker_card_path(collection, sticker):
    """Get the path to a sticker price card."""
    # Use the same normalization as the price card generator
    def normalize_name(name):
        import re
        name = name.strip().lower()
        name = re.sub(r'[^a-z0-9]', '_', name)
        name = re.sub(r'_+', '_', name)
        return name.strip('_')
    
    # Normalize collection and sticker names for file matching
    collection_normalized = normalize_name(collection)
    sticker_normalized = normalize_name(sticker)
    
    filename = f"{collection_normalized}_{sticker_normalized}_price_card.png"
    filepath = os.path.join(STICKER_CARDS_DIR, filename)
    
    if os.path.exists(filepath):
        return filepath
    
    # Try alternative naming patterns
    alt_filename = f"{collection_normalized}_{sticker_normalized}_card.png"
    alt_filepath = os.path.join(STICKER_CARDS_DIR, alt_filename)
    
    if os.path.exists(alt_filepath):
        return alt_filepath
    
    return None

def find_matching_stickers(query):
    """Find stickers that match the query with exact name matching only."""
    query_lower = query.lower().strip()
    
    # Load sticker data
    sticker_data = load_sticker_price_data()
    stickers = sticker_data.get("stickers_with_prices", [])
    collections = set(item["collection"] for item in stickers)
    
    # 1. Try exact collection name match (case-insensitive, whole phrase)
    for collection in collections:
        if query_lower == collection.lower():
            packs = get_stickers_in_collection(collection)
            return [(collection, pack) for pack in packs]
    
    # 2. Try exact sticker name matching only
    matches = []
    for sticker_info in stickers:
        collection = sticker_info["collection"]
        sticker = sticker_info["sticker"]
        sticker_lower = sticker.lower()
        
        # Only exact matches allowed
        if query_lower == sticker_lower:
            matches.append((collection, sticker))
        # Also check collection + sticker format
        elif query_lower == f"{collection.lower()} {sticker_lower}":
            matches.append((collection, sticker))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_matches = []
    for match in matches:
        if match not in seen:
            seen.add(match)
            unique_matches.append(match)
    
    return unique_matches

def get_sticker_suggestions(query):
    """Get intelligent suggestions for sticker searches when no exact match is found."""
    query_lower = query.lower().strip()
    suggestions = []
    
    # Common user queries and their suggestions
    suggestion_map = {
        "smile": ["Try: 'smile face', 'happy', 'cute'"],
        "happy": ["Try: 'smile face', 'cute', 'mood'"],
        "cute": ["Try: 'cute pack', 'smile face', 'penguin'"],
        "pixel": ["Try: 'pixel art', 'retro', '8bit', 'vintage'"],
        "penguin": ["Try: 'pengu', 'pudgy', 'blue pengu'"],
        "dog": ["Try: 'dogs og', 'puppy', 'canine'"],
        "cat": ["Try: 'cattea', 'kitty', 'feline'"],
        "bird": ["Try: 'flappy bird', 'wings', 'flying'"],
        "meme": ["Try: 'memes', 'funny', 'random memes'"],
        "ape": ["Try: 'bored stickers', 'monkey', 'bayc'"],
        "bone": ["Try: 'gold bone', 'silver bone', 'precious'"],
        "love": ["Try: 'valentines', 'heart', 'romance'"],
        "money": ["Try: 'lazy rich', 'wealth', 'capital'"],
        "art": ["Try: 'doodles', 'pixel art', 'draw'"],
        "anime": ["Try: 'azuki', 'japanese', 'manga'"],
        "wrestling": ["Try: 'ric flair', 'wrestler', 'woo'"],
        "crypto": ["Try: 'notcoin', 'coin', 'token'"],
        "ai": ["Try: 'wagmi hub', 'ai agent', 'artificial intelligence'"],
        "space": ["Try: 'sundog', 'sun', 'cosmic'"],
        "russian": ["Try: 'smeshariki', 'chamomile valley'"],
        "cartoon": ["Try: 'smeshariki', 'doodles', 'anime'"]
    }
    
    # Check for exact suggestion matches
    for key, suggestion in suggestion_map.items():
        if key in query_lower or query_lower in key:
            suggestions.extend(suggestion)
    
    # Add general suggestions based on query words
    query_words = query_lower.split()
    for word in query_words:
        if len(word) >= 3:
            if "pixel" in word:
                suggestions.append("Try: 'pixel art', 'retro', '8bit'")
            elif "pengu" in word or "penguin" in word:
                suggestions.append("Try: 'pengu', 'pudgy', 'blue pengu'")
            elif "dog" in word:
                suggestions.append("Try: 'dogs og', 'puppy'")
            elif "cat" in word:
                suggestions.append("Try: 'cattea', 'kitty'")
            elif "bird" in word:
                suggestions.append("Try: 'flappy bird', 'wings'")
            elif "meme" in word:
                suggestions.append("Try: 'memes', 'funny'")
            elif "ape" in word:
                suggestions.append("Try: 'bored stickers', 'bayc'")
            elif "bone" in word:
                suggestions.append("Try: 'gold bone', 'silver bone'")
            elif "love" in word or "heart" in word:
                suggestions.append("Try: 'valentines', 'romance'")
            elif "money" in word or "rich" in word:
                suggestions.append("Try: 'lazy rich', 'wealth'")
            elif "art" in word or "draw" in word:
                suggestions.append("Try: 'doodles', 'pixel art'")
    
    # Remove duplicates
    suggestions = list(set(suggestions))
    
    # Add general help if no specific suggestions
    if not suggestions:
        suggestions = [
            "Try: 'pixel', 'penguin', 'dog', 'cat', 'bird', 'meme', 'ape'",
            "Or browse all collections with /sticker"
        ]
    
    return suggestions[:3]  # Limit to 3 suggestions

def format_sticker_price_message(sticker_info):
    """Format sticker price information into a readable message."""
    collection = sticker_info["collection"]
    sticker = sticker_info["sticker"]
    
    # Simplified caption - only collection and sticker name
    message = f"*{collection} - {sticker}*"
    
    return message

async def send_sticker_card(update: Update, context: ContextTypes.DEFAULT_TYPE, collection, sticker, edit_message_id=None, chat_id=None):
    """Send a sticker price card with buttons."""
    # Get the card path
    card_path = get_sticker_card_path(collection, sticker)
    
    if not card_path:
        error_msg = f"Sorry, couldn't find the sticker card for {collection} - {sticker}."
        if edit_message_id and chat_id:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=edit_message_id,
                text=error_msg
            )
        else:
            await update.message.reply_text(error_msg)
        return
    
    # Get sticker price info from stickers.tools API
    price_info = sticker_api.get_sticker_price(collection, sticker)
    if not price_info:
        await update.message.reply_text(f"No price info for {collection} - {sticker}.")
        return
    
    # Determine group id for premium
    group_id = chat_id if chat_id is not None else update.effective_chat.id
    is_premium = premium_system.is_group_premium(group_id)
    links = premium_system.get_premium_links(group_id) if is_premium else None
    mrkt_link = links.get('mrkt_link') if links and links.get('mrkt_link') else DEFAULT_MRKT_LINK
    palace_link = links.get('palace_link') if links and links.get('palace_link') else DEFAULT_PALACE_LINK

    # Create keyboard with Buy/Sell and Back to Collections on the same row, then Delete below
    keyboard = [
        [
            InlineKeyboardButton("💰 Buy/Sell Stickers", callback_data=f"sticker_markets_{collection}_{sticker}"),
            InlineKeyboardButton("« Back to Collections", callback_data="sticker_collections")
        ],
        [InlineKeyboardButton("🗑️ Delete", callback_data="delete")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Create caption
    if price_info:
        # Create a proper sticker_info structure for the format function
        sticker_info = {
            "collection": collection,
            "sticker": sticker,
            "price": price_info.get("floor_price_ton", 0),
            "supply": price_info.get("supply", 0)
        }
        base_caption = format_sticker_price_message(sticker_info)
        # Add channel promotion and bot command suggestion
        caption = f"{base_caption}\n\nJoin @The01Studio\nTry @CollectibleKITbot"
    else:
        base_caption = f"{collection} - {sticker}"
        # Add channel promotion and bot command suggestion
        caption = f"{base_caption}\n\nJoin @The01Studio\nTry @CollectibleKITbot"
    
    try:
        # Send or edit the message with the photo
        if edit_message_id and chat_id:
            # When editing an existing message
            with open(card_path, 'rb') as photo_file:
                await context.bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=edit_message_id,
                    media=InputMediaPhoto(
                        media=photo_file,
                        caption=caption,
                        parse_mode='Markdown'
                    ),
                    reply_markup=reply_markup
                )
        else:
            # When sending a new message
            sent_message = await update.message.reply_photo(
                photo=open(card_path, 'rb'),
                caption=caption,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            # Register the message owner in the database for delete permission tracking
            try:
                from rate_limiter import register_message
                user_id = update.effective_user.id
                chat_id = update.effective_chat.id
                register_message(user_id, chat_id, sent_message.message_id)
                logger.info(f"✅ REGISTERED: Sticker card message {sent_message.message_id} to user {user_id} in chat {chat_id}")
            except ImportError:
                logger.warning("Rate limiter not available, message ownership not registered")
            except Exception as e:
                logger.error(f"Error registering message ownership: {e}")
            
    except Exception as e:
        logger.error(f"Error sending sticker card: {e}")
        if edit_message_id and chat_id:
            try:
                await context.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=edit_message_id,
                    caption=caption,
                    parse_mode='Markdown'
                )
            except:
                pass

def get_sticker_collections():
    """Get list of all available sticker collections."""
    sticker_data = load_sticker_price_data()
    collections = set()
    
    for item in sticker_data.get("stickers_with_prices", []):
        collections.add(item["collection"])
    
    return sorted(list(collections))

def get_stickers_in_collection(collection):
    """Get all stickers in a specific collection."""
    sticker_data = load_sticker_price_data()
    stickers = []
    
    for item in sticker_data.get("stickers_with_prices", []):
        if item["collection"] == collection:
            stickers.append(item["sticker"])
    
    return sorted(stickers)

def get_sticker_keyboard(collection=None, page=0):
    """Get keyboard for sticker browsing with pagination."""
    if collection:
        # Show stickers in a specific collection
        stickers = get_stickers_in_collection(collection)
        keyboard = []
        
        # Special pagination for Dogs OG collection (68 stickers)
        if collection == "Dogs OG":
            items_per_page = 12  # 6 rows of 2 stickers each
            total_pages = (len(stickers) + items_per_page - 1) // items_per_page
            
            # Ensure page is within bounds
            page = max(0, min(page, total_pages - 1))
            
            # Get stickers for current page
            start_idx = page * items_per_page
            end_idx = min(start_idx + items_per_page, len(stickers))
            page_stickers = stickers[start_idx:end_idx]
            
            row = []
            for i, sticker in enumerate(page_stickers):
                row.append(InlineKeyboardButton(sticker, callback_data=f"sticker_{collection}_{sticker}"))
                if len(row) == 2:  # Always 2 columns
                    keyboard.append(row)
                    row = []
            
            # Add any remaining items in the last row
            if row:
                keyboard.append(row)
            
            # Add navigation buttons
            nav_row = []
            if page > 0:
                nav_row.append(InlineKeyboardButton("← Back", callback_data=f"sticker_paginate_{collection.replace(' ', '_')}_{page-1}"))
            if page < total_pages - 1:
                nav_row.append(InlineKeyboardButton("Next →", callback_data=f"sticker_paginate_{collection.replace(' ', '_')}_{page+1}"))
            
            if nav_row:
                keyboard.append(nav_row)
            
            # Add back to collections button
            keyboard.append([InlineKeyboardButton("« Back to Collections", callback_data="sticker_collections")])
            
        else:
            # Regular handling for other collections
            row = []
            for i, sticker in enumerate(stickers):
                row.append(InlineKeyboardButton(sticker, callback_data=f"sticker_{collection}_{sticker}"))
                if len(row) == 2 or i == len(stickers) - 1:
                    keyboard.append(row)
                    row = []
            
            # Add back button
            keyboard.append([InlineKeyboardButton("« Back to Collections", callback_data="sticker_collections")])
        
    else:
        # Show collections with pagination
        collections = get_sticker_collections()
        items_per_page = 12  # Show 12 collections per page (6 rows of 2)
        total_pages = (len(collections) + items_per_page - 1) // items_per_page
        
        # Ensure page is within bounds
        page = max(0, min(page, total_pages - 1))
        
        # Get collections for current page
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, len(collections))
        page_collections = collections[start_idx:end_idx]
        
        keyboard = []
        row = []
        
        for i, collection_name in enumerate(page_collections):
            row.append(InlineKeyboardButton(collection_name, callback_data=f"sticker_collection_{collection_name}"))
            if len(row) == 2:  # Always 2 columns
                keyboard.append(row)
                row = []
        
        # Add any remaining items in the last row
        if row:
            keyboard.append(row)
        
        # Add navigation buttons
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("← Back", callback_data=f"sticker_page_{page-1}"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("Next →", callback_data=f"sticker_page_{page+1}"))
        
        if nav_row:
            keyboard.append(nav_row)
    
    return InlineKeyboardMarkup(keyboard)

async def handle_sticker_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle sticker-related callback queries."""
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    
    logger.info(f"Sticker callback from user {user_id} in chat {chat_id} for message {message_id}: {data}")
    
    # Check ownership for ALL button interactions (except delete which has its own check)
    if data != "delete":
        try:
            from rate_limiter import can_delete_message, get_message_owner
            logger.info(f"🔒 Checking ownership for button '{data}' - User: {user_id}, Chat: {chat_id}, Message: {message_id}")
            
            # First, try the normal ownership check
            is_owner = can_delete_message(user_id, chat_id, message_id)
            
            if not is_owner:
                # User is not the owner of this message
                # Get the actual owner for logging
                actual_owner = get_message_owner(chat_id, message_id)
                if actual_owner:
                    logger.warning(f"🚫 UNAUTHORIZED ACCESS: User {user_id} tried to use button '{data}' on message {message_id} owned by user {actual_owner}")
                else:
                    logger.warning(f"🚫 UNAUTHORIZED ACCESS: User {user_id} tried to use button '{data}' on message {message_id} (no owner recorded)")
                
                await query.answer("🚫 Only the user who requested this sticker can use these buttons.", show_alert=True)
                return
            else:
                logger.info(f"✅ AUTHORIZED: User {user_id} can use button '{data}' on message {message_id}")
                
        except ImportError:
            # Rate limiter not available, continue without checking
            logger.warning("Rate limiter not available, continuing without ownership check")
        except Exception as e:
            logger.error(f"Error checking message ownership: {e}")
            # For safety, deny access if there's an error checking ownership
            await query.answer("🚫 Error checking permissions. Please try again.", show_alert=True)
            return
    
    # Check if this is a delete button
    if data == "delete":
        # Check if the user is the owner of this message
        try:
            from rate_limiter import can_delete_message, get_message_owner
            is_owner = can_delete_message(user_id, chat_id, message_id)
            
            if not is_owner:
                # User is not the owner of this message
                actual_owner = get_message_owner(chat_id, message_id)
                if actual_owner:
                    logger.warning(f"🚫 UNAUTHORIZED DELETE: User {user_id} tried to delete message {message_id} owned by user {actual_owner}")
                else:
                    logger.warning(f"🚫 UNAUTHORIZED DELETE: User {user_id} tried to delete message {message_id} (no owner recorded)")
                
                await query.answer("🚫 Only the user who requested this sticker can delete this message.", show_alert=True)
                return
            else:
                logger.info(f"✅ AUTHORIZED DELETE: User {user_id} can delete message {message_id}")
        except ImportError:
            # Rate limiter not available, continue without checking
            logger.warning("Rate limiter not available, continuing without ownership check")
        except Exception as e:
            logger.error(f"Error checking message ownership for delete: {e}")
            await query.answer("🚫 Error checking permissions. Please try again.", show_alert=True)
            return
        
        # User is authorized to delete the message
        try:
            await query.message.delete()
            logger.info(f"Message {message_id} deleted successfully by user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            await query.answer("Cannot delete this message", show_alert=True)
        return
    
    # User is authorized to use the buttons
    await query.answer()
    
    if data == "sticker_collections":
        # Show collections
        reply_markup = get_sticker_keyboard()
        # If the message is a photo, delete and send new text message
        if query.message.photo:
            try:
                await query.message.delete()
            except Exception as e:
                logger.error(f"Error deleting sticker card for back to collections: {e}")
            sent_message = await query.message.chat.send_message(
                "🌟 Choose a sticker collection to browse:",
                reply_markup=reply_markup
            )
            
            # Register the message owner for the new collections message
            try:
                from rate_limiter import register_message
                register_message(user_id, chat_id, sent_message.message_id)
                logger.info(f"✅ REGISTERED: Collections message {sent_message.message_id} to user {user_id} in chat {chat_id}")
            except ImportError:
                logger.warning("Rate limiter not available, message ownership not registered")
            except Exception as e:
                logger.error(f"Error registering message ownership: {e}")
        else:
            try:
                await query.edit_message_text(
                    "🌟 Choose a sticker collection to browse:",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error editing message text: {e}")
                # Fallback: delete and send new message
                try:
                    await query.message.delete()
                    sent_message = await query.message.chat.send_message(
                        "🌟 Choose a sticker collection to browse:",
                        reply_markup=reply_markup
                    )
                    # Register the message owner
                    try:
                        from rate_limiter import register_message
                        register_message(user_id, chat_id, sent_message.message_id)
                        logger.info(f"✅ REGISTERED: Fallback collections message {sent_message.message_id} to user {user_id} in chat {chat_id}")
                    except ImportError:
                        logger.warning("Rate limiter not available, message ownership not registered")
                    except Exception as e:
                        logger.error(f"Error registering message ownership: {e}")
                except Exception as e2:
                    logger.error(f"Error in fallback message handling: {e2}")
    elif data.startswith("sticker_page_"):
        # Handle pagination
        try:
            page = int(data.replace("sticker_page_", ""))
            reply_markup = get_sticker_keyboard(page=page)
            await query.edit_message_text(
                "🌟 Choose a sticker collection to browse:",
                reply_markup=reply_markup
            )
        except ValueError:
            await query.answer("Invalid page number", show_alert=True)
    elif data.startswith("sticker_collection_"):
        # Show stickers in a collection
        collection = data.replace("sticker_collection_", "")
        reply_markup = get_sticker_keyboard(collection=collection)
        await query.edit_message_text(
            f"🌟 Stickers in *{collection}*:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif data.startswith("sticker_markets_"):
        # Show marketplace options
        parts = data.split("_", 3)
        if len(parts) >= 4:
            collection = parts[2]
            sticker = parts[3]
            # Determine group id for premium
            group_id = chat_id
            is_premium = premium_system.is_group_premium(group_id)
            links = premium_system.get_premium_links(group_id) if is_premium else None
            mrkt_link = links.get('mrkt_link') if links and links.get('mrkt_link') else DEFAULT_MRKT_LINK
            palace_link = links.get('palace_link') if links and links.get('palace_link') else DEFAULT_PALACE_LINK
            # Create keyboard with MRKT and Palace buttons, then Back
            keyboard = [
                [
                    InlineKeyboardButton("🛒 MRKT", url=mrkt_link),
                    InlineKeyboardButton("🏰 Palace", url=palace_link)
                ],
                [InlineKeyboardButton("« Back", callback_data=f"sticker_{collection}_{sticker}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup=reply_markup)
    elif data.startswith("sticker_paginate_"):
        # Handle pagination for specific collections (Dogs OG)
        try:
            # Format: sticker_paginate_Dogs_OG_1 -> collection="Dogs OG", page=1
            parts = data.split("_")
            if len(parts) >= 4:
                # Remove "sticker" and "paginate" from the beginning
                collection_parts = parts[2:-1]  # Get all parts except first 2 and last
                page = int(parts[-1])  # Last part is the page number
                collection = " ".join(collection_parts)  # Join with spaces
                logger.info(f"Pagination request: collection={collection}, page={page}")
                reply_markup = get_sticker_keyboard(collection=collection, page=page)
                await query.edit_message_text(
                    f"🌟 Stickers in *{collection}* (Page {page + 1}):",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                await query.answer(f"Page {page + 1}")
            else:
                logger.error(f"Invalid pagination callback data: {data}")
                await query.answer("Invalid pagination request", show_alert=True)
        except Exception as e:
            logger.error(f"Error in pagination handler: {e}")
            await query.answer("Error loading page", show_alert=True)
    elif data.startswith("sticker_"):
        # Show specific sticker
        parts = data.split("_", 2)
        if len(parts) >= 3:
            collection = parts[1]
            sticker = parts[2]
            await send_sticker_card(update, context, collection, sticker, 
                                  edit_message_id=query.message.message_id, 
                                  chat_id=query.message.chat_id)

# Check if sticker functionality is available
def is_sticker_functionality_available():
    """Check if sticker functionality is available."""
    return (os.path.exists(STICKER_PRICE_DATA_FILE) and 
            os.path.exists(STICKER_CARDS_DIR))
