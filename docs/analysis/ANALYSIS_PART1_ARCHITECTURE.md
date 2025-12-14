# Part 1: Architecture & Core Systems

## 🏗️ SYSTEM ARCHITECTURE

### Docker Compose Stack
```yaml
services:
  bot:          # Main Telegram bot (telegram_bot.py)
  cdn:          # Flask CDN server (port 4000)
  scheduler:    # Card pregeneration (every 32 min)
  sticker:      # Sticker price updates
```

### Process Flow
```
User Message → Bot Handler → Rate Limiter → Gift Matcher
    ↓
Check Cache → Portal API → Card Generator → Send Response
    ↓
Register Message Owner → Track for Deletion
```

## 🔑 CORE BOT LOGIC (telegram_bot.py - 3,616 lines)

### Key Functions:

1. **is_message_too_old()**
   - Filters messages older than 5 minutes (300 seconds)
   - Prevents backlog processing on bot restart
   - Critical for avoiding spam

2. **find_matching_gifts()**
   - Smart fuzzy matching with 75% threshold
   - Handles special cases (Jack-in-the-Box, Durov's Cap)
   - Returns max 5 matches to avoid overwhelming users
   - Gift groups for disambiguation (ring, hat, heart, etc.)

3. **send_gift_card()**
   - Checks premium status
   - Generates custom buttons based on group
   - Registers message ownership
   - Different captions for premium vs non-premium

4. **handle_message()**
   - Main message processor
   - Rate limiting check (5 req/min)
   - Gift name matching
   - Sticker detection
   - Command routing

### Admin System:
```python
ADMIN_USER_IDS = [800092886, 6529233780]
```

### Special Groups Configuration:
```python
SPECIAL_GROUPS = {
    -1002155968676: {
        "buy_sell_link": "...",
        "portal_link": "..."
    }
}
```
