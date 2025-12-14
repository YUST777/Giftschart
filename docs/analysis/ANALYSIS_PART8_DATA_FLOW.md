# Part 8: Complete Data Flow Analysis

## 🔄 USER REQUEST FLOW

### 1. Gift Card Request
```
User types "tama" in group
    ↓
telegram_bot.py: handle_message()
    ↓
Check: is_message_too_old() → Skip if > 5 min old
    ↓
rate_limiter.py: can_user_request_gift()
    ↓
If rate limited → Send "wait X seconds" message
    ↓
find_matching_gifts("tama")
    ↓
Match found: "Tama Gadget"
    ↓
get_gift_card_by_name("Tama Gadget")
    ↓
Check: new_gift_cards/Tama_Gadget_card.webp exists?
    ↓
If not exists → generate_gift_card()
    ↓
portal_api.py: fetch_gift_data("Tama Gadget")
    ↓
Portal API search → Get price, supply, etc.
    ↓
gift_card_generator.py: generate_specific_gift()
    ↓
Load template: card_templates/Tama_Gadget_template.png
Load metadata: card_metadata/Tama_Gadget_metadata.json
Load image: downloaded_images/Tama_Gadget.webp
    ↓
Generate gradient background from dominant color
    ↓
Overlay: image, price, supply, TON logo, star logo
    ↓
Save: new_gift_cards/Tama_Gadget_card.webp
    ↓
send_gift_card()
    ↓
Check premium status: premium_system.is_group_premium()
    ↓
Generate buttons with custom/default links
    ↓
Send photo with caption and buttons
    ↓
register_message() → Store message ownership
    ↓
User receives gift card
```

### 2. Premium Subscription Flow
```
User clicks "💫 Get Premium" button
    ↓
premium_system.py: handle_premium_button()
    ↓
Check: Is private chat? → If no, ask to DM
    ↓
Send Telegram Stars invoice (1 Star)
    ↓
Create pending_payments record
    ↓
User completes payment in Telegram
    ↓
Telegram sends pre_checkout_query
    ↓
handle_pre_checkout_query()
    ↓
Validate payment_id exists in pending_payments
    ↓
Answer pre-checkout query with OK
    ↓
Telegram processes payment
    ↓
Telegram sends successful_payment update
    ↓
handle_successful_payment()
    ↓
Save to premium_subscriptions table
    ↓
Set expires_at = now + 30 days
    ↓
Start group setup flow
    ↓
Ask user to share group
    ↓
User shares group → Get group_id
    ↓
Validate group_id (must start with -100)
    ↓
Ask for MRKT link → Validate format
    ↓
Ask for Palace link → Validate format
    ↓
Ask for Tonnel link → Validate format
    ↓
Ask for Portal link → Validate format
    ↓
Save all links to premium_subscriptions
    ↓
Set is_active = 1
    ↓
Send confirmation message
    ↓
Premium features activated
```

### 3. Sticker Request Flow
```
User types "/sticker" or searches inline
    ↓
sticker_command() or inline_query()
    ↓
Show collection browser
    ↓
User selects collection (e.g., "Pudgy Penguins")
    ↓
sticker_integration.py: handle_sticker_callback()
    ↓
Load collection metadata
    ↓
Show sticker list with prices
    ↓
User selects sticker (e.g., "Blue Pengu")
    ↓
Get sticker metadata from sticker_metadata/
    ↓
Check: Sticker_Price_Cards/{collection}_{sticker}.webp exists?
    ↓
If not → generate_sticker_price_card()
    ↓
Fetch price from stickers.tools API
    ↓
Generate card with price, supply, image
    ↓
Save to Sticker_Price_Cards/
    ↓
Send sticker card with buttons
    ↓
User receives sticker price card
```

## 📊 SCHEDULED PROCESSES

### Card Pregeneration (Every 32 minutes)
```
scheduler service starts
    ↓
pregenerate_gift_cards.py: main()
    ↓
Read data/all_gift_names.txt
    ↓
For each gift (77+ gifts):
    ↓
    portal_api.fetch_gift_data(gift_name)
    ↓
    gift_card_generator.generate_specific_gift()
    ↓
    Save to new_gift_cards/
    ↓
Update last_generation_time.txt
    ↓
Log results to pregenerate_cards.log
    ↓
Sleep 32 minutes
    ↓
Repeat
```

### Sticker Price Updates
```
sticker service starts
    ↓
scheduled_sticker_update.py: main()
    ↓
Fetch all sticker collections
    ↓
For each sticker:
    ↓
    Get current price from API
    ↓
    Compare with cached price
    ↓
    If changed:
        ↓
        Update metadata JSON
        ↓
        Regenerate price card
    ↓
Log update results
    ↓
Sleep until next update
```
