# Security Audit Report

## 🔒 Security Issues Found

### 🔴 CRITICAL - Hardcoded Sensitive Data

#### 1. Hardcoded User Authentication Data
**File**: `services/mrkt_api.py` (Line 73)
**Severity**: CRITICAL
**Issue**: Full authentication data including user ID, signature, and hash hardcoded in source code

```python
AUTH_DATA = {
    "data": "user=%7B%22id%22%3A7660176383%2C%22first_name%22%3A%22Afsado%22...",
    "photo": "https://t.me/i/userpic/320/...",
    "appId": None
}
```

**Risk**:
- Exposes user ID: `7660176383`
- Exposes username: `Afsado`
- Contains authentication signature and hash
- Anyone with access to code can impersonate this user
- Signature may be used to access MRKT API

**Fix**: 
- Remove hardcoded AUTH_DATA
- Generate auth data dynamically using Telegram session
- Store sensitive data in environment variables
- Use secure token rotation

---

#### 2. Hardcoded Referral IDs
**File**: `core/bot_config.py` (Lines 41-55)
**Severity**: MEDIUM
**Issue**: Personal referral IDs hardcoded in config

```python
DEFAULT_BUY_SELL_LINK = "https://t.me/tonnel_network_bot/gifts?startapp=ref_7660176383"
DEFAULT_MRKT_LINK = "https://t.me/mrkt/app?startapp=7660176383"
```

**Exposed IDs**:
- `7660176383` - Main referral ID
- `1251203296` - Special group 1
- `1109811477` - Special group 2

**Risk**:
- Referral IDs can be tracked
- Competitors can see your referral strategy
- IDs linked to specific Telegram accounts

**Fix**:
- Move to environment variables
- Use configuration file not in git
- Consider using dynamic referral generation

---

#### 3. Hardcoded Group IDs
**File**: `core/bot_config.py` (Lines 40-48)
**Severity**: LOW
**Issue**: Specific Telegram group IDs hardcoded

```python
SPECIAL_GROUPS = {
    -1002155968676: {...},
    -1001891015899: {...}
}
```

**Risk**:
- Reveals which groups have special treatment
- Group IDs can be used to find actual groups
- Privacy concern for group owners

**Fix**:
- Move to database or config file
- Use environment variables for sensitive groups
- Document that these are example IDs

---

### 🟡 MEDIUM - Hardcoded URLs and Endpoints

#### 4. Hardcoded API Endpoints
**Files**: Multiple
**Severity**: MEDIUM

```python
# mrkt_api.py
API_BASE = 'https://api.tgmrkt.io'

# bot_config.py
CDN_BASE_URL = "https://giftschart.the01studio.xyz/api"

# ton_price_utils.py
ton_url = "https://coinmarketcap.com/currencies/toncoin/"
```

**Risk**:
- Hard to change endpoints in production
- No fallback if service moves
- Difficult to test with different environments

**Fix**:
- Move to environment variables
- Add fallback URLs
- Use configuration management

---

#### 5. Hardcoded Telegram Links
**File**: `core/telegram_bot.py` (Multiple lines)
**Severity**: LOW

```python
[InlineKeyboardButton("Join our channel", url="https://t.me/The01Studio")]
[InlineKeyboardButton("Donate", url="https://app.tonkeeper.com/transfer/UQC...")]
```

**Risk**:
- Channel links can't be changed without code update
- Donation address is public (but that's okay for donations)

**Fix**:
- Move to configuration file
- Allow dynamic channel links
- Keep donation address in config

---

### 🟢 LOW - Information Disclosure

#### 6. Hardcoded Phone Number Reference
**File**: `setup_pyrogram_session.py`
**Severity**: INFO
**Issue**: Example phone number format shown

```python
print("  1. Enter your phone number (with country code, e.g., +1234567890)")
```

**Risk**: None - This is just an example

---

#### 7. Hardcoded Telegram API IP
**File**: `core/bot_config.py` (Line 33)
**Severity**: INFO

```python
API_TELEGRAM_IP = "149.154.167.220"
```

**Risk**: None - This is a public Telegram server IP

---

## 🛡️ Security Recommendations

### Immediate Actions (Critical)

1. **Remove AUTH_DATA from mrkt_api.py**
   ```python
   # REMOVE THIS:
   AUTH_DATA = {...}
   
   # REPLACE WITH:
   def get_auth_data():
       return {
           "data": os.getenv("MRKT_AUTH_DATA"),
           "photo": os.getenv("MRKT_USER_PHOTO"),
           "appId": None
       }
   ```

2. **Move Referral IDs to Environment**
   ```bash
   # .env
   DEFAULT_REFERRAL_ID=7660176383
   SPECIAL_GROUP_1_ID=-1002155968676
   SPECIAL_GROUP_1_REF=1251203296
   ```

3. **Rotate Exposed Credentials**
   - Generate new MRKT authentication
   - Consider new referral codes if compromised
   - Update any exposed API keys

### Short-term Actions (High Priority)

4. **Create Secure Configuration System**
   ```python
   # config/secure_config.py
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   
   class SecureConfig:
       # API Endpoints
       MRKT_API_BASE = os.getenv("MRKT_API_BASE", "https://api.tgmrkt.io")
       CDN_BASE_URL = os.getenv("CDN_BASE_URL")
       
       # Referral IDs
       DEFAULT_REFERRAL_ID = os.getenv("DEFAULT_REFERRAL_ID")
       
       # Telegram
       COMMUNITY_CHANNEL = os.getenv("COMMUNITY_CHANNEL", "@The01Studio")
       DONATION_ADDRESS = os.getenv("DONATION_ADDRESS")
   ```

5. **Update .gitignore**
   ```gitignore
   # Sensitive files
   *.session
   *_auth_token.txt
   *_session_string.txt
   .env
   .env.local
   .env.production
   config/secure_config.py
   ```

6. **Add .env.example**
   ```bash
   # .env.example
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   DEFAULT_REFERRAL_ID=your_referral_id
   MRKT_API_BASE=https://api.tgmrkt.io
   CDN_BASE_URL=https://your-cdn.com/api
   COMMUNITY_CHANNEL=@YourChannel
   ```

### Long-term Actions (Medium Priority)

7. **Implement Secrets Management**
   - Use HashiCorp Vault or AWS Secrets Manager
   - Rotate credentials regularly
   - Implement secret versioning

8. **Add Security Headers**
   ```python
   # For CDN server
   @app.after_request
   def add_security_headers(response):
       response.headers['X-Content-Type-Options'] = 'nosniff'
       response.headers['X-Frame-Options'] = 'DENY'
       response.headers['X-XSS-Protection'] = '1; mode=block'
       return response
   ```

9. **Implement Rate Limiting for APIs**
   - Add rate limiting to CDN endpoints
   - Implement IP-based throttling
   - Add authentication for sensitive endpoints

10. **Security Monitoring**
    - Log all authentication attempts
    - Monitor for unusual API usage
    - Set up alerts for failed auth attempts

---

## 📋 Security Checklist

### Before Deployment

- [ ] Remove all hardcoded credentials
- [ ] Move sensitive data to environment variables
- [ ] Update .gitignore with all sensitive files
- [ ] Create .env.example for documentation
- [ ] Rotate any exposed credentials
- [ ] Review all API endpoints
- [ ] Check for exposed user data
- [ ] Verify database credentials are secure
- [ ] Test with production-like environment
- [ ] Document all environment variables

### Regular Maintenance

- [ ] Rotate API keys monthly
- [ ] Review access logs weekly
- [ ] Update dependencies for security patches
- [ ] Audit code for new hardcoded data
- [ ] Check for exposed secrets in git history
- [ ] Review and update .gitignore
- [ ] Test backup and restore procedures
- [ ] Verify encryption for sensitive data

---

## 🔍 How to Check for Secrets

### Scan for Hardcoded Secrets
```bash
# Search for potential secrets
grep -r "api_key\|API_KEY\|token\|TOKEN\|password\|PASSWORD" --include="*.py" .

# Search for URLs with credentials
grep -r "://.*:.*@" --include="*.py" .

# Search for hardcoded IPs
grep -r "[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}" --include="*.py" .
```

### Check Git History
```bash
# Search git history for secrets
git log -p | grep -i "password\|token\|api_key"

# Use git-secrets tool
git secrets --scan
```

---

## 📚 Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Telegram Bot Security](https://core.telegram.org/bots/security)
- [Git Secrets Tool](https://github.com/awslabs/git-secrets)

---

## 📝 Summary

**Total Issues Found**: 7
- 🔴 Critical: 1 (Hardcoded AUTH_DATA)
- 🟡 Medium: 4 (Referral IDs, Group IDs, API endpoints, Telegram links)
- 🟢 Low: 2 (Information disclosure)

**Priority Actions**:
1. Remove AUTH_DATA from mrkt_api.py immediately
2. Move all referral IDs to environment variables
3. Create secure configuration system
4. Update .gitignore and create .env.example
5. Rotate any exposed credentials

**Status**: ⚠️ **NEEDS IMMEDIATE ATTENTION**

The most critical issue is the hardcoded authentication data in `mrkt_api.py`. This should be removed and replaced with environment-based configuration immediately.

---

*Last Updated: February 4, 2026*
*Auditor: Security Review*
