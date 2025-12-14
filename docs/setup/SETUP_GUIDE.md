# Quick Setup Guide

## ✅ Configuration Complete

Your `.env` file has been created with your credentials:
- **Bot Token**: Configured
- **Portal API ID**: 22307634
- **Portal API Hash**: Configured
- **Telegram API**: Configured (same as Portal API)

## 🚀 Next Steps

### 1. Install Dependencies
```bash
cd GiftsChart-ALL
pip install -r requirements.txt
```

### 2. Start the Bot
```bash
python telegram_bot.py
```

Or use the startup script:
```bash
python start_bot.py
```

### 3. Docker Deployment (Optional)
```bash
docker-compose up -d
```

This will start 4 services:
- **bot**: Main Telegram bot
- **cdn**: CDN server on port 4000
- **scheduler**: Card pregeneration (every 32 minutes)
- **sticker**: Sticker update scheduler

## 📁 Project Structure

```
GiftsChart-ALL/
├── .env                    # ✅ Your configuration (DO NOT COMMIT)
├── telegram_bot.py         # Main bot entry point
├── core/
│   └── bot_config.py      # Bot configuration loader
├── api/                   # API integrations
├── generators/            # Card generation logic
├── services/              # External services
├── schedulers/            # Background tasks
└── assets/                # Images and templates
```

## 🔑 Key Features

1. **Gift Card Generation**: Type any gift name in chat
2. **Premium System**: `/premium` command for subscriptions
3. **Sticker Collections**: `/sticker` command
4. **Admin Dashboard**: Admin commands for monitoring
5. **Rate Limiting**: 5 requests per minute per user

## 🔒 Security Notes

- ✅ `.env` is in `.gitignore` - safe from commits
- ✅ All credentials are environment-based
- ✅ Rate limiting enabled by default
- ✅ Message ownership tracking for security

## 📚 Documentation

See `README.md` for complete documentation including:
- Architecture overview
- API integrations
- Premium system details
- Admin functions
- Troubleshooting guide

## 🆘 Common Issues

### Bot won't start
```bash
# Check if .env is loaded
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('TELEGRAM_BOT_TOKEN'))"
```

### Portal API issues
- Verify API_ID and API_HASH are correct
- Check `portal_auth_token.txt` is generated
- Review logs in `gift_api_results.log`

### Database errors
```bash
# Recreate databases if corrupted
rm sqlite_data/*.db
# Restart bot to recreate
```

## 📞 Support

- Telegram: @GiftsChart_Support
- GitHub Issues: [Repository Issues]
- Documentation: See README.md

---

**Status**: ✅ Ready to start!
**Last Updated**: February 3, 2026
