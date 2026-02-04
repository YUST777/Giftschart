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
  <video src="assets/giftschart.mp4" width="800" controls>
    Your browser does not support the video tag.
  </video>
  <br>
  <p><i>👆 See GiftsChart in action</i></p>
</div>

<br/>

> [!TIP]
> **New!** Premium features now include custom referral links, branded price cards, and priority support. Get started with just 99★ for 30 days!

---

## 🎯 Overview

GiftsChart is a powerful Telegram bot that brings **live NFT price tracking** to your fingertips. Every TON gift and sticker has a price—now you can know it instantly, right in Telegram.

**Every NFT Has a Price. Know It Live.**

Get instant price cards with real-time market data, supply information, and direct marketplace links—all without leaving Telegram.

**Key Capabilities:**
- 🎁 **Gift Price Cards**: Track 93+ TON gifts with live prices from Portal API
- 🎭 **Sticker Price Cards**: Monitor 218+ sticker collections from Stickers.tools
- 💎 **Premium Features**: Custom referral links and branded cards for groups
- ⚡ **Lightning Fast**: Cached responses with 30-minute refresh cycles
- 🔒 **Spam Protection**: Built-in rate limiting and ownership verification
- 📊 **Live Data**: Real-time prices from Portal, MRKT, and Stickers.tools APIs

---

## ✨ Features

### 🎁 Gift Tracking
Track any TON gift instantly. Just type the gift name in any chat:

- **Live Prices**: Real-time TON and USD prices
- **Supply Data**: Current and initial supply information
- **Market Links**: Direct links to Portal, MRKT, Tonnel, and Palace
- **Beautiful Cards**: Auto-generated cards with gift images and gradients
- **Smart Matching**: Fuzzy search finds gifts even with typos

### 🎭 Sticker Collections
Browse and track 218+ sticker collections:

- **Collection Browser**: Organized by collection with pagination
- **Price Tracking**: Floor prices in TON and USD
- **Supply Info**: Track availability and rarity
- **Marketplace Links**: Quick access to MRKT and Palace
- **Preview Images**: High-quality sticker previews

### 💎 Premium System
Unlock advanced features for your group:

- **Custom Referral Links**: Add your own MRKT, Palace, Tonnel, and Portal links
- **Branded Cards**: Your links appear on all price cards in your group
- **Priority Support**: Get help faster
- **No Ads**: Clean, distraction-free experience
- **30-Day Access**: Just 99★ (Telegram Stars)
- **3-Day Refund**: Full refund within 3 days if not satisfied

### 🛡️ Security & Performance
- **Rate Limiting**: Prevents spam and abuse
- **Message Ownership**: Only requesters can use buttons
- **Cached Data**: Fast responses with smart cache invalidation
- **Error Handling**: Graceful degradation when APIs are down
- **Database Backup**: Automatic Supabase backups every 6 hours

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     TELEGRAM PLATFORM                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    Users     │  │    Groups    │  │   Channels   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Telegram Bot   │
                    │      API        │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
    │    Bot    │     │    CDN    │     │ Scheduler │
    │  Service  │     │  Service  │     │  Service  │
    │ (Main)    │     │ (Flask)   │     │  (Cron)   │
    └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
          │                 │                  │
          └─────────────────┼──────────────────┘
                            │
                   ┌────────▼────────┐
                   │   SQLite DBs    │
                   │  - Premium      │
                   │  - Rate Limit   │
                   │  - Analytics    │
                   └────────┬────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
    │  Portal   │    │   MRKT    │    │  Stickers │
    │    API    │    │    API    │    │    API    │
    └───────────┘    └───────────┘    └───────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Telegram Bot Token
- Portal API credentials
- 2GB RAM minimum
- Linux/macOS (Windows with WSL)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/GiftsChart-ALL.git
cd GiftsChart-ALL
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Run the bot**:
```bash
./quick_start.sh
```

Or use PM2 for production:
```bash
pm2 start ecosystem.config.js
```

### Docker Deployment

```bash
docker-compose up -d --build
```

---

## 📖 Usage

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
Deluxe
Diamond Ring
Astral Shard
```

The bot will automatically detect and respond with a price card!

---

## 💎 Premium Features

### How to Get Premium

1. Start a private chat with [@GiftsChartBot](https://t.me/GiftsChartBot)
2. Send `/premium` command
3. Pay 99★ (Telegram Stars)
4. Share your group with the bot
5. Add your custom referral links
6. Enjoy premium features for 30 days!

### What's Included

✅ **Custom Referral Links** - Add your MRKT, Palace, Tonnel, and Portal links  
✅ **Branded Price Cards** - Your links appear on all cards in your group  
✅ **Priority Support** - Get help faster from our team  
✅ **No Ads** - Clean, distraction-free experience  
✅ **30-Day Access** - Full month of premium features  
✅ **3-Day Refund** - Not satisfied? Get a full refund within 3 days  

---

## 🗂️ Project Structure

```
GiftsChart-ALL/
├── core/                    # Core bot functionality
│   ├── telegram_bot.py      # Main bot logic
│   ├── callback_handler.py  # Button callbacks
│   ├── premium_system.py    # Premium features
│   └── rate_limiter.py      # Spam protection
├── services/                # External API integrations
│   ├── portal_api.py        # Portal API client
│   ├── mrkt_api.py          # MRKT API client
│   └── sticker_integration.py # Sticker functionality
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

## 📊 Statistics

- **93 Gift Templates** - All major TON gifts supported
- **218 Sticker Collections** - Comprehensive sticker tracking
- **320+ Generated Cards** - Pre-generated for instant responses
- **30-Minute Cache** - Fresh data without API spam
- **6-Hour Backups** - Automatic database backups to Supabase
- **15,000+ Lines of Code** - Production-ready, well-tested

---

## 🛠️ Development

### Running Tests

```bash
# Test Portal API
python test_portal_live.py

# Check system status
python check_system.py

# Generate all cards
python generators/pregenerate_gift_cards.py
python generators/generate_all_stickers.py
```

### Code Quality

We maintain high code quality standards:
- ✅ No bare `except:` clauses
- ✅ Specific exception handling
- ✅ Comprehensive logging
- ✅ Type hints (in progress)
- ✅ Clean code structure

See [docs/code_quality/](docs/code_quality/) for details.

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guide
- Add docstrings to all functions
- Write tests for new features
- Update documentation
- Use meaningful commit messages

---

## 📚 Documentation

- **Getting Started**: [docs/setup/START_HERE.md](docs/setup/START_HERE.md)
- **Production Setup**: [docs/setup/PRODUCTION_SETUP.md](docs/setup/PRODUCTION_SETUP.md)
- **System Architecture**: [docs/analysis/SYSTEM_DIAGRAMS.md](docs/analysis/SYSTEM_DIAGRAMS.md)
- **API Documentation**: [docs/analysis/ANALYSIS_PART3_API.md](docs/analysis/ANALYSIS_PART3_API.md)
- **Premium System**: [docs/analysis/ANALYSIS_PART2_PREMIUM.md](docs/analysis/ANALYSIS_PART2_PREMIUM.md)

---

## 🔒 Security & Privacy

GiftsChart is committed to user privacy and security:

- **No Data Collection**: We don't store personal messages
- **Secure Storage**: All sensitive data encrypted
- **Rate Limiting**: Protection against abuse
- **Open Source**: Transparent and auditable code
- **Regular Updates**: Security patches applied promptly

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 Support the Project

**Love GiftsChart?** Here's how you can help:

- ⭐ **Star this repository** on GitHub
- 📢 **Share** with your friends and communities
- 💬 **Join** our community at [@The01Studio](https://t.me/The01Studio)
- 🐛 **Report bugs** via [GitHub Issues](https://github.com/yourusername/GiftsChart-ALL/issues)
- 💡 **Suggest features** in [Discussions](https://github.com/yourusername/GiftsChart-ALL/discussions)

---

## 📞 Contact & Community

- **Telegram Bot**: [@GiftsChartBot](https://t.me/GiftsChartBot)
- **Community**: [@The01Studio](https://t.me/The01Studio)
- **Issues**: [GitHub Issues](https://github.com/yourusername/GiftsChart-ALL/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/GiftsChart-ALL/discussions)

---

## 🗺️ Roadmap

### ✅ Completed (February 2026)
- Core gift tracking functionality
- Sticker collection support
- Premium system with custom links
- Rate limiting and spam protection
- Automatic database backups
- CDN server for image hosting

### 🚧 In Progress
- AI-powered gift recommendations
- Price alerts and notifications
- Historical price charts
- Multi-language support

### 🔮 Future Plans
- Mobile app companion
- Web dashboard for analytics
- API for third-party integrations
- Advanced analytics and insights
- Community marketplace features

---

<div align="center">

### Built with ❤️ for the TON Community

*GiftsChart is currently in Production. We appreciate your feedback!*

<sub>Made by [@The01Studio](https://t.me/The01Studio) • Powered by TON Blockchain</sub>

</div>
