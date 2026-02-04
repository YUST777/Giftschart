# Part 2: Premium System Deep Dive

## 💎 PREMIUM SYSTEM (premium_system.py - 1,613 lines)

### Class: PremiumSystem

#### Database Schema:
```sql
-- premium_subscriptions table
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
```

### Payment Flow:

1. **handle_premium_button()**
   - Checks if private chat
   - Sends Telegram Stars invoice
   - Price: 1 Star (test mode)
   - Creates pending payment record

2. **handle_pre_checkout_query()**
   - Validates payment before processing
   - Checks pending payment exists
   - Answers with OK or error

3. **handle_successful_payment()**
   - Receives payment confirmation
   - Saves to premium_subscriptions
   - Starts group setup flow
   - 30-day subscription period

4. **handle_premium_setup()**
   - Step-by-step link collection
   - Validates each link format
   - Stores custom referral links
   - Activates premium features

### Link Validation:
```python
def is_valid_link(link, kind):
    patterns = {
        "mrkt": r"https://t\.me/mrkt/app\?startapp=\d+",
        "palace": r"https://t\.me/palacenftbot/app\?startapp=[a-zA-Z0-9]+",
        "tonnel": r"https://t\.me/[Tt]onnel_[Nn]etwork_bot/gifts\?startapp=ref_\d+",
        "portal": r"https://t\.me/portals/market\?startapp=[a-zA-Z0-9_-]+"
    }
```

### Refund System:
- 3-day refund window
- One-time per group policy
- Instant Telegram Stars refund
- Tracks refunded_groups table
