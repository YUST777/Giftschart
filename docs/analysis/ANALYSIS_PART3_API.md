# Part 3: API Integration Analysis

## 🔌 PORTAL API INTEGRATION (portal_api.py)

### Authentication System:

```python
# Token Management
_portal_auth_token = None
_token_last_refreshed = 0
TOKEN_REFRESH_INTERVAL = 1920  # 32 minutes

# Rate Limiting
_last_request_time = 0
MIN_REQUEST_INTERVAL = 0.5  # 500ms between requests
_rate_limit_until = 0
```

### Key Functions:

1. **get_fresh_auth_token()**
   ```python
   async def get_fresh_auth_token():
       # Try session string first
       session_string = await load_session_string()
       if session_string:
           token = await update_auth(
               session_string=session_string,
               session_path=_project_root,
               session_name="account"
           )
       # Fallback to API credentials
       token = await update_auth(
           api_id=API_ID,
           api_hash=API_HASH
       )
   ```

2. **apply_request_rate_limiting()**
   - Enforces 500ms between requests
   - Handles 429 rate limit errors
   - Exponential backoff on failures

3. **fetch_gift_data()**
   - Primary: Portal API search
   - Fallback: Legacy API
   - Caches supply data (10 min)

### API Call Flow:
```
Request → Rate Limit Check → Get Auth Token → Portal Search
    ↓
Success? → Process Results → Return Data
    ↓
Failure? → Legacy API Fallback → Return Data
```

### Environment Variables Required:
```bash
PORTAL_API_ID=22307634
PORTAL_API_HASH=7ab906fc6d065a2047a84411c1697593
```

## 📊 LEGACY API (Fallback)

### Endpoints:
```python
GIFTS_API = "https://giftcharts-api.onrender.com/gifts"
CHART_API = "https://giftcharts-api.onrender.com/weekChart?name="
```

### Usage:
- Supply data when Portal fails
- Chart generation
- Backup pricing data
- Historical data
