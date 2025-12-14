import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Reduce logging for HTTP requests
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Import special groups configuration
try:
    from bot_config import (
        SPECIAL_GROUPS, DEFAULT_BUY_SELL_LINK, DEFAULT_TONNEL_LINK, DEFAULT_PALACE_LINK, DEFAULT_PORTAL_LINK, DEFAULT_MRKT_LINK
    )
except ImportError:
    # Default values if config file is missing
    SPECIAL_GROUPS = {}
    DEFAULT_BUY_SELL_LINK = "https://t.me/tonnel_network_bot/gifts?startapp=ref_7660176383"
    DEFAULT_TONNEL_LINK = "https://t.me/tonnel_network_bot/gifts?startapp=ref_7660176383"
    DEFAULT_PALACE_LINK = "https://t.me/palacenftbot/app?startapp=zOyJPdbc9t"
    DEFAULT_PORTAL_LINK = "https://t.me/portals/market?startapp=q7iu6i"
    DEFAULT_MRKT_LINK = "https://t.me/mrkt/app?startapp=7660176383"

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries."""
    query = update.callback_query
    await query.answer()  # Answer callback query to stop loading animation
    
    callback_data = query.data
    logger.info(f"Received callback query: {callback_data}")
    
    # Handle premium button callbacks (including user-specific ones)
    if callback_data == "premium_button" or callback_data.startswith("premium_button:"):
        logger.info("Premium button clicked - starting processing")
        
        # Apply rate limiting FIRST (before any other checks)
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            logger.info(f"Checking rate limit for user {user_id} in chat {chat_id}")
            
            from rate_limiter import can_user_use_command
            can_use, seconds_remaining = can_user_use_command(user_id, chat_id, "premium_button")
            
            if not can_use:
                # User is rate limited for premium button
                logger.info(f"🚫 RATE LIMIT HIT: User {user_id} is rate limited for premium button - {seconds_remaining} seconds remaining")
                await query.answer(f"⏱️ Spam protection: Wait {seconds_remaining}s", show_alert=True)
                return
            else:
                logger.info(f"✅ Rate limit passed for user {user_id}")
        except ImportError:
            # Rate limiter not available, continue without rate limiting
            logger.warning("Rate limiter not available, continuing without rate limiting")
        except Exception as e:
            # Log any other errors but continue processing
            logger.error(f"Error in premium button rate limiting: {e}")
        
        # Check if this is a user-specific button
        if callback_data.startswith("premium_button:"):
            # Extract the authorized user ID from callback data
            try:
                authorized_user_id = int(callback_data.split(":")[1])
                current_user_id = update.effective_user.id
                
                # Check if the current user is authorized to use this button
                if current_user_id != authorized_user_id:
                    logger.info(f"User {current_user_id} tried to use premium button authorized for user {authorized_user_id}")
                    await query.answer("🚫 This button can only be used by the person who requested the gift card.", show_alert=True)
                    return
                
                logger.info(f"User {current_user_id} authorized to use premium button")
            except (ValueError, IndexError):
                logger.error(f"Invalid premium button callback data format: {callback_data}")
                await query.answer("❌ Invalid button data", show_alert=True)
                return
        
        # Check if user is in private chat (required for premium operations)
        if update.effective_chat.type != "private":
            logger.info("Premium button clicked in non-private chat - showing promotional message")
            
            # Send a promotional message with image instead of just an alert
            promotional_message = (
                "🚀 Premium: 99★ / 30d\n"
                "• Custom Ref links\n"
                "• Branded price cards\n"
                "• Priority support\n"
                "• No Ads\n\n"
                "💬 Start: DM @giftsChartBot → /premium\n"
                "🔁 3d refund"
            )
            
            try:
                # Get script directory for cross-platform compatibility
                import os
                script_dir = os.path.dirname(os.path.abspath(__file__))
                premium_image_path = os.path.join(script_dir, "assets", "premium.jpg")
                
                # Send photo with promotional message as caption
                if os.path.exists(premium_image_path):
                    promo_message = await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=open(premium_image_path, 'rb'),
                        caption=promotional_message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_to_message_id=query.message.message_id
                    )
                else:
                    # Fallback to text message if image not found
                    promo_message = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=promotional_message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_to_message_id=query.message.message_id
                    )
                
                # Register the promotional message as linked to the original message
                try:
                    from rate_limiter import register_linked_message
                    register_linked_message(user_id, update.effective_chat.id, query.message.message_id, promo_message.message_id)
                except Exception as reg_e:
                    logger.error(f"Error registering linked message: {reg_e}")
                
                await query.answer("💫 Premium info sent! Check the message above.")
            except Exception as e:
                logger.error(f"Error sending promotional message: {e}")
                await query.answer("💫 Message me privately @TWETestBot and use /premium to get started!", show_alert=True)
            return
        
        logger.info("Premium button clicked in private chat - proceeding with premium setup")
        
        logger.info("Calling handle_premium_button function")
        try:
            from premium_system import handle_premium_button
            await handle_premium_button(update, context)
            logger.info("handle_premium_button completed successfully")
        except ImportError:
            logger.error("Premium system import failed")
            await query.answer("Premium system not available", show_alert=True)
        except Exception as e:
            logger.error(f"Error in handle_premium_button: {e}")
            await query.answer("An error occurred while processing premium request", show_alert=True)
        return
    
    elif callback_data == "premium_info":
        # Apply rate limiting for premium info button
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            
            from rate_limiter import can_user_use_command
            can_use, seconds_remaining = can_user_use_command(user_id, chat_id, "premium_info")
            
            if not can_use:
                # User is rate limited for premium info button
                await query.answer(f"⏱️ Please wait {seconds_remaining} seconds before clicking Premium Info again.", show_alert=True)
                return
        except ImportError:
            # Rate limiter not available, continue without rate limiting
            logger.warning("Rate limiter not available, continuing without rate limiting")
        except Exception as e:
            # Log any other errors but continue processing
            logger.error(f"Error in premium info button rate limiting: {e}")
        
        await query.answer("💫 This group has an active premium subscription!", show_alert=True)
        return
    
    elif callback_data == "cancel_premium":
        # Check if user is in private chat (required for premium operations)
        if update.effective_chat.type != "private":
            await query.answer("💫 Premium operations can only be performed in private chat.", show_alert=True)
            return
        
        # Apply rate limiting for cancel premium button
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            
            from rate_limiter import can_user_use_command
            can_use, seconds_remaining = can_user_use_command(user_id, chat_id, "cancel_premium")
            
            if not can_use:
                # User is rate limited for cancel premium button
                await query.answer(f"⏱️ Please wait {seconds_remaining} seconds before clicking Cancel Premium again.", show_alert=True)
                return
        except ImportError:
            # Rate limiter not available, continue without rate limiting
            logger.warning("Rate limiter not available, continuing without rate limiting")
        except Exception as e:
            # Log any other errors but continue processing
            logger.error(f"Error in cancel premium button rate limiting: {e}")
        
        try:
            from premium_system import handle_premium_cancel
            await handle_premium_cancel(update, context)
        except ImportError:
            await query.answer("Premium system not available", show_alert=True)
        return
    
    # Handle configure callbacks
    elif callback_data.startswith("edit_"):
        # Check if user is in private chat (required for premium operations)
        if update.effective_chat.type != "private":
            await query.answer("💫 Premium operations can only be performed in private chat.", show_alert=True)
            return
        
        # Apply rate limiting for configure callbacks
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            
            from rate_limiter import can_user_use_command
            can_use, seconds_remaining = can_user_use_command(user_id, chat_id, "configure_callback")
            
            if not can_use:
                # User is rate limited for configure callbacks
                await query.answer(f"⏱️ Please wait {seconds_remaining} seconds before clicking configure buttons again.", show_alert=True)
                return
        except ImportError:
            # Rate limiter not available, continue without rate limiting
            logger.warning("Rate limiter not available, continuing without rate limiting")
        except Exception as e:
            # Log any other errors but continue processing
            logger.error(f"Error in configure callback rate limiting: {e}")
        
        logger.info(f"Handling configure callback: {callback_data}")
        try:
            if callback_data == "edit_done":
                from telegram_bot import configure_done_handler
                await configure_done_handler(update, context)
            else:
                from telegram_bot import configure_callback_handler
                await configure_callback_handler(update, context)
        except ImportError:
            await query.answer("Configure functionality not available", show_alert=True)
        except Exception as e:
            logger.error(f"Error handling configure callback: {e}")
            await query.answer("Error processing configure request", show_alert=True)
        return
    
    # Handle help callback
    elif callback_data == "help":
        logger.info("Help callback received in external callback handler")
        help_text = (
            "🎁 *Telegram Gift Price Bot Help*\n\n"
            "*How to use:*\n"
            "Add me to your group, then simply type any gift name (like `tama`, `pepe`, etc.) in the group chat and I'll show you its current price with a beautiful chart! 📊 _This feature only works in groups, not in private chat._\n\n"
            "*Examples:*\n"
            "• `tama` - Shows Tama gift price\n"
            "• `pepe` - Shows Pepe gift price\n"
            "• `heart` - Shows Heart gift price\n"
            "• `diamond` - Shows Diamond gift price\n\n"
            "*Available Commands:*\n"
            "• /start - Welcome message\n"
            "• /help - This help message\n"
            "• /devs - About the developers\n"
            "• /sticker - Browse sticker collections\n\n"
            "*Premium Commands:*\n"
            "• /premium - Get premium subscription\n"
            "• /premium_status - Check premium status\n"
            "• /cancel_premium - Cancel premium setup\n"
            "• /configure - Configure premium settings\n"
            "• /terms - Terms of service\n"
            "• /refund - Refund policy\n\n"
            "*For Groups:*\n"
            "Add me to your group and type any gift name - no admin privileges needed! 🎉\n\n"
            "*Need Support?*\n"
            "Contact @GiftsChart_Support for help or new features! 💬"
        )
        
        try:
            # Send a new message instead of editing the existing one
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=help_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Error sending help message: {e}")
            await query.answer("Error sending help message", show_alert=True)
        return
    
    # Check if this is a delete button callback
    elif callback_data == "delete" or callback_data.startswith("delete_") or callback_data.startswith("inline_delete_"):
        try:
            user_id = update.effective_user.id
            
            # Check if this is an inline message delete request (inline_message_id is present)
            if query.inline_message_id:
                # This is an inline message deletion
                try:
                    await context.bot.edit_message_text(
                        text="This message has been deleted.",
                        inline_message_id=query.inline_message_id
                    )
                    logger.info(f"Inline message {query.inline_message_id} deleted by user {user_id}")
                except Exception as e:
                    logger.error(f"Error deleting inline message: {e}")
                    await query.answer("Error deleting message", show_alert=True)
            
            # Handle inline_delete_ format (used for inline messages)
            elif callback_data.startswith("inline_delete_"):
                try:
                    # Extract inline_message_id from callback data
                    inline_message_id = callback_data[13:]  # Remove "inline_delete_" prefix
                    
                    await context.bot.edit_message_text(
                        text="This message has been deleted.",
                        inline_message_id=inline_message_id
                    )
                    logger.info(f"Inline message {inline_message_id} deleted by user {user_id}")
                except Exception as e:
                    logger.error(f"Error deleting inline message: {e}")
                    await query.answer("Error deleting message", show_alert=True)
            
            # Handle special delete_[inline_message_id] format (legacy format)
            elif callback_data.startswith("delete_") and not any(c.isalpha() for c in callback_data[7:]):
                # This might be an inline message ID
                try:
                    # Try to extract inline_message_id from callback data
                    inline_message_id = callback_data[7:]  # Remove "delete_" prefix
                    
                    # Check if the data after "delete_" is long enough to be an inline message ID
                    # Inline message IDs are usually long strings, while user IDs are shorter
                    if len(inline_message_id) > 10:  # Inline message IDs are typically quite long
                        await context.bot.edit_message_text(
                            text="This message has been deleted.",
                            inline_message_id=inline_message_id
                        )
                        logger.info(f"Inline message {inline_message_id} deleted by user {user_id}")
                    else:
                        # This is likely a user ID, handle as regular message
                        await regular_message_delete(update, context, user_id)
                except Exception as e:
                    logger.error(f"Error handling delete_{inline_message_id}: {e}")
                    # If inline message deletion fails, try regular message deletion as fallback
                    await regular_message_delete(update, context, user_id)
            else:
                # Regular message deletion
                await regular_message_delete(update, context, user_id)
                
        except Exception as e:
            logger.error(f"Error in delete handler: {e}")
            await query.answer("Error processing delete request", show_alert=True)
    
    # Check if this is from an inline query callback for a gift
    elif callback_data.startswith("gift_"):
        # Extract gift name from callback data
        gift_file_name = callback_data[5:]  # Remove "gift_" prefix
        # Convert sanitized callback data back to original gift name
        try:
            from telegram_bot import desanitize_callback_data
            gift_name = desanitize_callback_data(gift_file_name)
        except ImportError:
            # Fallback to simple underscore replacement if function not available
            gift_name = gift_file_name.replace("_", " ")
        
        # Check ownership for gift buttons
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_id = query.message.message_id
        
        try:
            from rate_limiter import can_delete_message, get_message_owner
            logger.info(f"🔒 Checking ownership for gift button '{callback_data}' - User: {user_id}, Chat: {chat_id}, Message: {message_id}")
            
            is_owner = can_delete_message(user_id, chat_id, message_id)
            
            if not is_owner:
                # User is not the owner of this message
                actual_owner = get_message_owner(chat_id, message_id)
                if actual_owner:
                    logger.warning(f"🚫 UNAUTHORIZED GIFT ACCESS: User {user_id} tried to use gift button '{callback_data}' on message {message_id} owned by user {actual_owner}")
                else:
                    logger.warning(f"🚫 UNAUTHORIZED GIFT ACCESS: User {user_id} tried to use gift button '{callback_data}' on message {message_id} (no owner recorded)")
                
                await query.answer("🚫 Only the user who requested this gift can use these buttons.", show_alert=True)
                return
            else:
                logger.info(f"✅ AUTHORIZED: User {user_id} can use gift button '{callback_data}' on message {message_id}")
                
        except ImportError:
            # Rate limiter not available, continue without checking
            logger.warning("Rate limiter not available, continuing without ownership check")
        except Exception as e:
            logger.error(f"Error checking message ownership for gift button: {e}")
            # For safety, deny access if there's an error checking ownership
            await query.answer("🚫 Error checking permissions. Please try again.", show_alert=True)
            return
        
        # Apply rate limiting for specific gift
        try:
            user_id = update.effective_user.id
            
            # For inline queries, effective_chat is None, use a special chat_id
            if query.inline_message_id:
                # For inline mode, use a special chat ID
                chat_id = 0  # Special value for inline mode
            else:
                chat_id = update.effective_chat.id
            
            from rate_limiter import can_user_request
            can_request, seconds_remaining = can_user_request(user_id, chat_id, gift_name)
            
            if not can_request:
                # User is rate limited for this gift
                if seconds_remaining > 0:
                    # Only notify in private chats to avoid spam
                    if not query.inline_message_id:  # Skip for inline mode
                        is_private = update.effective_chat.type == "private"
                        
                        if is_private:
                            await query.message.reply_text(
                                f"⏱️ You can request each gift once per minute. Please wait {seconds_remaining} seconds to request {gift_name} again.",
                                reply_to_message_id=query.message.message_id
                            )
                
                # Still delete the original button message to prevent spam (but not for inline mode)
                if not query.inline_message_id:
                    try:
                        await query.message.delete()
                    except Exception as e:
                        logger.error(f"Error deleting original message: {e}")
                
                return
        except ImportError:
            # Rate limiter not available, continue without rate limiting
            logger.warning("Rate limiter not available, continuing without rate limiting")
        except Exception as e:
            # Log any other errors but continue processing
            logger.error(f"Error in rate limiting: {e}")
        
        try:
            # Handle messaging differently depending on whether this is from inline query or not
            if query.inline_message_id:
                # This is from an inline query result
                logger.info(f"Processing inline query callback for {gift_name}")
                
                # First update the inline message to show loading
                try:
                    await context.bot.edit_message_text(
                        text=f"📊 Generating price card for {gift_name}...",
                        inline_message_id=query.inline_message_id
                    )
                except Exception as e:
                    logger.error(f"Error updating inline message: {e}")
                
                # Generate a fresh gift card with timestamp to ensure it's new
                from telegram_bot import generate_timestamped_card
                card_path = generate_timestamped_card(gift_file_name)
                
                if not card_path:
                    # If we failed to generate the card, update the message
                    await context.bot.edit_message_text(
                        text=f"❌ Sorry, couldn't generate price card for {gift_name}.",
                        inline_message_id=query.inline_message_id
                    )
                    return
                
                # Use CDN URL instead of Catbox
                CDN_BASE_URL = "https://test.asadffastest.store/api"
                from telegram_bot import normalize_gift_filename
                gift_file_name = normalize_gift_filename(gift_name)
                image_url = f"{CDN_BASE_URL}/new_gift_cards/{gift_file_name}_card.png"
                
                # Get the gift price data
                try:
                    import new_card_design
                    gift_data = new_card_design.fetch_gift_data(gift_name)
                    if gift_data:
                        price_usd = float(gift_data.get("priceUsd", 0))
                        price_ton = float(gift_data.get("priceTon", 0))
                        change_pct = float(gift_data.get("changePercentage", 0))
                        
                        # Format the change percentage with sign
                        change_sign = "+" if change_pct >= 0 else ""
                        change_formatted = f"{change_sign}{change_pct:.2f}"
                        
                        caption = f"💎 <b>{gift_name}</b> 💎\n\n{price_ton:.1f} TON = ${price_usd:,.0f} USD ({change_formatted}%)"
                    else:
                        caption = f"💎 <b>{gift_name}</b> 💎"
                except Exception as e:
                    logger.error(f"Error formatting price data: {e}")
                    caption = f"💎 <b>{gift_name}</b> 💎"
                
                # Create message with image preview
                # The invisible link trick with a zero-width space after href=
                message_text = f"<a href='{image_url}'> </a>{caption}"
                
                # Send the message with image preview
                try:
                    result = await context.bot.edit_message_text(
                        text=message_text,
                        inline_message_id=query.inline_message_id,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=False,  # Important: enable preview
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("💰 Buy/Sell Gifts", callback_data=f"gift_markets_{gift_file_name}")],
                            [InlineKeyboardButton("🗑️ Delete", callback_data=f"inline_delete_{query.inline_message_id}")]
                        ])
                    )
                    logger.info(f"Successfully sent gift card for {gift_name} with image preview")
                except Exception as e:
                    logger.error(f"Error sending gift card: {e}")
                    # If failed, try to send just text
                    try:
                        await context.bot.edit_message_text(
                            text=caption,
                            inline_message_id=query.inline_message_id,
                            parse_mode=ParseMode.HTML,
                                                    reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("💰 Buy/Sell Gifts", callback_data=f"gift_markets_{gift_file_name}")],
                            [InlineKeyboardButton("🗑️ Delete", callback_data=f"inline_delete_{query.inline_message_id}")]
                        ])
                        )
                    except Exception as nested_error:
                        logger.error(f"Error in fallback message: {nested_error}")
            else:
                # This is from a regular message
                logger.info(f"Processing regular message callback for {gift_name}")
                
                # Send a loading message
                loading_message = await query.message.reply_text(f"📊 Generating price card for {gift_name}...")
                
                # Generate the gift card
                from telegram_bot import generate_gift_price_card
                card_path = await generate_gift_price_card(gift_file_name)
                
                if not card_path:
                    # If we failed to generate the card, update the message
                    await loading_message.edit_text(f"❌ Sorry, couldn't generate price card for {gift_name}.")
                    return
                
                # Check if this is a special group with custom buttons
                # Get the current chat ID
                chat_id = update.effective_chat.id
                
                # Check if this is a premium group and use custom links
                from premium_system import premium_system
                buy_sell_link = DEFAULT_BUY_SELL_LINK
                portal_link = None
                if premium_system.is_group_premium(chat_id):
                    links = premium_system.get_premium_links(chat_id)
                    if links:
                        buy_sell_link = links.get('mrkt_link') or buy_sell_link
                        portal_link = links.get('portal_link') or portal_link
                # Create three buttons for premium or special groups
                keyboard = [
                    [InlineKeyboardButton("💰 Buy/Sell Gifts", url=buy_sell_link)],
                ]
                if portal_link:
                    keyboard[0].append(InlineKeyboardButton("🌐 Portal", url=portal_link))
                keyboard.append([InlineKeyboardButton("🗑️ Delete", callback_data="delete")])
                
                # Create caption based on premium status
                if premium_system.is_group_premium(chat_id):
                    # Premium groups: show gift name + pro tip
                    caption = f"{gift_name}\n\nJoin @The01Studio\nTry @CollectibleKITbot"
                else:
                    # Non-premium groups: show gift name + promotional text + sticker promotion
                    caption = f"{gift_name}\n\nJoin @The01Studio\nTry @CollectibleKITbot"
                
                # Send the photo with the appropriate keyboard
                sent_message = await query.message.reply_photo(
                    photo=open(card_path, 'rb'),
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                # Register message ownership in database for delete permission
                from rate_limiter import register_message
                register_message(user_id, chat_id, sent_message.message_id)
                
                # Delete the loading message
                await loading_message.delete()
                
                # Delete the original message with the button
                try:
                    await query.message.delete()
                except Exception as e:
                    logger.error(f"Error deleting original message: {e}")
                
        except Exception as e:
            logger.error(f"Error processing gift callback: {e}")
            # Try to notify the user
            try:
                if query.inline_message_id:
                    await context.bot.edit_message_text(
                        text=f"❌ Error generating price card: {e}",
                        inline_message_id=query.inline_message_id
                    )
                else:
                    await query.message.reply_text(f"❌ Error generating price card: {e}")
            except:
                pass
    
    # Handle gift markets button (Buy/Sell Gifts)
    elif callback_data.startswith("gift_markets_"):
        # Extract gift name from callback data
        gift_file_name = callback_data[13:]  # Remove "gift_markets_" prefix
        # Convert sanitized callback data back to original gift name
        try:
            from telegram_bot import desanitize_callback_data
            gift_name = desanitize_callback_data(gift_file_name)
        except ImportError:
            # Fallback to simple underscore replacement if function not available
            gift_name = gift_file_name.replace("_", " ")
        
        # Check ownership for gift market buttons
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_id = query.message.message_id
        
        try:
            from rate_limiter import can_delete_message, get_message_owner
            logger.info(f"🔒 Checking ownership for gift markets button '{callback_data}' - User: {user_id}, Chat: {chat_id}, Message: {message_id}")
            
            is_owner = can_delete_message(user_id, chat_id, message_id)
            
            if not is_owner:
                # User is not the owner of this message
                actual_owner = get_message_owner(chat_id, message_id)
                if actual_owner:
                    logger.warning(f"🚫 UNAUTHORIZED GIFT MARKETS ACCESS: User {user_id} tried to use gift markets button '{callback_data}' on message {message_id} owned by user {actual_owner}")
                else:
                    logger.warning(f"🚫 UNAUTHORIZED GIFT MARKETS ACCESS: User {user_id} tried to use gift markets button '{callback_data}' on message {message_id} (no owner recorded)")
                
                await query.answer("🚫 Only the user who requested this gift can use these buttons.", show_alert=True)
                return
            else:
                logger.info(f"✅ AUTHORIZED: User {user_id} can use gift markets button '{callback_data}' on message {message_id}")
                
        except ImportError:
            # Rate limiter not available, continue without checking
            logger.warning("Rate limiter not available, continuing without ownership check")
        except Exception as e:
            logger.error(f"Error checking message ownership for gift markets button: {e}")
            # For safety, deny access if there's an error checking ownership
            await query.answer("🚫 Error checking permissions. Please try again.", show_alert=True)
            return
        
        # Check if this is a special group with custom buttons
        chat_id = update.effective_chat.id
        
        # Check if this is a premium group and use custom links
        from premium_system import premium_system
        buy_sell_link = DEFAULT_BUY_SELL_LINK
        portal_link = None
        
        try:
            if premium_system.is_group_premium(chat_id):
                links = premium_system.get_premium_links(chat_id)
                if links and links.get('buy_sell_link'):
                    buy_sell_link = links.get('buy_sell_link')
                if links and links.get('portal_link'):
                    portal_link = links.get('portal_link')
        except Exception as e:
            logger.error(f"Error checking premium status: {e}")
        
        # Check if this is a special group
        if chat_id in SPECIAL_GROUPS:
            special_config = SPECIAL_GROUPS[chat_id]
            if special_config.get("buy_sell_link"):
                buy_sell_link = special_config.get("buy_sell_link")
            if special_config.get("portal_link"):
                portal_link = special_config.get("portal_link")
        
        # Create keyboard with marketplace options
        keyboard = []
        
        if portal_link:
            # If we have both links, show them in a row
            keyboard.append([
                InlineKeyboardButton("🛒 Buy/Sell", url=buy_sell_link),
                InlineKeyboardButton("🌐 Portal", url=portal_link)
            ])
        else:
            # Only show Buy/Sell button
            keyboard.append([InlineKeyboardButton("🛒 Buy/Sell", url=buy_sell_link)])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("« Back", callback_data=f"gift_{gift_file_name}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Update the message with the marketplace options
        try:
            await query.edit_message_reply_markup(reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error updating message with marketplace options: {e}")
            await query.answer("❌ Error updating message", show_alert=True)
            
    # Other callback types like category_, page_, etc. would be handled here
    elif callback_data.startswith("category_"):
        # Check ownership for category buttons
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_id = query.message.message_id
        
        try:
            from rate_limiter import can_delete_message, get_message_owner
            logger.info(f"🔒 Checking ownership for category button '{callback_data}' - User: {user_id}, Chat: {chat_id}, Message: {message_id}")
            
            is_owner = can_delete_message(user_id, chat_id, message_id)
            
            if not is_owner:
                # User is not the owner of this message
                actual_owner = get_message_owner(chat_id, message_id)
                if actual_owner:
                    logger.warning(f"🚫 UNAUTHORIZED CATEGORY ACCESS: User {user_id} tried to use category button '{callback_data}' on message {message_id} owned by user {actual_owner}")
                else:
                    logger.warning(f"🚫 UNAUTHORIZED CATEGORY ACCESS: User {user_id} tried to use category button '{callback_data}' on message {message_id} (no owner recorded)")
                
                await query.answer("🚫 Only the user who requested this can use these buttons.", show_alert=True)
                return
            else:
                logger.info(f"✅ AUTHORIZED: User {user_id} can use category button '{callback_data}' on message {message_id}")
                
        except ImportError:
            # Rate limiter not available, continue without checking
            logger.warning("Rate limiter not available, continuing without ownership check")
        except Exception as e:
            logger.error(f"Error checking message ownership for category button: {e}")
            # For safety, deny access if there's an error checking ownership
            await query.answer("🚫 Error checking permissions. Please try again.", show_alert=True)
            return
        
        category = callback_data[9:]  # Remove "category_" prefix
        from telegram_bot import get_gift_keyboard
        reply_markup = get_gift_keyboard(category)
        
        # Instead of editing the message, send a new message and delete the old one
        await query.message.reply_text(
            f"Here are gifts in the {category} category:", 
            reply_markup=reply_markup
        )
        
        # Delete the original message with the button
        try:
            await query.message.delete()
        except Exception as e:
            logger.error(f"Error deleting original message: {e}")
    
    elif callback_data.startswith("page_"):
        # Check ownership for page buttons
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_id = query.message.message_id
        
        try:
            from rate_limiter import can_delete_message, get_message_owner
            logger.info(f"🔒 Checking ownership for page button '{callback_data}' - User: {user_id}, Chat: {chat_id}, Message: {message_id}")
            
            is_owner = can_delete_message(user_id, chat_id, message_id)
            
            if not is_owner:
                # User is not the owner of this message
                actual_owner = get_message_owner(chat_id, message_id)
                if actual_owner:
                    logger.warning(f"🚫 UNAUTHORIZED PAGE ACCESS: User {user_id} tried to use page button '{callback_data}' on message {message_id} owned by user {actual_owner}")
                else:
                    logger.warning(f"🚫 UNAUTHORIZED PAGE ACCESS: User {user_id} tried to use page button '{callback_data}' on message {message_id} (no owner recorded)")
                
                await query.answer("🚫 Only the user who requested this can use these buttons.", show_alert=True)
                return
            else:
                logger.info(f"✅ AUTHORIZED: User {user_id} can use page button '{callback_data}' on message {message_id}")
                
        except ImportError:
            # Rate limiter not available, continue without checking
            logger.warning("Rate limiter not available, continuing without ownership check")
        except Exception as e:
            logger.error(f"Error checking message ownership for page button: {e}")
            # For safety, deny access if there's an error checking ownership
            await query.answer("🚫 Error checking permissions. Please try again.", show_alert=True)
            return
        
        # Handle pagination for gift browsing
        parts = callback_data.split("_")
        page = int(parts[1])
        category = parts[2] if len(parts) > 2 else None
        
        from telegram_bot import get_gift_keyboard
        reply_markup = get_gift_keyboard(category, page)
        
        # Update the text based on whether we're showing a category or all gifts
        message_text = ""
        if category and category != "None":
            message_text = f"Here are gifts in the {category} category (page {page+1}):"
        else:
            message_text = f"Browsing all gifts (page {page+1}):"
            
        # Instead of editing the message, send a new message and delete the old one
        await query.message.reply_text(message_text, reply_markup=reply_markup)
        
        # Delete the original message with the button
        try:
            await query.message.delete()
        except Exception as e:
            logger.error(f"Error deleting original message: {e}")
    
    elif callback_data == "back_to_categories":
        # Check ownership for back to categories button
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_id = query.message.message_id
        
        try:
            from rate_limiter import can_delete_message, get_message_owner
            logger.info(f"🔒 Checking ownership for back_to_categories button - User: {user_id}, Chat: {chat_id}, Message: {message_id}")
            
            is_owner = can_delete_message(user_id, chat_id, message_id)
            
            if not is_owner:
                # User is not the owner of this message
                actual_owner = get_message_owner(chat_id, message_id)
                if actual_owner:
                    logger.warning(f"🚫 UNAUTHORIZED BACK ACCESS: User {user_id} tried to use back_to_categories button on message {message_id} owned by user {actual_owner}")
                else:
                    logger.warning(f"🚫 UNAUTHORIZED BACK ACCESS: User {user_id} tried to use back_to_categories button on message {message_id} (no owner recorded)")
                
                await query.answer("🚫 Only the user who requested this can use these buttons.", show_alert=True)
                return
            else:
                logger.info(f"✅ AUTHORIZED: User {user_id} can use back_to_categories button on message {message_id}")
                
        except ImportError:
            # Rate limiter not available, continue without checking
            logger.warning("Rate limiter not available, continuing without ownership check")
        except Exception as e:
            logger.error(f"Error checking message ownership for back_to_categories button: {e}")
            # For safety, deny access if there's an error checking ownership
            await query.answer("🚫 Error checking permissions. Please try again.", show_alert=True)
            return
        
        from telegram_bot import get_category_keyboard
        reply_markup = get_category_keyboard()
        
        # Instead of editing the message, send a new message and delete the old one
        await query.message.reply_text("Choose a gift category to browse:", reply_markup=reply_markup)
        
        # Delete the original message with the button
        try:
            await query.message.delete()
        except Exception as e:
            logger.error(f"Error deleting original message: {e}")
    
    elif callback_data == "random_gift":
        # Check ownership for random gift button
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_id = query.message.message_id
        
        try:
            from rate_limiter import can_delete_message, get_message_owner
            logger.info(f"🔒 Checking ownership for random_gift button - User: {user_id}, Chat: {chat_id}, Message: {message_id}")
            
            is_owner = can_delete_message(user_id, chat_id, message_id)
            
            if not is_owner:
                # User is not the owner of this message
                actual_owner = get_message_owner(chat_id, message_id)
                if actual_owner:
                    logger.warning(f"🚫 UNAUTHORIZED RANDOM ACCESS: User {user_id} tried to use random_gift button on message {message_id} owned by user {actual_owner}")
                else:
                    logger.warning(f"🚫 UNAUTHORIZED RANDOM ACCESS: User {user_id} tried to use random_gift button on message {message_id} (no owner recorded)")
                
                await query.answer("🚫 Only the user who requested this can use these buttons.", show_alert=True)
                return
            else:
                logger.info(f"✅ AUTHORIZED: User {user_id} can use random_gift button on message {message_id}")
                
        except ImportError:
            # Rate limiter not available, continue without checking
            logger.warning("Rate limiter not available, continuing without ownership check")
        except Exception as e:
            logger.error(f"Error checking message ownership for random_gift button: {e}")
            # For safety, deny access if there's an error checking ownership
            await query.answer("🚫 Error checking permissions. Please try again.", show_alert=True)
            return
        
        # Show a random gift
        from telegram_bot import random
        from telegram_bot import names
        from telegram_bot import send_gift_card
        
        # Choose random gift name
        gift_name = random.choice(names)
        
        # First send a loading message
        loading_message = await query.message.reply_text(f"🎲 Generating random gift: {gift_name}...")
        
        # Generate and send the gift card
        await send_gift_card(update, context, gift_name)
        
        # Delete the loading message
        await loading_message.delete()
        
        # Delete the original message with the button
        try:
            await query.message.delete()
        except Exception as e:
            logger.error(f"Error deleting original message: {e}")

    # Handle Buy/Sell Gifts submenu
    elif callback_data == "show_markets":
        # Check ownership for show_markets button
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_id = query.message.message_id
        
        try:
            from rate_limiter import can_delete_message, get_message_owner
            logger.info(f"🔒 Checking ownership for show_markets button - User: {user_id}, Chat: {chat_id}, Message: {message_id}")
            
            is_owner = can_delete_message(user_id, chat_id, message_id)
            
            if not is_owner:
                # User is not the owner of this message
                actual_owner = get_message_owner(chat_id, message_id)
                if actual_owner:
                    logger.warning(f"🚫 UNAUTHORIZED MARKETS ACCESS: User {user_id} tried to use show_markets button on message {message_id} owned by user {actual_owner}")
                else:
                    logger.warning(f"🚫 UNAUTHORIZED MARKETS ACCESS: User {user_id} tried to use show_markets button on message {message_id} (no owner recorded)")
                
                await query.answer("🚫 Only the user who requested this can use these buttons.", show_alert=True)
                return
            else:
                logger.info(f"✅ AUTHORIZED: User {user_id} can use show_markets button on message {message_id}")
                
        except ImportError:
            # Rate limiter not available, continue without checking
            logger.warning("Rate limiter not available, continuing without ownership check")
        except Exception as e:
            logger.error(f"Error checking message ownership for show_markets button: {e}")
            # For safety, deny access if there's an error checking ownership
            await query.answer("🚫 Error checking permissions. Please try again.", show_alert=True)
            return
        
        from telegram_bot import get_markets_submenu_keyboard
        from premium_system import premium_system
        chat_id = update.effective_chat.id
        links = premium_system.get_premium_links(chat_id)
        mrkt_link = links.get('mrkt_link') if links else DEFAULT_MRKT_LINK
        tonnel_link = links.get('tonnel_link') if links else DEFAULT_TONNEL_LINK
        portal_link = links.get('portal_link') if links else DEFAULT_PORTAL_LINK
        palace_link = links.get('palace_link') if links else DEFAULT_PALACE_LINK
        await query.edit_message_reply_markup(reply_markup=get_markets_submenu_keyboard(mrkt_link, tonnel_link, portal_link, palace_link))
        return
    elif callback_data == "back_to_main":
        # Check ownership for back_to_main button
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_id = query.message.message_id
        
        try:
            from rate_limiter import can_delete_message, get_message_owner
            logger.info(f"🔒 Checking ownership for back_to_main button - User: {user_id}, Chat: {chat_id}, Message: {message_id}")
            
            is_owner = can_delete_message(user_id, chat_id, message_id)
            
            if not is_owner:
                # User is not the owner of this message
                actual_owner = get_message_owner(chat_id, message_id)
                if actual_owner:
                    logger.warning(f"🚫 UNAUTHORIZED BACK MAIN ACCESS: User {user_id} tried to use back_to_main button on message {message_id} owned by user {actual_owner}")
                else:
                    logger.warning(f"🚫 UNAUTHORIZED BACK MAIN ACCESS: User {user_id} tried to use back_to_main button on message {message_id} (no owner recorded)")
                
                await query.answer("🚫 Only the user who requested this can use these buttons.", show_alert=True)
                return
            else:
                logger.info(f"✅ AUTHORIZED: User {user_id} can use back_to_main button on message {message_id}")
                
        except ImportError:
            # Rate limiter not available, continue without checking
            logger.warning("Rate limiter not available, continuing without ownership check")
        except Exception as e:
            logger.error(f"Error checking message ownership for back_to_main button: {e}")
            # For safety, deny access if there's an error checking ownership
            await query.answer("🚫 Error checking permissions. Please try again.", show_alert=True)
            return
        
        from telegram_bot import get_gift_price_card_keyboard
        from premium_system import premium_system
        chat_id = update.effective_chat.id
        
        # Get the user who owns this message
        from rate_limiter import get_message_owner
        try:
            message_owner_id = get_message_owner(chat_id, query.message.message_id)
        except:
            # Fallback to current user if we can't determine the owner
            message_owner_id = update.effective_user.id
        
        links = premium_system.get_premium_links(chat_id)
        mrkt_link = links.get('mrkt_link') if links else DEFAULT_MRKT_LINK
        tonnel_link = links.get('tonnel_link') if links else DEFAULT_TONNEL_LINK
        portal_link = links.get('portal_link') if links else DEFAULT_PORTAL_LINK
        palace_link = links.get('palace_link') if links else DEFAULT_PALACE_LINK
        is_premium = premium_system.is_group_premium(chat_id)
        await query.edit_message_reply_markup(reply_markup=get_gift_price_card_keyboard(is_premium, mrkt_link, tonnel_link, portal_link, palace_link, message_owner_id))
        return

async def regular_message_delete(update, context, user_id):
    """Handle regular (non-inline) message deletion"""
    query = update.callback_query
    message_id = query.message.message_id
    chat_id = update.effective_chat.id
    
    try:
        # Check if this user can delete this message
        from rate_limiter import can_delete_message, get_linked_messages
        can_delete = can_delete_message(user_id, chat_id, message_id)
        logger.info(f"User {user_id} attempting to delete message {message_id}, allowed: {can_delete}")
        
        if can_delete:
            # Get any linked messages (like promotional messages) that should be deleted too
            linked_messages = get_linked_messages(chat_id, message_id)
            
            # Delete linked messages first
            for linked_message_id in linked_messages:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=linked_message_id)
                    logger.info(f"Deleted linked message {linked_message_id} for original {message_id}")
                except Exception as linked_error:
                    logger.error(f"Error deleting linked message {linked_message_id}: {linked_error}")
            
            # Delete the main message
            await query.message.delete()
            logger.info(f"Message {message_id} deleted successfully by user {user_id}")
        else:
            # Notify that only the requester can delete the message
            await query.answer("Only the user who requested this card can delete it", show_alert=True)
            logger.warning(f"Delete attempt by unauthorized user {user_id} for message {message_id}")
    except Exception as del_error:
        # If there's an error checking permissions, try to delete anyway
        logger.error(f"Error checking message permissions: {del_error}")
        try:
            await query.message.delete()
            logger.info(f"Message {message_id} deleted after permission check error")
        except Exception as final_error:
            logger.error(f"Final error deleting message: {final_error}")
            await query.answer("Error deleting message", show_alert=True) 