<p align="center">
  <img src="assets/giftschartbanner.jpg" alt="GiftsChart Banner" width="100%">
</p>

<div align="center">

# GiftsChart Bot

### Every NFT Has a Price. Know It Live.

<br/>

[![Telegram Bot](https://img.shields.io/badge/Telegram-@GiftsChartBot-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/GiftsChartBot)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production-success?style=for-the-badge)](https://t.me/GiftsChartBot)
[![Community](https://img.shields.io/badge/Community-@The01Studio-blueviolet?style=for-the-badge&logo=telegram)](https://t.me/The01Studio)

</div>

<br/>

<div align="center">
  <a href="https://youtube.com/shorts/VdemjP__Um4?feature=share">
    <img src="https://img.youtube.com/vi/VdemjP__Um4/maxresdefault.jpg" alt="Watch GiftsChart Demo" width="800" style="border-radius: 8px;">
  </a>
  <br>
  <p><i>Click to watch GiftsChart in action</i></p>
</div>

<br/>

> [!TIP]
> **New!** Premium features now include custom referral links, branded price cards, and priority support. Get started with just 99 Stars for 30 days!

---

## Overview

GiftsChart is a powerful Telegram bot that brings **live gift price tracking** to your fingertips. Every Telegram gift and sticker has a price—now you can know it instantly, right in Telegram.

**Every NFT Has a Price. Know It Live.**

Get instant price cards with real-time market data, supply information, and direct marketplace links—all without leaving Telegram.

**Key Capabilities:**
- **Gift Price Cards**: Track 93+ Telegram gifts with live prices from Portal API
- **Sticker Price Cards**: Monitor 218+ sticker collections from Stickers.tools
- **Premium Features**: Custom referral links and branded cards for groups
- **Lightning Fast**: Cached responses with 30-minute refresh cycles
- **Spam Protection**: Built-in rate limiting and ownership verification
- **Live Data**: Real-time prices from Portal, MRKT, and Stickers.tools APIs

---

## Features

### Gift Tracking
Track any Telegram gift instantly. Just type the gift name in any chat:

- **Live Prices**: Real-time prices in Stars and USD
- **Supply Data**: Current and initial supply information
- **Market Links**: Direct links to Portal, MRKT, Tonnel, and Palace
- **Beautiful Cards**: Auto-generated cards with gift images and gradients
- **Smart Matching**: Fuzzy search finds gifts even with typos

### Sticker Collections
Browse and track 218+ sticker collections:

- **Collection Browser**: Organized by collection with pagination
- **Price Tracking**: Floor prices in Stars and USD
- **Supply Info**: Track availability and rarity
- **Marketplace Links**: Quick access to MRKT and Palace
- **Preview Images**: High-quality sticker previews

### Premium System
Unlock advanced features for your group:

- **Custom Referral Links**: Add your own MRKT, Palace, Tonnel, and Portal links
- **Branded Cards**: Your links appear on all price cards in your group
- **Priority Support**: Get help faster
- **No Ads**: Clean, distraction-free experience
- **30-Day Access**: Just 99 Stars (Telegram Stars)
- **3-Day Refund**: Full refund within 3 days if not satisfied

### Security & Performance
- **Rate Limiting**: Prevents spam and abuse
- **Message Ownership**: Only requesters can use buttons
- **Cached Data**: Fast responses with smart cache invalidation
- **Error Handling**: Graceful degradation when APIs are down
- **Database Backup**: Automatic Supabase backups every 6 hours

---

## System Architecture

```mermaid
graph TB
    subgraph "User Interface"
        A[Telegram Users] --> B[Main Bot Interface]
        B --> C[Gift Card Requests]
        B --> D[Sticker Requests]
        B --> E[Premium Commands]
    end
    
    subgraph "Core Bot System"
        B --> G[telegram_bot.py<br/>Main Bot Logic<br/>3620 lines]
        G --> H[callback_handler.py<br/>Button Interactions]
        G --> I[bot_config.py<br/>Configuration]
        G --> J[rate_limiter.py<br/>Request Tracking]
    end
    
    subgraph "Premium System"
        E --> K[premium_system.py<br/>Payment Processing<br/>1759 lines]
        K --> L[Telegram Stars API]
        K --> M[SQLite Premium DB]
        K --> N[Refund System]
    end
    
    subgraph "Gift Card System"
        C --> O[Gift Card Generation]
        O --> P[gift_card_generator.py<br/>Card Creation<br/>Dynamic Pricing]
        O --> Q[Card Templates<br/>93+ Designs]
        O --> R[Real-time Pricing<br/>Portal API]
        P --> S[Generated Cards<br/>WebP Files]
    end
    
    subgraph "Sticker System"
        D --> T[sticker_integration.py<br/>Sticker Management<br/>1368 lines]
        T --> U[Sticker Collections<br/>218+ Packs]
        T --> V[Price Cards Generation]
        T --> W[Metadata Management]
    end
    
    subgraph "Rate Limiting & Security"
        J --> X[User Request DB<br/>Per-minute Limits]
        J --> Y[Message Ownership<br/>Secure Deletion]
    end
    
    subgraph "APIs & External Services"
        R --> Z[Portal API<br/>Gift Prices]
        P --> AA[MRKT API<br/>Market Data]
        K --> AB[Telegram Payment API<br/>Stars Processing]
        T --> AC[Stickers.tools API<br/>Sticker Data]
    end
    
    subgraph "Data Storage"
        M --> AD[(premium_subscriptions.db<br/>SQLite)]
        X --> AE[(user_requests.db<br/>Rate Limiting)]
        W --> AF[JSON Metadata<br/>Card & Sticker Info]
    end
```

---

## Usage

### Basic Commands

- `/start` - Welcome message and bot introduction
- `/gift <name>` - Get price card for a specific gift
- `/sticker` - Browse sticker collections
- `/premium` - Upgrade to premium features
- `/help` - Show help and available commands

### Inline Mode

Type `@GiftsChartBot <gift name>` in any chat to search and share gift cards instantly.

### Natural Language

Just type a gift name in any chat where the bot is present:
```
Plush Pepe
Diamond Ring
Astral Shard
```

The bot will automatically detect and respond with a price card!

---

## Premium Features

### How to Get Premium

1. Start a private chat with [@GiftsChartBot](https://t.me/GiftsChartBot)
2. Send `/premium` command
3. Pay 99 Stars (Telegram Stars)
4. Share your group with the bot
5. Add your custom referral links
6. Enjoy premium features for 30 days!

### What's Included

- **Custom Referral Links** - Add your MRKT, Palace, Tonnel, and Portal links
- **Branded Price Cards** - Your links appear on all cards in your group
- **Priority Support** - Get help faster from our team
- **No Ads** - Clean, distraction-free experience
- **30-Day Access** - Full month of premium features
- **3-Day Refund** - Not satisfied? Get a full refund within 3 days

---

## Project Structure

```
GiftsChart-ALL/
├── core/                    # Core bot functionality
│   ├── telegram_bot.py      # Main bot logic (3620 lines)
│   ├── callback_handler.py  # Button callbacks
│   ├── premium_system.py    # Premium features (1759 lines)
│   ├── rate_limiter.py      # Spam protection
│   └── bot_config.py        # Configuration
├── services/                # External API integrations
│   ├── portal_api.py        # Portal API client
│   ├── mrkt_api.py          # MRKT API client
│   ├── sticker_integration.py # Sticker functionality (1368 lines)
│   └── stickers_tools_api.py  # Stickers.tools API
├── generators/              # Card generation
│   ├── gift_card_generator.py
│   └── sticker_price_card_generator.py
├── schedulers/              # Background tasks
│   └── supabase_backup_sync.py
├── docs/                    # Documentation
│   ├── setup/               # Setup guides
│   ├── analysis/            # Technical docs
│   └── status/              # Status reports
└── assets/                  # Static assets
```

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for detailed structure.

---

<div align="center">

### Built with love for the Telegram Community

*GiftsChart is currently in Production. We appreciate your feedback!*

<sub>Made by [@The01Studio](https://t.me/The01Studio)</sub>

</div>
