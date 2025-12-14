# Part 9: Database Schema & Queries

## 💾 DATABASE ARCHITECTURE

### Database Files:
```
sqlite_data/
├── premium_system.db      # Premium subscriptions & payments
├── user_requests.db        # Rate limiting & message ownership
└── analytics.db            # Usage statistics (optional)
```

## 📊 COMPLETE SCHEMA DEFINITIONS

### 1. premium_system.db

#### premium_subscriptions
```sql
CREATE TABLE premium_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,              -- Telegram user ID who paid
    group_id INTEGER NOT NULL,              -- Group ID (starts with -100)
    payment_id TEXT NOT NULL,               -- Unique payment identifier
    telegram_payment_charge_id TEXT,        -- Telegram's charge ID
    stars_amount INTEGER NOT NULL,          -- Amount paid in Stars
    mrkt_link TEXT,                         -- Custom MRKT referral link
    palace_link TEXT,                       -- Custom Palace referral link
    tonnel_link TEXT,                       -- Custom Tonnel referral link
    portal_link TEXT,                       -- Custom Portal referral link
    created_at INTEGER NOT NULL,            -- Unix timestamp
    expires_at INTEGER,                     -- Unix timestamp (30 days)
    is_active BOOLEAN DEFAULT 1,            -- Active status
    UNIQUE(owner_id, group_id)              -- One subscription per owner-group
);

CREATE INDEX idx_group_id ON premium_subscriptions(group_id);
CREATE INDEX idx_owner_id ON premium_subscriptions(owner_id);
CREATE INDEX idx_expires_at ON premium_subscriptions(expires_at);
```

#### payment_history
```sql
CREATE TABLE payment_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    payment_id TEXT NOT NULL,
    stars_amount INTEGER NOT NULL,
    status TEXT NOT NULL,                   -- 'pending', 'completed', 'failed'
    created_at INTEGER NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES premium_subscriptions(owner_id)
);

CREATE INDEX idx_payment_owner ON payment_history(owner_id);
CREATE INDEX idx_payment_status ON payment_history(status);
```

#### pending_payments
```sql
CREATE TABLE pending_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    payment_id TEXT NOT NULL UNIQUE,
    stars_amount INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,            -- 30 minutes from creation
    UNIQUE(payment_id)
);

CREATE INDEX idx_pending_expires ON pending_payments(expires_at);
```

#### refunds
```sql
CREATE TABLE refunds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    payment_id TEXT NOT NULL,
    telegram_payment_charge_id TEXT,
    reason TEXT,
    status TEXT DEFAULT 'pending',          -- 'pending', 'approved', 'rejected'
    created_at INTEGER NOT NULL,
    processed_at INTEGER,
    processed_by TEXT,                      -- Admin who processed
    FOREIGN KEY (owner_id, group_id) 
        REFERENCES premium_subscriptions(owner_id, group_id)
);

CREATE INDEX idx_refund_status ON refunds(status);
CREATE INDEX idx_refund_group ON refunds(group_id);
```

#### refunded_groups
```sql
CREATE TABLE refunded_groups (
    group_id INTEGER PRIMARY KEY,
    refund_date INTEGER NOT NULL,
    UNIQUE(group_id)                        -- One refund per group ever
);
```

### 2. user_requests.db

#### user_requests
```sql
CREATE TABLE user_requests (
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    gift_name TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, chat_id, gift_name)
);

CREATE INDEX idx_user_timestamp ON user_requests(user_id, timestamp);
CREATE INDEX idx_chat_timestamp ON user_requests(chat_id, timestamp);
```

#### command_requests
```sql
CREATE TABLE command_requests (
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    command_name TEXT NOT NULL,
    minute INTEGER NOT NULL,                -- Current minute (time/60)
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, chat_id, command_name, minute)
);

CREATE INDEX idx_command_minute ON command_requests(minute);
```

#### message_owners
```sql
CREATE TABLE message_owners (
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, chat_id, message_id)
);

CREATE INDEX idx_message_user ON message_owners(user_id);
CREATE INDEX idx_message_chat ON message_owners(chat_id);
```

## 🔍 KEY QUERIES

### Premium System Queries:

```sql
-- Check if group is premium
SELECT is_active, expires_at 
FROM premium_subscriptions 
WHERE group_id = ? AND is_active = 1 
AND (expires_at IS NULL OR expires_at > ?);

-- Get premium links for group
SELECT mrkt_link, palace_link, tonnel_link, portal_link
FROM premium_subscriptions
WHERE group_id = ? AND is_active = 1;

-- Get user's premium groups
SELECT group_id, created_at, expires_at
FROM premium_subscriptions
WHERE owner_id = ? AND is_active = 1;

-- Check if group was refunded
SELECT 1 FROM refunded_groups WHERE group_id = ?;
```

### Rate Limiting Queries:

```sql
-- Check gift request rate limit
SELECT timestamp FROM user_requests
WHERE user_id = ? AND chat_id = ? AND gift_name = ?;

-- Check command rate limit
SELECT COUNT(*) FROM command_requests
WHERE user_id = ? AND chat_id = ? 
AND command_name = ? AND minute = ?;

-- Check message ownership
SELECT 1 FROM message_owners
WHERE user_id = ? AND chat_id = ? AND message_id = ?;
```
