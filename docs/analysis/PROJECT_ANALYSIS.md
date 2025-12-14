# GiftsChart Bot - Complete Project Analysis

## 📋 Executive Summary

**Project Type**: Telegram Bot for Gift Card & Sticker Price Tracking  
**Language**: Python 3.8+  
**Architecture**: Microservices (Bot + CDN + Schedulers)  
**Deployment**: Docker Compose (4 services)  
**Database**: SQLite (3 databases)  
**APIs**: Portal API (primary), Legacy API (fallback), Telegram Bot API

---

## 🏗️ Architecture Overview

### Service Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                      │
├─────────────────────────────────────────────────────────────┤
│  1. bot          → Main Telegram Bot (telegram_bot.py)      │
│  2. cdn          → Flask CDN Server (port 4000)              │
│  3. scheduler    → Card Pregeneration (every 32 min)         │
│  4. sticker      → Sticker Price Updates                     │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure
```
GiftsChart-ALL/
├── core/                    # Core bot logic
│   ├── telegram_bot.py      # Main bot (3,615 lines)
│   ├── bot_config.py        # Configuration loader
│   ├── premium_system.py    # Payment & subscriptions (1,613 lines)
│   ├── rate_limiter.py      # Rate limiting system
│   └── start_bot.py         # Startup script
│
├── services/                # External API integrations
│   ├── portal_api.py        # Portal API (primary data source)
│   ├── tonnel_api.py        # Tonnel marketplace API
│   ├── mrkt_api.py          # MRKT marketplace API
│   ├── sticker_integration.py # Sticker management (1,167 lines)
│   └── cdn_server.py        # Flask CDN server
│
├── generators/              # Card generation logic
│   ├── gift_card_generator.py      # Main card generator (1,946 lines)
│   ├── pregenerate_gift_cards.py   # Scheduled pregeneration
│   └── sticker_price_card_generator.py
│
├── schedulers/              # Background tasks
│   ├── scheduled_sticker_update.py
│   ├── backup_scheduler.py
│   └── premarket_price_scheduler.py
│
├── config/                  # Configuration
│   └── paths.py            # Centralized path management
│
├── utils/                   # Utilities
│   ├── ton_price_utils.py
│   ├── advanced_analytics.py
│   └── refresh_auth.py
│
├── assets/                  # Images, fonts, templates
├── card_templates/          # 77+ gift card templates
├── card_metadata/           # Gift metadata JSON files
├── sticker_collections/     # 40+ sticker collections
├── sticker_metadata/        # Sticker metadata
├── downloaded_images/       # Gift images (webp)
├── sqlite_data/            # SQLite databases
│
├── .env                    # ✅ Environment configuration
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker orchestration
└── Dockerfile             # Container definition
```

---

## 🔑 Key Components

### 1. Main Bot (`core/telegram_bot.py`)
**Lines**: 3,615  
**Purpose**: Central bot logic and command handling

**Key Features**:
- Message timestamp filtering (prevents old message processing)
- Multi-admin support (2 admin IDs)
- Rate limiting integration (5 requests/min)
- Gift card generation on text input
- Premium subscription management
- Inline mode support
- Callback query handling

**Admin IDs**: 800092886, 6529233780

**Commands**:
- `/start` - Welcome message
- `/help` - Help information
- `/premium` - Premium subscription
- `/sticker` - Sticker collections
- `/terms` - Terms of service
- `/refund` - Refund management

### 2. Premium System (`core/premium_system.py`)
**Lines**: 1,613  
**Purpose**: Telegram Stars payment processing

**Features**:
- Telegram Stars integration (XTR currency)
- 30-day subscriptions
- Custom referral links (MRKT, Palace, Tonnel, Portal)
- 3-day refund window
- One-time refund per group
- Payment history tracking

**Database Tables**:
- `premium_subscriptions` - Active subscriptions
- `payment_history` - All payments
- `pending_payments` - Awaiting confirmation
- `refunds` - Refund requests
- `refunded_groups` - One-time refund tracking

### 3. Portal API Integration (`services/portal_api.py`)
**Purpose**: Primary data source for gift prices

**Features**:
- Automatic token refresh (every 32 minutes)
- Rate limiting (500ms between requests)
- Session string authentication
- Fallback to legacy API
- Supply data caching (10 minutes)

**Environment Variables Required**:
```bash
PORTAL_API_ID=22307634
PORTAL_API_HASH=7ab906fc6d065a2047a84411c1697593
```

**Authentication Flow**:
1. Load session string from file
2. Call `update_auth()` from aportalsmp
3. Save token to `portal_auth_token.txt`
4. Refresh every 32 minutes

### 4. Gift Card Generator (`generators/gift_card_generator.py`)
**Lines**: 1,946  
**Purpose**: Dynamic gift card creation

**Process**:
1. Fetch gift data from Portal API
2. Load template from `card_templates/`
3. Load metadata from `card_metadata/`
4. Overlay price, supply, TON conversion
5. Save to `new_gift_cards/`

**77+ Gift Cards Available**:
- Tama Gadget, Plush Pepe, Diamond Ring
- Eternal Rose, Swiss Watch, Delicious Cake
- And 70+ more...

### 5. Rate Limiter (`core/rate_limiter.py`)
**Purpose**: Prevent abuse and ensure fair usage

**Limits**:
- 5 requests per minute per user
- 1 gift request per minute per gift
- Message ownership tracking for secure deletion

**Database**: `user_requests.db`
- `user_requests` - Gift request tracking
- `command_requests` - Command usage tracking
- `message_owners` - Message ownership for deletion

### 6. CDN Server (`services/cdn_server.py`)
**Purpose**: Serve generated cards via HTTP

**Port**: 4000  
**Base URL**: `https://giftschart.the01studio.xyz/api`

**Endpoints**:
- `/api/cards/<gift_name>` - Gift cards
- `/api/stickers/<collection>/<sticker>` - Sticker cards
- `/api/health` - Health check

---

## 🔌 API Integrations

### Portal API (Primary)
**Library**: `aportalsmp==1.2`  
**Status**: ✅ Fully Integrated

**Functions**:
- `portal_search()` - Search gifts by name
- `update_auth()` - Refresh authentication token

**Rate Limits**:
- 500ms between requests
- Automatic retry on 429 errors

### Legacy API (Fallback)
**Endpoints**:
- `https://giftcharts-api.onrender.com/gifts`
- `https://giftcharts-api.onrender.com/weekChart?name=`

**Used For**:
- Supply data when Portal API fails
- Chart data generation
- Backup pricing data

### Telegram Bot API
**Library**: `python-telegram-bot==22.1`

**Features Used**:
- Bot commands
- Inline keyboards
- Callback queries
- Inline mode
- Payment processing (Telegram Stars)
- Media sending

---

## 💾 Database Schema

### 1. Premium System (`premium_system.db`)

```sql
-- Premium subscriptions
CREATE TABLE premium_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    payment_id TEXT NOT NULL,
    telegram_payment_charge_id TEXT,
    stars_amount INTEGER NOT NULL,
    mrkt_link TEXT,
    palace_link TEXT,
    tonnel_link TEXT,
    portal_link TEXT,
    created_at INTEGER NOT NULL,
    expires_at INTEGER,
    is_active BOOLEAN DEFAULT 1,
    UNIQUE(owner_id, group_id)
);

-- Payment history
CREATE TABLE payment_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    payment_id TEXT NOT NULL,
    stars_amount INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

-- Refunds
CREATE TABLE refunds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    payment_id TEXT NOT NULL,
    reason TEXT,
    status TEXT DEFAULT 'pending',
    created_at INTEGER NOT NULL,
    processed_at INTEGER,
    processed_by TEXT
);
```

### 2. Rate Limiter (`user_requests.db`)

```sql
-- User gift requests
CREATE TABLE user_requests (
    user_id INTEGER,
    chat_id INTEGER,
    gift_name TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, chat_id, gift_name)
);

-- Command requests
CREATE TABLE command_requests (
    user_id INTEGER,
    chat_id INTEGER,
    command_name TEXT,
    minute INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, chat_id, command_name)
);

-- Message ownership
CREATE TABLE message_owners (
    user_id INTEGER,
    chat_id INTEGER,
    message_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, chat_id, message_id)
);
```

---

## 🚀 Deployment

### Environment Variables (.env)
```bash
# Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_USERNAME=@giftsChartBot

# Portal API (Primary Data Source)
PORTAL_API_ID=22307634
PORTAL_API_HASH=7ab906fc6d065a2047a84411c1697593

# Telethon API (Same as Portal)
TELEGRAM_API_ID=22307634
TELEGRAM_API_HASH=7ab906fc6d065a2047a84411c1697593

# Session Configuration
TELEGRAM_SESSION_NAME=gifts_session
```

### Docker Deployment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down
```

### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Start bot
python core/telegram_bot.py

# Or use startup script
python core/start_bot.py
```

---

## 📊 Data Flow

### Gift Card Request Flow
```
User types "tama" in chat
    ↓
telegram_bot.py receives message
    ↓
Check rate limit (rate_limiter.py)
    ↓
Check if card exists in new_gift_cards/
    ↓
If not exists:
    ↓
    Fetch data from Portal API (portal_api.py)
    ↓
    Generate card (gift_card_generator.py)
    ↓
    Save to new_gift_cards/
    ↓
Send card to user with buttons
    ↓
Track message ownership (rate_limiter.py)
```

### Premium Subscription Flow
```
User clicks "💫 Get Premium"
    ↓
Bot sends Telegram Stars invoice
    ↓
User completes payment
    ↓
Bot receives successful_payment update
    ↓
premium_system.py processes payment
    ↓
Save to premium_subscriptions table
    ↓
Start group setup flow
    ↓
Collect custom referral links
    ↓
Activate premium features
```

### Card Pregeneration Flow (Scheduler)
```
Every 32 minutes:
    ↓
pregenerate_gift_cards.py runs
    ↓
Read all_gift_names.txt (77+ gifts)
    ↓
For each gift:
    ↓
    Fetch latest data from Portal API
    ↓
    Generate card with current prices
    ↓
    Save to new_gift_cards/
    ↓
Log results to pregenerate_cards.log
```

---

## 🔒 Security Features

### 1. Rate Limiting
- Per-user request tracking
- 5 requests per minute limit
- Command-specific limits
- Database persistence

### 2. Message Ownership
- Track who requested each message
- Only requester can delete
- Prevents unauthorized deletions

### 3. Timestamp Filtering
- Ignore messages older than 5 minutes
- Prevents backlog processing on restart
- Reduces spam processing

### 4. Payment Security
- Telegram Stars integration
- Secure payment verification
- Refund protection (3-day window)
- One-time refund per group

### 5. Admin Access Control
- Multi-admin support
- Admin-only commands
- Audit logging

---

## 📈 Performance Metrics

### Response Times
- Gift card generation: < 2 seconds
- API calls: < 1 second
- Card pregeneration: ~30 seconds for all 77 cards

### Resource Usage
- Memory: ~200MB base
- CPU: < 10% average
- Storage: ~500MB (templates + generated cards)
- Network: ~1GB/month

### Scalability
- Concurrent users: 100+
- Requests per minute: 500+
- Database size: < 50MB
- Card cache: 77 cards pregenerated

---

## 🛠️ Maintenance

### Regular Tasks
1. **Token Refresh**: Automatic every 32 minutes
2. **Card Pregeneration**: Every 32 minutes
3. **Database Backup**: Hourly (backup_scheduler.py)
4. **Sticker Updates**: Scheduled (scheduled_sticker_update.py)

### Log Files
- `gift_api_results.log` - Portal API calls
- `pregenerate_cards.log` - Card generation
- `premium_system.log` - Payment processing
- `telegram_bot.log` - Bot operations

### Monitoring
- System health checks
- API status monitoring
- Database integrity checks
- Error rate tracking

---

## 🐛 Common Issues & Solutions

### Issue 1: Portal API Connection Failed
**Cause**: Invalid API credentials or expired token  
**Solution**: 
```bash
# Verify credentials in .env
echo $PORTAL_API_ID
echo $PORTAL_API_HASH

# Regenerate token
python utils/refresh_auth.py
```

### Issue 2: Bot Not Responding
**Cause**: Rate limiting or old messages  
**Solution**: 
- Check rate limiter database
- Verify timestamp filtering is working
- Clear old messages from queue

### Issue 3: Card Generation Failed
**Cause**: Missing template or metadata  
**Solution**:
```bash
# Check template exists
ls card_templates/Tama_Gadget_template.png

# Check metadata exists
ls card_metadata/Tama_Gadget_metadata.json
```

### Issue 4: Database Locked
**Cause**: Multiple processes accessing SQLite  
**Solution**:
```bash
# Stop all services
docker-compose down

# Remove lock files
rm sqlite_data/*.db-journal

# Restart
docker-compose up -d
```

---

## 📝 Development Notes

### Adding New Gift Cards
1. Create template: `card_templates/{Gift_Name}_template.png`
2. Create metadata: `card_metadata/{Gift_Name}_metadata.json`
3. Add to `data/all_gift_names.txt`
4. Run pregeneration: `python generators/pregenerate_gift_cards.py`

### Adding New Commands
1. Add handler in `telegram_bot.py`
2. Add to help text
3. Test with rate limiting
4. Update documentation

### Modifying Premium Features
1. Edit `core/premium_system.py`
2. Update database schema if needed
3. Test payment flow
4. Update refund logic if applicable

---

## 🎯 Future Enhancements

### Planned Features
- Web dashboard for analytics
- Multi-language support
- Advanced caching (Redis)
- Webhook integration
- Mobile app
- API webhooks for real-time updates

### Performance Improvements
- CDN integration for faster delivery
- Database optimization (indexes)
- Async processing for all operations
- Load balancing for multiple instances

---

## 📞 Support & Resources

### Documentation
- Main README: `README.md`
- Setup Guide: `SETUP_GUIDE.md`
- This Analysis: `PROJECT_ANALYSIS.md`

### Key Files to Understand
1. `core/telegram_bot.py` - Main bot logic
2. `core/premium_system.py` - Payment system
3. `services/portal_api.py` - API integration
4. `generators/gift_card_generator.py` - Card generation
5. `config/paths.py` - Path management

### External Resources
- Portal API: https://github.com/aportalsmp
- Telegram Bot API: https://core.telegram.org/bots/api
- python-telegram-bot: https://python-telegram-bot.org/

---

**Last Updated**: February 3, 2026  
**Version**: 3.4  
**Analysis Version**: 1.0
