# 🔴 Fix Live Prices - Remove Mock Data

## Problem

Your bot is using **mock/hardcoded data** instead of **live prices** from APIs because:
1. ❌ Portal API session is corrupted
2. ❌ Fallback to mock data when APIs fail

## Solution

Fix the Portal API session to get **100% live prices** from:
- ✅ Portal API (primary)
- ✅ MRKT API (fallback)
- ✅ Tonnel API (fallback)
- ✅ Quant API (fallback)

---

## Step 1: Fix Portal API Session (5 minutes)

### Run the Fix Script

```bash
python3 fix_portal_session.py
```

### What It Will Ask

1. **Phone number**: Enter with country code (e.g., `+1234567890`)
2. **Verification code**: Check your Telegram app for the code
3. **2FA password** (if enabled): Enter your 2FA password

### Expected Output

```
✅ Session Created Successfully!

Files created:
  • account.session (Pyrogram session file)
  • portal_session_string.txt (session string)

Your bot can now use Portal API for live prices!
```

---

## Step 2: Restart Bot

```bash
# Kill old bot
pkill -f telegram_bot.py

# Start fresh
python3 core/telegram_bot.py
```

---

## Step 3: Verify Live Prices

```bash
# Test Portal API
python3 test_portal_live.py
```

Expected output:
```
✅ Portal API working
✅ Live prices fetched
✅ No mock data
```

---

## Step 4: Regenerate Cards with Live Data

```bash
# Delete old cards with mock data
rm -rf new_gift_cards/*.webp

# Delete timestamp to force regeneration
rm -f data/last_generation_time.txt

# Generate fresh cards with LIVE prices
python3 generators/pregenerate_gift_cards.py
```

This will generate **103 cards with 100% live prices**.

---

## API Priority (No Mock Data)

### Gift Prices

```
1. Portal API (primary) ✅
   ↓ if fails
2. MRKT API (fallback) ✅
   ↓ if fails
3. Tonnel API (fallback) ✅
   ↓ if fails
4. Quant API (fallback) ✅
   ↓ if ALL fail
5. ❌ ERROR (no mock data)
```

### Chart Data

```
1. Portal API chart ✅
   ↓ if fails
2. MRKT historical ✅
   ↓ if fails
3. ❌ ERROR (no mock data)
```

---

## Remove Mock Data Fallbacks

If you want to **completely disable mock data** (bot will error instead):

### Edit `services/portal_api.py`

Find these functions and comment them out:
- `_generate_mock_gift_data()`
- `_generate_mock_chart_data()`

Replace calls with:
```python
# Instead of: return _generate_mock_chart_data(gift_name)
return None  # Force error if API fails
```

### Edit `services/mrkt_quant_api.py`

Find `_generate_mock_data()` and comment it out.

Replace calls with:
```python
# Instead of: result = _generate_mock_data(gift_name)
return None  # Force error if API fails
```

---

## Verify No Mock Data

### Check Logs

```bash
tail -f data/logs/gift_api_results.log | grep -i mock
```

Should show **nothing** if all APIs are working.

### Check Card Generation

```bash
tail -f data/logs/pregenerate_cards.log | grep -i mock
```

Should show **nothing** if Portal API is working.

---

## Current API Status

### Portal API
- **Status**: ❌ Broken (session corrupted)
- **Fix**: Run `python3 fix_portal_session.py`
- **Provides**: Live prices + chart data

### MRKT API
- **Status**: ✅ Working (uses local JSON)
- **Provides**: Live prices (no chart)

### Tonnel API
- **Status**: ✅ Working
- **Provides**: Live prices (no chart)

### Quant API
- **Status**: ✅ Working
- **Provides**: Live prices (no chart)

---

## Quick Fix Commands

```bash
# 1. Fix Portal session
python3 fix_portal_session.py

# 2. Test it works
python3 test_portal_live.py

# 3. Restart bot
pkill -f telegram_bot.py && python3 core/telegram_bot.py &

# 4. Regenerate cards with live data
rm -rf new_gift_cards/*.webp
rm -f data/last_generation_time.txt
python3 generators/pregenerate_gift_cards.py

# 5. Verify no mock data
tail -f data/logs/gift_api_results.log | grep -i mock
# Should show nothing!
```

---

## Why Mock Data Was Used

From the logs:
```
[Portal Auth] Session file authentication failed: no such column: number
[Portal API] No auth token available, cannot make request
[Portal API] All attempts failed, falling back to legacy API
[Legacy API] HTTP 403
[FINAL FALLBACK] All APIs failed, returning None
[Mock Data] Generated 24 chart points
```

**Root cause**: Corrupted Pyrogram session file

**Solution**: Regenerate session with `fix_portal_session.py`

---

## After Fix

### Expected Logs

```
[Portal Auth] ✅ Session loaded successfully
[Portal API] ✅ Gift: Tama Gadget | Price: 2.64 TON
[Portal API] ✅ Chart data fetched (24 points)
✅ Card generated with LIVE data
```

### No More Mock Data

```
❌ [Mock Data] - REMOVED
❌ [Mock] - REMOVED
❌ using mock data - REMOVED
```

---

## Troubleshooting

### "Session file authentication failed"
→ Run `python3 fix_portal_session.py` to create fresh session

### "HTTP 403" from APIs
→ Normal, bot will try next API in chain

### "All APIs failed"
→ Check internet connection, verify API keys in `.env`

### Still seeing mock data
→ Delete old cards: `rm -rf new_gift_cards/*.webp`
→ Regenerate: `python3 generators/pregenerate_gift_cards.py`

---

## Summary

**Current State**: ❌ Mock data (Portal session broken)  
**After Fix**: ✅ 100% live prices from APIs  
**Time to Fix**: 5 minutes  
**Commands**: 5 simple commands  

**Run this now**:
```bash
python3 fix_portal_session.py
```

Then your bot will have **100% live prices, zero mock data**! 🚀
