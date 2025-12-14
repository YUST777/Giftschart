# Telegram Inline Mode with CDN Integration - Complete Guide

## 📋 Table of Contents
- [Overview](#overview)
- [What is Telegram Inline Mode?](#what-is-telegram-inline-mode)
- [System Architecture](#system-architecture)
- [How It Works](#how-it-works)
- [CDN Server Implementation](#cdn-server-implementation)
- [Bot Inline Query Handler](#bot-inline-query-handler)
- [Image Display Flow](#image-display-flow)
- [Code Examples](#code-examples)
- [Building Your Own System](#building-your-own-system)

---

## Overview

This document explains how the GiftsChart Telegram bot implements inline mode with a CDN (Content Delivery Network) to display gift cards and sticker price cards directly in Telegram chats. Users can search for gifts/stickers using `@YourBot gift pepe` or `@YourBot sticker azuki`, and the bot returns visual results with images served from a CDN.

---

## What is Telegram Inline Mode?

Telegram Inline Mode allows users to search for content from your bot directly in any chat by typing `@YourBotName <query>`. When a user types this, Telegram sends an inline query to your bot, and your bot responds with a list of results that can include:

- **Photos** (`InlineQueryResultPhoto`) - Direct image results
- **Articles** (`InlineQueryResultArticle`) - Text results with thumbnails
- **Videos, Documents, etc.** - Other media types

The key advantage: Users can share content from your bot without leaving their current chat!

### Example Usage:
```
User types: @GiftsChartBot gift pepe
Bot returns: Photo of Pepe gift card with price
User clicks: Photo is sent to chat
```

---

## System Architecture

```
┌─────────────────┐
│  Telegram User  │
│  Types: @bot    │
│  gift pepe      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Telegram Servers                  │
│  Sends inline_query update         │
└────────┬──────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Telegram Bot (telegram_bot.py)    │
│  - Receives inline_query            │
│  - Searches gift/sticker database    │
│  - Creates InlineQueryResultPhoto   │
│  - Returns CDN URLs                 │
└────────┬──────────────────────────┘
         │
         │ Returns: photo_url=https://cdn.example.com/api/new_gift_cards/Pepe_card.png
         │
         ▼
┌─────────────────────────────────────┐
│  Telegram Servers                  │
│  - Fetches images from CDN URLs     │
│  - Displays thumbnails to user      │
└────────┬──────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  CDN Server (cdn_server.py)         │
│  - Receives HTTP request            │
│  - Serves image file from disk       │
│  - Returns PNG/JPG with headers      │
└─────────────────────────────────────┘
```

---

## How It Works

### Step-by-Step Flow:

1. **User Initiates Search**
   - User types `@GiftsChartBot gift pepe` in any Telegram chat
   - Telegram client sends inline query to Telegram servers

2. **Telegram Sends Update to Bot**
   ```python
   # Telegram sends this update:
   {
     "update_id": 123456,
     "inline_query": {
       "id": "abc123",
       "from": {"id": 12345, "username": "user"},
       "query": "gift pepe",
       "offset": ""
     }
   }
   ```

3. **Bot Processes Query**
   - Bot receives `inline_query` update
   - Searches for matching gifts/stickers
   - Creates result objects with CDN URLs

4. **Bot Returns Results**
   ```python
   # Bot sends back:
   [
     InlineQueryResultPhoto(
       id="unique-id-123",
       photo_url="https://giftschart.01studio.xyz/api/new_gift_cards/Pepe_card.png?t=1234567890",
       thumbnail_url="https://giftschart.01studio.xyz/api/new_gift_cards/Pepe_card.png?t=1234567890",
       title="Pepe",
       description="Gift Price Card",
       caption="💎 Pepe 💎"
     )
   ]
   ```

5. **Telegram Fetches Images**
   - Telegram servers make HTTP GET request to CDN URL
   - CDN server responds with image file
   - Telegram displays thumbnail in inline results

6. **User Selects Result**
   - User clicks on thumbnail
   - Telegram sends the photo to the chat
   - Photo appears in chat with caption

---

## CDN Server Implementation

The CDN server (`cdn_server.py`) is a Flask application that serves static files directly from disk.

### Key Features:

1. **Direct File Serving**
   - Serves images from organized folders
   - Handles nested directory structures
   - Supports multiple file types (PNG, JPG, GIF, WebP)

2. **Proper HTTP Headers**
   ```python
   response.headers['Content-Type'] = 'image/png'
   response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
   response.headers['Content-Disposition'] = 'inline'  # Display in browser, don't download
   ```

3. **URL Structure**
   ```
   https://giftschart.01studio.xyz/api/new_gift_cards/Pepe_card.png
   https://giftschart.01studio.xyz/api/sticker_price_cards/Azuki_Raizan_price_card.png
   https://giftschart.01studio.xyz/api/sticker_collections/azuki/raizan/1_png
   ```

### CDN Server Code:

```python
from flask import Flask, send_from_directory
import os

app = Flask(__name__)
BASE_DIR = "/root/01studio/giftschart"

# Define folders to serve
FOLDERS = {
    "new_gift_cards": "new_gift_cards",
    "sticker_price_cards": "Sticker_Price_Cards",
    "sticker_collections": "sticker_collections",
    "downloaded_images": "downloaded_images"
}

@app.route("/api/<folder_key>/<path:filename>")
def serve_file(folder_key, filename):
    """Serve a specific file from a folder"""
    folder_name = FOLDERS.get(folder_key)
    if not folder_name:
        return {"error": "Invalid folder"}, 404
    
    folder_path = os.path.join(BASE_DIR, folder_name)
    file_path = os.path.join(folder_path, filename)
    
    if not os.path.exists(file_path):
        return {"error": "File not found"}, 404
    
    # Set proper MIME type
    mime_type = 'image/png' if filename.endswith('.png') else 'image/jpeg'
    
    response = send_from_directory(folder_path, filename)
    response.headers['Content-Type'] = mime_type
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Content-Disposition'] = 'inline'
    
    return response
```

---

## Bot Inline Query Handler

The bot's inline query handler (`inline_query` function in `telegram_bot.py`) processes user queries and returns formatted results.

### Key Components:

1. **Query Processing**
   ```python
   async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
       query = update.inline_query.query.lower().strip()
       offset = update.inline_query.offset or "0"
       
       # Handle special queries
       if query == "gift":
           # Show all gifts with pagination
       elif query == "sticker":
           # Show all stickers with pagination
       else:
           # Search for specific gifts/stickers
   ```

2. **CDN URL Generation**
   ```python
   CDN_BASE_URL = "https://giftschart.01studio.xyz/api"
   
   def create_safe_cdn_url(base_path, filename, file_type="general"):
       """Create safe CDN URL with proper encoding"""
       normalized_filename = normalize_cdn_path(filename, file_type)
       encoded_filename = quote(normalized_filename)
       return f"{CDN_BASE_URL}/{base_path}/{encoded_filename}"
   ```

3. **Result Creation**

   **For Gifts (Photo Results):**
   ```python
   results.append(
       InlineQueryResultPhoto(
           id=str(uuid4()),
           photo_url=gift_card_url + f"?t={timestamp}",  # Cache-busting
           thumbnail_url=gift_card_url + f"?t={timestamp}",
           title=gift_name,
           description="Gift Price Card",
           caption=f"💎 {gift_name} 💎",
           parse_mode=ParseMode.HTML
       )
   )
   ```

   **For Stickers (Article Results with Thumbnails):**
   ```python
   results.append(
       InlineQueryResultArticle(
           id=str(uuid4()),
           title=f"{collection} - {sticker}",
           description=f"Sticker from {collection}",
           thumbnail_url=sticker_image_url,  # Actual sticker image
           input_message_content=InputTextMessageContent(
               message_text=f"<a href='{sticker_card_url}'> </a><b>{collection} - {sticker}</b>",
               parse_mode=ParseMode.HTML,
               disable_web_page_preview=False
           )
       )
   )
   ```

4. **Pagination Support**
   ```python
   # Show 50 results per page
   RESULTS_PER_PAGE = 50
   start_idx = page_offset * RESULTS_PER_PAGE
   end_idx = start_idx + RESULTS_PER_PAGE
   
   # Calculate next offset
   next_offset = str(page_offset + 1) if end_idx < total_items else None
   
   await update.inline_query.answer(
       results, 
       cache_time=1, 
       next_offset=next_offset  # Telegram will request more with this offset
   )
   ```

---

## Image Display Flow

### How Photos Appear in Telegram:

1. **InlineQueryResultPhoto**
   - `photo_url`: Full-size image URL (Telegram fetches this)
   - `thumbnail_url`: Thumbnail URL (shown in results list)
   - When user clicks, Telegram sends the photo to chat

2. **InlineQueryResultArticle**
   - `thumbnail_url`: Small preview image
   - `input_message_content`: What gets sent when clicked
   - Uses HTML `<a href='image_url'> </a>` trick to embed image in text message

### The HTML Image Embed Trick:

```python
# This creates a message with an embedded image:
message_text = f"<a href='{sticker_card_url}'> </a><b>{collection} - {sticker}</b>"
```

Telegram interprets `<a href='image_url'> </a>` as an image embed. The empty link tag with a space tells Telegram to fetch and display the image inline.

---

## Code Examples

### Complete Inline Query Handler Example:

```python
from telegram import Update, InlineQueryResultPhoto, InlineQueryResultArticle
from telegram.ext import Application, InlineQueryHandler
from uuid import uuid4
from urllib.parse import quote
import datetime

CDN_BASE_URL = "https://your-cdn-domain.com/api"

async def inline_query(update: Update, context):
    query = update.inline_query.query.lower().strip()
    offset = update.inline_query.offset or "0"
    
    results = []
    
    # Example: Search for gifts
    if query.startswith("gift "):
        gift_name = query[5:].strip()
        
        # Normalize filename
        gift_filename = gift_name.replace(" ", "_") + "_card.png"
        
        # Create CDN URL with cache-busting
        timestamp = int(datetime.datetime.now().timestamp())
        photo_url = f"{CDN_BASE_URL}/new_gift_cards/{quote(gift_filename)}?t={timestamp}"
        
        # Create photo result
        results.append(
            InlineQueryResultPhoto(
                id=str(uuid4()),
                photo_url=photo_url,
                thumbnail_url=photo_url,
                title=gift_name,
                description="Gift Price Card",
                caption=f"💎 {gift_name} 💎"
            )
        )
    
    # Answer the query
    await update.inline_query.answer(results, cache_time=60)

# Register handler
application.add_handler(InlineQueryHandler(inline_query))
```

### CDN Server Example:

```python
from flask import Flask, send_from_directory
import os

app = Flask(__name__)

@app.route("/api/<folder>/<path:filename>")
def serve_file(folder, filename):
    base_dir = "/path/to/your/files"
    folder_path = os.path.join(base_dir, folder)
    file_path = os.path.join(folder_path, filename)
    
    if not os.path.exists(file_path):
        return {"error": "Not found"}, 404
    
    response = send_from_directory(folder_path, filename)
    response.headers['Content-Type'] = 'image/png'
    response.headers['Cache-Control'] = 'no-cache'
    
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
```

---

## Building Your Own System

### Step 1: Set Up CDN Server

1. **Install Flask:**
   ```bash
   pip install flask
   ```

2. **Create CDN Server:**
   - Create `cdn_server.py` (use code example above)
   - Organize your images in folders
   - Configure domain/SSL certificate

3. **Deploy CDN Server:**
   ```bash
   # Using Gunicorn (recommended)
   gunicorn --bind 0.0.0.0:8081 cdn_server:app
   
   # Or using PM2
   pm2 start cdn_server.py --interpreter python3
   ```

4. **Configure Nginx (Optional):**
   ```nginx
   server {
       listen 443 ssl;
       server_name your-cdn-domain.com;
       
       location /api/ {
           proxy_pass http://localhost:8081;
       }
   }
   ```

### Step 2: Set Up Telegram Bot

1. **Create Bot with BotFather:**
   - Message `@BotFather` on Telegram
   - Use `/newbot` command
   - Enable inline mode: `/setinline`

2. **Install python-telegram-bot:**
   ```bash
   pip install python-telegram-bot
   ```

3. **Create Bot Handler:**
   ```python
   from telegram.ext import Application, InlineQueryHandler
   
   async def inline_query(update, context):
       # Your inline query logic here
       pass
   
   application = Application.builder().token("YOUR_BOT_TOKEN").build()
   application.add_handler(InlineQueryHandler(inline_query))
   application.run_polling()
   ```

### Step 3: Organize Your Files

```
project/
├── images/
│   ├── gift_cards/
│   │   ├── Pepe_card.png
│   │   └── Tama_card.png
│   └── stickers/
│       └── Azuki_Raizan_price_card.png
├── cdn_server.py
└── telegram_bot.py
```

### Step 4: Test Your System

1. **Test CDN:**
   ```bash
   curl https://your-cdn-domain.com/api/gift_cards/Pepe_card.png
   # Should return PNG image
   ```

2. **Test Bot:**
   - Start bot: `python telegram_bot.py`
   - In Telegram, type: `@YourBot gift pepe`
   - Should see image thumbnail in results

### Step 5: Optimize Performance

1. **Use Cache-Busting:**
   ```python
   timestamp = int(time.time())
   url = f"{CDN_URL}/image.png?t={timestamp}"
   ```

2. **Implement Pagination:**
   ```python
   # Return 50 results per page
   next_offset = str(page + 1) if has_more else None
   await update.inline_query.answer(results, next_offset=next_offset)
   ```

3. **Optimize Images:**
   - Compress PNG files
   - Use appropriate image sizes
   - Consider WebP format for smaller files

---

## Key Concepts Summary

### 1. **Inline Mode Flow:**
   User Query → Telegram → Bot → CDN URLs → Telegram → CDN → Images → User

### 2. **CDN Requirements:**
   - Must serve images via HTTP/HTTPS
   - Must return proper Content-Type headers
   - Must be publicly accessible
   - Should support cache-busting (query parameters)

### 3. **Result Types:**
   - `InlineQueryResultPhoto`: Direct photo results
   - `InlineQueryResultArticle`: Text with thumbnail (can embed images)

### 4. **Image Embedding Trick:**
   ```html
   <a href='https://cdn.com/image.png'> </a>
   ```
   Empty link tag makes Telegram fetch and display image inline

### 5. **Pagination:**
   - Use `offset` parameter for pagination
   - Return `next_offset` if more results available
   - Telegram automatically requests more when user scrolls

---

## Troubleshooting

### Images Not Showing:

1. **Check CDN URL:**
   ```bash
   curl -I https://your-cdn.com/api/image.png
   # Should return 200 OK with Content-Type: image/png
   ```

2. **Verify Bot Token:**
   - Make sure bot token is correct
   - Check bot has inline mode enabled

3. **Check File Paths:**
   - Ensure files exist on CDN server
   - Verify folder structure matches URLs

4. **Test CDN Directly:**
   - Open CDN URL in browser
   - Should see image, not JSON error

### Common Issues:

- **404 Errors**: File path mismatch
- **CORS Errors**: Add CORS headers to CDN server
- **Slow Loading**: Optimize images, use CDN caching
- **Pagination Not Working**: Check `next_offset` logic

---

## Best Practices

1. **Use HTTPS**: Always use HTTPS for CDN URLs
2. **Normalize Filenames**: Handle special characters properly
3. **Cache-Busting**: Add timestamps to prevent stale images
4. **Error Handling**: Return fallback results if CDN fails
5. **Rate Limiting**: Implement rate limiting for CDN requests
6. **Monitoring**: Log CDN requests for debugging
7. **Optimization**: Compress images, use appropriate sizes

---

## Conclusion

Telegram inline mode with CDN integration provides a powerful way to share visual content directly in chats. The key components are:

- **CDN Server**: Serves images efficiently
- **Bot Handler**: Processes queries and returns CDN URLs
- **Telegram**: Fetches and displays images

By following this guide, you can build your own inline mode system for sharing images, cards, or any visual content through Telegram!

---

*Last Updated: December 2024*
*Based on GiftsChart Bot Implementation*

