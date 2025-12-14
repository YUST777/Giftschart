# 🚀 PRODUCTION SETUP GUIDE

## ⚠️ CRITICAL: Portal API Authentication Required

The bot **CANNOT** fetch gift prices without Portal API authentication.

### Step 1: Install Dependencies
```bash
cd GiftsChart-ALL
pip install -r requirements.txt
```

### Step 2: Setup Portal Authentication (REQUIRED)
```bash
python3 setup_portal_auth.py
```

**What this does:**
- Creates a Telegram session for Portal API
- Generates `portal_session_string.txt`
- Generates `account.session` file
- These files allow the bot to authenticate with Portal API

**You'll need to provide:**
1. Your phone number (with country code, e.g., +1234567890)
2. Verification code from Telegram
3. 2FA password (if enabled)

**⚠️ SECURITY:**
- These files give access to your Telegram account
- Keep them SECRET
- Never commit to git (already in .gitignore)
- Use a dedicated account for production

### Step 3: Verify Configuration
```bash
# Check .env file has all required variables
cat .env
```

Required variables:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
PORTAL_API_ID=22307634
PORTAL_API_HASH=your_hash
TELEGRAM_API_ID=22307634
TELEGRAM_API_HASH=your_hash
```

### Step 4: Test Portal API
```bash
python3 -c "
import asyncio
from services.portal_api import fetch_gift_data

async def test():
    data = await fetch_gift_data('Tama Gadget')
    print('✅ Portal API working!' if data else '❌ Portal API failed!')

asyncio.run(test())
"
```

### Step 5: Start the Bot

**Option A: Direct Python**
```bash
python3 core/telegram_bot.py
```

**Option B: With Startup Script**
```bash
python3 core/start_bot.py
```

**Option C: Docker (Production)**
```bash
docker-compose up -d
```

---

## 🔧 TROUBLESHOOTING

### Issue: "No auth token available"
**Solution:** Run `python3 setup_portal_auth.py` first

### Issue: "Session authentication required"
**Solution:** Delete old session files and run setup again:
```bash
rm account.session portal_session_string.txt
python3 setup_portal_auth.py
```

### Issue: "Could not resolve host portals-market.com"
**Solution:** Check your internet connection and DNS settings

### Issue: "Rate limited"
**Solution:** Wait 2-5 minutes, the bot handles this automatically

---

## 📊 PRODUCTION CHECKLIST

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Portal authentication setup (`python3 setup_portal_auth.py`)
- [ ] `.env` file configured with all variables
- [ ] Session files created (`portal_session_string.txt`, `account.session`)
- [ ] Portal API tested and working
- [ ] Bot token valid and active
- [ ] Database directories exist (`sqlite_data/`)
- [ ] Asset directories exist (`assets/`, `card_templates/`, etc.)
- [ ] Logs directory exists (`data/logs/`)

---

## 🎯 FOR 1200+ USERS

### Performance Optimization:
1. **Use Docker** for better resource management
2. **Enable pregeneration** (runs every 32 minutes)
3. **Monitor rate limits** (5 req/min per user)
4. **Database backups** (automatic hourly)

### Scaling Recommendations:
- **Memory**: Allocate 1GB minimum
- **CPU**: 2 cores recommended
- **Storage**: 2GB for cards and databases
- **Network**: Stable connection required

### Monitoring:
```bash
# Check bot logs
tail -f data/logs/telegram_bot.log

# Check Portal API logs
tail -f data/logs/gift_api_results.log

# Check system resources
docker stats  # if using Docker
```

---

## 🔒 SECURITY FOR PRODUCTION

1. **Session Files**: Keep `account.session` and `portal_session_string.txt` secure
2. **Environment Variables**: Never commit `.env` to git
3. **Bot Token**: Regenerate if compromised
4. **Rate Limiting**: Already implemented (5 req/min)
5. **Admin Access**: Only trusted user IDs in `ADMIN_USER_IDS`

---

## 📞 SUPPORT

If you encounter issues:
1. Check logs in `data/logs/`
2. Verify Portal API authentication
3. Test with a single gift first
4. Check network connectivity

---

**Last Updated**: February 3, 2026  
**For**: Production deployment with 1200+ users
