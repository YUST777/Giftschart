# Part 5: Rate Limiting & Security

## 🛡️ RATE LIMITER (rate_limiter.py)

### Database Schema:
```sql
-- User gift requests
CREATE TABLE user_requests (
    user_id INTEGER,
    chat_id INTEGER,
    gift_name TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, chat_id, gift_name)
);

-- Command requests
CREATE TABLE command_requests (
    user_id INTEGER,
    chat_id INTEGER,
    command_name TEXT,
    minute INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, chat_id, command_name)
);

-- Message ownership
CREATE TABLE message_owners (
    user_id INTEGER,
    chat_id INTEGER,
    message_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, chat_id, message_id)
);
```

### Rate Limiting Logic:

```python
def can_user_request_gift(user_id, chat_id, gift_name):
    # Check if user requested this gift in last minute
    query = """
        SELECT timestamp FROM user_requests
        WHERE user_id = ? AND chat_id = ? AND gift_name = ?
    """
    # If found and < 60 seconds ago: DENY
    # Else: ALLOW and update timestamp
```

### Command Rate Limiting:
```python
REQUESTS_PER_MINUTE = 5

def can_user_use_command(user_id, chat_id, command_name):
    current_minute = int(time.time() / 60)
    # Count requests in current minute
    # If >= 5: DENY
    # Else: ALLOW and increment
```

### Message Ownership:
```python
def register_message(user_id, chat_id, message_id):
    # Store who requested each message
    # Used for delete permission checking
```

```python
def can_user_delete_message(user_id, chat_id, message_id):
    # Check if user owns this message
    # Only owner can delete
```

## 🔒 SECURITY FEATURES

### 1. Timestamp Filtering
```python
def is_message_too_old(update, max_age_seconds=300):
    message_time = update.message.date
    current_time = datetime.datetime.now(message_time.tzinfo)
    time_difference = current_time - message_time
    
    if time_difference.total_seconds() > max_age_seconds:
        return True  # Ignore old messages
```

### 2. Admin Verification
```python
ADMIN_USER_IDS = [800092886, 6529233780]

def is_admin(user_id):
    return user_id in ADMIN_USER_IDS
```

### 3. Payment Security
- Telegram Stars integration (secure)
- Pre-checkout validation
- Payment ID verification
- Refund tracking (one-time per group)

### 4. Input Validation
```python
def sanitize_callback_data(text):
    # Only alphanumeric, underscore, hyphen
    return re.sub(r'[^a-zA-Z0-9_-]', '_', text)
```
