# GiftsChart Bot - ULTRA DEEP TECHNICAL ANALYSIS

## 🔬 EXECUTIVE TECHNICAL SUMMARY

**Project**: Telegram Gift & Sticker Price Tracking Bot  
**Codebase Size**: ~15,000+ lines of Python  
**Architecture**: Microservices with Docker Compose  
**Primary Language**: Python 3.8+  
**Framework**: python-telegram-bot 22.1  
**Database**: SQLite (3 separate databases)  
**APIs**: Portal API (primary), Legacy API (fallback), Telegram Bot API  
**Deployment**: Docker Compose (4 services) or standalone Python  

---

## 📁 COMPLETE FILE STRUCTURE ANALYSIS

### Core Bot Files (core/)
```
core/
├── telegram_bot.py          # 3,616 lines - Main bot logic
├── bot_config.py            # 65 lines - Configuration loader
├── premium_system.py        # 1,613 lines - Payment & subscriptions
├── rate_limiter.py          # ~300 lines - Rate limiting system
├── callback_handler.py      # ~500 lines - Button callback handling
└── start_bot.py             # 240 lines - Startup orchestration
```

### Services (services/)
```
services/
├── portal_api.py            # ~600 lines - Portal API integration
├── tonnel_api.py            # ~460 lines - Tonnel marketplace
├── mrkt_api.py              # ~765 lines - MRKT marketplace
├── mrkt_quant_api.py        # ~200 lines - Quant marketplace
├── sticker_integration.py   # 1,167 lines - Sticker management
├── cdn_server.py            # ~385 lines - Flask CDN server
├── plus_premarket_gifts.py  # ~150 lines - Premarket gifts
└── premarket_gifts.py       # ~100 lines - Premarket tracking
```

### Generators (generators/)
```
generators/
├── gift_card_generator.py              # 1,946 lines - Main card generator
├── pregenerate_gift_cards.py           # ~305 lines - Scheduled generation
├── sticker_price_card_generator.py     # ~770 lines - Sticker cards
├── goodies_price_card_generator.py     # ~837 lines - Goodies cards
├── live_price_card.py                  # ~160 lines - Live price cards
├── plus_premarket_card_generator.py    # ~200 lines - Premarket cards
└── generate_sticker_price_card.py      # ~350 lines - Sticker generation
```

### Schedulers (schedulers/)
```
schedulers/
├── scheduled_sticker_update.py    # ~316 lines - Sticker price updates
├── premarket_price_scheduler.py   # ~260 lines - Premarket scheduling
├── backup_scheduler.py            # ~191 lines - Database backups
├── sticker_updater.py             # ~132 lines - Sticker updater
└── update_sticker_prices.py       # ~105 lines - Price updates
```

### Utilities (utils/)
```
utils/
├── advanced_analytics.py      # ~430 lines - Analytics dashboard
├── visual_analytics.py        # ~361 lines - Visual reports
├── ton_price_utils.py         # ~100 lines - TON price conversion
├── refresh_auth.py            # ~87 lines - Auth token refresh
├── generate_session_string.py # ~52 lines - Session generation
├── setup_telegram_session.py  # ~50 lines - Session setup
└── image_uploader.py          # ~121 lines - Image upload utility
```

---

## 🏗️ ARCHITECTURE DEEP DIVE

### 1. Main Bot Architecture (telegram_bot.py)

#### Core Components:
