#!/usr/bin/env python3
"""
Premium System for Telegram Gift & Sticker Bot

This module handles premium subscriptions with Telegram Stars payments,
custom referral links for groups, and premium user management.
"""

import os
import sqlite3
import logging
import time
import json
import uuid
import re
from datetime import datetime, timedelta
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    LabeledPrice, 
    ReplyKeyboardRemove, 
    ReplyKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestChat
)
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import TelegramError, BadRequest
import asyncio
import threading

# Configure logging
logger = logging.getLogger(__name__)

# Database file for premium data
PREMIUM_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sqlite_data", "premium_system.db")

# Premium subscription price (in Telegram Stars)
PREMIUM_PRICE_STARS = 99  # Number of Stars to charge (99 Stars = 9900 units)

# Define link validation patterns
def is_valid_link(link, kind, debug=False):
    """Validate referral links based on their type with flexible patterns and detailed debug info."""
    
    # Define expected bot names for debug messages
    expected_bots = {
        'mrkt': 'mrkt',
        'palace': 'palacenftbot', 
        'tonnel': 'tonnel_network_bot',
        'portal': 'portals'
    }
    
    # Basic URL structure validation
    if not link.startswith('https://t.me/'):
        if debug:
            return False, f"❌ Link must start with 'https://t.me/' (found: {link[:20]}...)"
        return False
    
    # Extract bot name from URL
    try:
        url_parts = link.replace('https://t.me/', '').split('/')
        bot_name = url_parts[0].split('?')[0]  # Get bot name before any parameters
    except:
        if debug:
            return False, f"❌ Invalid URL format. Expected: https://t.me/BOTNAME?startapp=..."
        return False
    
    # Check if it's the correct bot (case insensitive)
    expected_bot = expected_bots.get(kind)
    if not expected_bot or bot_name.lower() != expected_bot.lower():
        if debug:
            return False, f"❌ Wrong bot name! Expected: @{expected_bot}, Found: @{bot_name}"
        return False
    
    # Check for startapp parameter
    if 'startapp=' not in link:
        if debug:
            return False, f"❌ Missing 'startapp' parameter! Add ?startapp=YOUR_REFERRAL_CODE"
        return False
    
    # Extract startapp value for special validation
    try:
        startapp_part = link.split('startapp=')[1].split('&')[0]  # Get value before any & parameters
    except:
        if debug:
            return False, f"❌ Invalid 'startapp' parameter format"
        return False
    
    # Special validation for Tonnel (must contain 'ref_')
    if kind == 'tonnel' and 'ref_' not in startapp_part:
        if debug:
            return False, f"❌ Tonnel links must contain 'ref_' in startapp value. Found: {startapp_part}"
        return False
    
    # Check if startapp value is not empty
    if not startapp_part.strip():
        if debug:
            return False, f"❌ 'startapp' parameter is empty. Add your referral code after startapp="
        return False
    
    # If we get here, the link is valid
    if debug:
        return True, f"✅ Valid {kind.upper()} link! Bot: @{bot_name}, startapp: {startapp_part}"
    return True

def validate_link_with_debug(link, kind):
    """Wrapper function that returns both validation result and debug message."""
    result = is_valid_link(link, kind, debug=True)
    if isinstance(result, tuple):
        return result
    else:
        # Backward compatibility for non-debug calls
        return result, "Valid" if result else "Invalid"

def get_link_examples(kind):
    """Get example links for each market type."""
    examples = {
        'mrkt': [
            'https://t.me/mrkt/app?startapp=YOUR_CODE',
            'https://t.me/mrkt?startapp=YOUR_CODE',
            'https://t.me/mrkt/market?startapp=YOUR_CODE'
        ],
        'palace': [
            'https://t.me/palacenftbot/?startapp=YOUR_CODE',
            'https://t.me/palacenftbot?startapp=YOUR_CODE',
            'https://t.me/palacenftbot/app?startapp=YOUR_CODE'
        ],
        'tonnel': [
            'https://t.me/tonnel_network_bot/gifts?startapp=ref_YOUR_CODE',
            'https://t.me/tonnel_network_bot?startapp=ref_YOUR_CODE',
            'https://t.me/tonnel_network_bot/app?startapp=ref_YOUR_CODE'
        ],
        'portal': [
            'https://t.me/portals/market?startapp=YOUR_CODE',
            'https://t.me/portals?startapp=YOUR_CODE',
            'https://t.me/portals/app?startapp=YOUR_CODE'
        ]
    }
    return examples.get(kind, [])

def get_detailed_help_message(kind, invalid_link=None):
    """Generate a comprehensive help message for link validation."""
    expected_bot = {
        'mrkt': 'mrkt',
        'palace': 'palacenftbot',
        'tonnel': 'tonnel_network_bot', 
        'portal': 'portals'
    }.get(kind, 'unknown')
    
    help_msg = f"📋 {kind.upper()} Link Format Help:\n"
    help_msg += f"🤖 Expected Bot: @{expected_bot}\n"
    
    if kind == 'tonnel':
        help_msg += f"🔑 Special Requirement: startapp must contain 'ref_'\n"
        help_msg += f"   Example: startapp=ref_YOUR_REFERRAL_CODE\n"
    else:
        help_msg += f"🔑 Required Parameter: ?startapp=YOUR_REFERRAL_CODE\n"
    
    help_msg += f"✅ Valid Examples:\n"
    for example in get_link_examples(kind):
        help_msg += f"   • {example}\n"
    
    if invalid_link:
        help_msg += f"\n❌ Your Link: {invalid_link}\n"
        is_valid, debug_msg = validate_link_with_debug(invalid_link, kind)
        help_msg += f"💡 Issue: {debug_msg}\n"
    
    return help_msg

class PremiumSystem:
    def __init__(self):
        self.ensure_database()
    
    def ensure_database(self):
        """Ensure premium database exists with required tables."""
        conn = sqlite3.connect(PREMIUM_DB_FILE)
        cursor = conn.cursor()
        
        # Create premium subscriptions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS premium_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            payment_id TEXT NOT NULL,
            telegram_payment_charge_id TEXT NOT NULL,
            stars_amount INTEGER NOT NULL,
            mrkt_link TEXT,
            palace_link TEXT,
            tonnel_link TEXT,
            portal_link TEXT,
            created_at INTEGER NOT NULL,
            expires_at INTEGER,
            is_active BOOLEAN DEFAULT 1,
            UNIQUE(owner_id, group_id)
        )
        ''')
        
        # Create payment history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            payment_id TEXT NOT NULL,
            stars_amount INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        ''')
        
        # Create refund tracking table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS refunds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_id INTEGER NOT NULL,
            owner_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            payment_id TEXT NOT NULL,
            stars_amount INTEGER NOT NULL,
            refund_reason TEXT,
            refunded_at INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            processed_by TEXT,
            FOREIGN KEY (subscription_id) REFERENCES premium_subscriptions (id)
        )
        ''')
        
        # Create refunded groups tracking table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS refunded_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER UNIQUE NOT NULL,
            owner_id INTEGER NOT NULL,
            refunded_at INTEGER NOT NULL,
            reason TEXT
        )
        ''')
        
        # Create pending payments table for payment flow
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            payment_id TEXT NOT NULL,
            stars_amount INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Premium database initialized")
    
    def create_payment_request(self, owner_id: int) -> dict:
        """Create a new payment request for premium subscription."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            # Generate unique payment ID
            payment_id = f"premium_{owner_id}_{int(time.time())}"
            
            # Set expiration time (30 minutes from now)
            expires_at = int(time.time()) + (30 * 60)
            
            # Store pending payment
            cursor.execute('''
            INSERT INTO pending_payments (owner_id, payment_id, stars_amount, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (owner_id, payment_id, PREMIUM_PRICE_STARS, int(time.time()), expires_at))
            
            conn.commit()
            conn.close()
            
            return {
                "payment_id": payment_id,
                "stars_amount": PREMIUM_PRICE_STARS,
                "expires_at": expires_at
            }
        except Exception as e:
            logger.error(f"Error creating payment request: {e}")
            return None
    
    def verify_payment_exists(self, payment_id: str) -> bool:
        """Check if a payment request exists and is not expired."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT COUNT(*) FROM pending_payments 
            WHERE payment_id = ? AND expires_at > ?
            ''', (payment_id, int(time.time())))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Error verifying payment exists: {e}")
            return False
    
    def mark_payment_completed(self, payment_id: str) -> bool:
        """Mark a payment as completed and move to payment history."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            # Get payment details
            cursor.execute('''
            SELECT owner_id, stars_amount FROM pending_payments 
            WHERE payment_id = ?
            ''', (payment_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False
            
            owner_id, stars_amount = result
            
            # Move to payment history
            cursor.execute('''
            INSERT INTO payment_history (owner_id, payment_id, stars_amount, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (owner_id, payment_id, stars_amount, "completed", int(time.time())))
            
            # Remove from pending payments
            cursor.execute('DELETE FROM pending_payments WHERE payment_id = ?', (payment_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error marking payment completed: {e}")
            return False
    
    def add_premium_subscription(self, owner_id: int, group_id: int, payment_id: str, 
                                telegram_payment_charge_id: str,
                                mrkt_link: str = None, palace_link: str = None, 
                                tonnel_link: str = None, portal_link: str = None) -> bool:
        """Add a new premium subscription for a group."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            # Set expiration (30 days from now)
            expires_at = int(time.time()) + (30 * 24 * 60 * 60)
            
            cursor.execute('''
            INSERT OR REPLACE INTO premium_subscriptions 
            (owner_id, group_id, payment_id, telegram_payment_charge_id, stars_amount, mrkt_link, palace_link, tonnel_link, portal_link, created_at, expires_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (owner_id, group_id, payment_id, telegram_payment_charge_id, PREMIUM_PRICE_STARS, mrkt_link, palace_link, tonnel_link, portal_link, int(time.time()), expires_at))
            
            conn.commit()
            conn.close()
            logger.info(f"Premium subscription added for owner {owner_id}, group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding premium subscription: {e}")
            return False
    
    def update_premium_links(self, group_id: int, mrkt_link: str = None, palace_link: str = None, 
                           tonnel_link: str = None, portal_link: str = None) -> bool:
        """Update referral links for an existing premium subscription."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            # Build the update query dynamically based on which links are provided
            update_parts = []
            params = []
            
            if mrkt_link is not None:
                update_parts.append("mrkt_link = ?")
                params.append(mrkt_link)
            if palace_link is not None:
                update_parts.append("palace_link = ?")
                params.append(palace_link)
            if tonnel_link is not None:
                update_parts.append("tonnel_link = ?")
                params.append(tonnel_link)
            if portal_link is not None:
                update_parts.append("portal_link = ?")
                params.append(portal_link)
            
            if not update_parts:
                conn.close()
                return False
            
            # Add group_id to params
            params.append(group_id)
            
            query = f'''
            UPDATE premium_subscriptions 
            SET {', '.join(update_parts)}
            WHERE group_id = ? AND is_active = 1 AND expires_at > ?
            '''
            params.append(int(time.time()))
            
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            
            logger.info(f"Premium links updated for group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating premium links: {e}")
            return False
    
    def get_premium_links(self, group_id: int) -> dict:
        """Get custom referral links for a premium group."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT mrkt_link, palace_link, tonnel_link, portal_link, is_active, expires_at
            FROM premium_subscriptions 
            WHERE group_id = ? AND is_active = 1 AND expires_at > ?
            ''', (group_id, int(time.time())))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                mrkt_link, palace_link, tonnel_link, portal_link, is_active, expires_at = result
                return {
                    "mrkt_link": mrkt_link,
                    "palace_link": palace_link,
                    "tonnel_link": tonnel_link,
                    "portal_link": portal_link,
                    "is_active": bool(is_active),
                    "expires_at": expires_at
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting premium links: {e}")
            return None
    
    def is_group_premium(self, group_id: int) -> bool:
        """Check if a group has an active premium subscription."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT COUNT(*) FROM premium_subscriptions 
            WHERE group_id = ? AND is_active = 1 AND expires_at > ?
            ''', (group_id, int(time.time())))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking premium status: {e}")
            return False
    
    def get_user_premium_groups(self, owner_id: int) -> list:
        """Get all premium groups owned by a user."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT group_id, mrkt_link, palace_link, tonnel_link, portal_link, created_at, expires_at
            FROM premium_subscriptions 
            WHERE owner_id = ? AND is_active = 1 AND expires_at > ?
            ''', (owner_id, int(time.time())))
            
            results = cursor.fetchall()
            conn.close()
            
            groups = []
            for result in results:
                group_id, mrkt_link, palace_link, tonnel_link, portal_link, created_at, expires_at = result
                groups.append({
                    "group_id": group_id,
                    "mrkt_link": mrkt_link,
                    "palace_link": palace_link,
                    "tonnel_link": tonnel_link,
                    "portal_link": portal_link,
                    "created_at": created_at,
                    "expires_at": expires_at
                })
            
            return groups
            
        except Exception as e:
            logger.error(f"Error getting user premium groups: {e}")
            return []
    
    def is_group_refunded(self, group_id: int) -> bool:
        """Check if a group has been refunded before."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT COUNT(*) FROM refunded_groups WHERE group_id = ?
            ''', (group_id,))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking if group is refunded: {e}")
            return False
    
    def can_request_refund(self, owner_id: int, group_id: int) -> dict:
        """Check if a user can request a refund for a group."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            # Check if group has active premium subscription
            cursor.execute('''
            SELECT id, created_at, stars_amount, payment_id, telegram_payment_charge_id 
            FROM premium_subscriptions 
            WHERE owner_id = ? AND group_id = ? AND is_active = 1
            ''', (owner_id, group_id))
            
            subscription = cursor.fetchone()
            if not subscription:
                conn.close()
                return {"can_refund": False, "reason": "No active premium subscription found"}
            
            subscription_id, created_at, stars_amount, payment_id, telegram_payment_charge_id = subscription
            
            # Check if group has been refunded before
            if self.is_group_refunded(group_id):
                conn.close()
                return {"can_refund": False, "reason": "This group has already been refunded once"}
            
            # Check if within 24-hour Telegram API limit (required by Telegram)
            current_time = int(time.time())
            telegram_refund_deadline = created_at + (24 * 60 * 60)  # 24 hours in seconds
            
            if current_time > telegram_refund_deadline:
                conn.close()
                return {"can_refund": False, "reason": "Refund window has expired (24 hours from purchase - Telegram limit)"}
            
            # Check if within 3-day refund window (our policy)
            refund_deadline = created_at + (3 * 24 * 60 * 60)  # 3 days in seconds
            
            if current_time > refund_deadline:
                conn.close()
                return {"can_refund": False, "reason": "Refund window has expired (3 days from purchase)"}
            
            # Check if there's already a pending refund
            cursor.execute('''
            SELECT COUNT(*) FROM refunds 
            WHERE subscription_id = ? AND status = 'pending'
            ''', (subscription_id,))
            
            pending_count = cursor.fetchone()[0]
            if pending_count > 0:
                conn.close()
                return {"can_refund": False, "reason": "Refund request already pending"}
            
            conn.close()
            
            return {
                "can_refund": True,
                "subscription_id": subscription_id,
                "payment_id": payment_id,
                "telegram_payment_charge_id": telegram_payment_charge_id,
                "stars_amount": stars_amount,
                "days_remaining": (telegram_refund_deadline - current_time) // (24 * 60 * 60)
            }
            
        except Exception as e:
            logger.error(f"Error checking refund eligibility: {e}")
            return {"can_refund": False, "reason": "Error checking refund eligibility"}
    
    def request_refund(self, owner_id: int, group_id: int, reason: str = None) -> dict:
        """Request a refund for a premium subscription."""
        try:
            # Check eligibility first
            eligibility = self.can_request_refund(owner_id, group_id)
            if not eligibility["can_refund"]:
                return {"success": False, "reason": eligibility["reason"]}
            
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            # Create refund record
            cursor.execute('''
            INSERT INTO refunds (subscription_id, owner_id, group_id, payment_id, stars_amount, refund_reason, refunded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                eligibility["subscription_id"],
                owner_id,
                group_id,
                eligibility["payment_id"],  # Store the actual payment_id, not telegram_payment_charge_id
                eligibility["stars_amount"],
                reason,
                int(time.time())
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "refund_id": cursor.lastrowid,
                "stars_amount": eligibility["stars_amount"],
                "days_remaining": eligibility["days_remaining"]
            }
            
        except Exception as e:
            logger.error(f"Error requesting refund: {e}")
            return {"success": False, "reason": "Error processing refund request"}
    
    def process_refund(self, refund_id: int, processed_by: str) -> dict:
        """Process a refund request and mark it as completed."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            # Get refund details
            cursor.execute('''
            SELECT subscription_id, owner_id, group_id, payment_id, stars_amount 
            FROM refunds WHERE id = ? AND status = 'pending'
            ''', (refund_id,))
            
            refund = cursor.fetchone()
            if not refund:
                conn.close()
                return {"success": False, "reason": "Refund not found or already processed"}
            
            subscription_id, owner_id, group_id, payment_id, stars_amount = refund
            
            # Mark refund as processed
            cursor.execute('''
            UPDATE refunds SET status = 'completed', processed_by = ? WHERE id = ?
            ''', (processed_by, refund_id))
            
            # Deactivate premium subscription
            cursor.execute('''
            UPDATE premium_subscriptions SET is_active = 0 WHERE id = ?
            ''', (subscription_id,))
            
            # Mark group as refunded
            cursor.execute('''
            INSERT INTO refunded_groups (group_id, owner_id, refunded_at, reason)
            VALUES (?, ?, ?, ?)
            ''', (group_id, owner_id, int(time.time()), "Processed refund"))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "owner_id": owner_id,
                "group_id": group_id,
                "payment_id": payment_id,
                "stars_amount": stars_amount
            }
            
        except Exception as e:
            logger.error(f"Error processing refund: {e}")
            return {"success": False, "reason": "Error processing refund"}
    
    def get_pending_refunds(self) -> list:
        """Get all pending refund requests."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT r.id, r.owner_id, r.group_id, r.payment_id, r.stars_amount, 
                   r.refund_reason, r.refunded_at, p.owner_id as subscription_owner
            FROM refunds r
            JOIN premium_subscriptions p ON r.subscription_id = p.id
            WHERE r.status = 'pending'
            ORDER BY r.refunded_at ASC
            ''')
            
            refunds = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "refund_id": refund[0],
                    "owner_id": refund[1],
                    "group_id": refund[2],
                    "payment_id": refund[3],
                    "stars_amount": refund[4],
                    "refund_reason": refund[5],
                    "refunded_at": refund[6],
                    "subscription_owner": refund[7]
                }
                for refund in refunds
            ]
            
        except Exception as e:
            logger.error(f"Error getting pending refunds: {e}")
            return []
    
    def get_user_refunds(self, owner_id: int) -> list:
        """Get all refunds for a user."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, group_id, payment_id, stars_amount, refund_reason, 
                   refunded_at, status, processed_by
            FROM refunds 
            WHERE owner_id = ?
            ORDER BY refunded_at DESC
            ''', (owner_id,))
            
            refunds = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "refund_id": refund[0],
                    "group_id": refund[1],
                    "payment_id": refund[2],
                    "stars_amount": refund[3],
                    "refund_reason": refund[4],
                    "refunded_at": refund[5],
                    "status": refund[6],
                    "processed_by": refund[7]
                }
                for refund in refunds
            ]
            
        except Exception as e:
            logger.error(f"Error getting user refunds: {e}")
            return []
    
    def get_payment_details_for_refund(self, refund_id: int) -> dict:
        """Get payment details needed for Telegram Stars refund."""
        try:
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT r.payment_id, r.owner_id, r.stars_amount, r.group_id, p.telegram_payment_charge_id
            FROM refunds r
            JOIN premium_subscriptions p ON r.subscription_id = p.id
            WHERE r.id = ? AND r.status = 'pending'
            ''', (refund_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "telegram_payment_charge_id": result[4],  # Get the actual telegram_payment_charge_id from premium_subscriptions
                    "owner_id": result[1],
                    "stars_amount": result[2],
                    "group_id": result[3],
                    "payment_id": result[0]  # Store the payment_id for reference
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting payment details for refund: {e}")
            return None

# Global premium system instance
premium_system = PremiumSystem()

async def is_bot_admin_and_user_owner(context, group_id, user_id):
    """
    Utility function to check if the bot is admin and the user is the group owner in the group.
    Returns (is_admin, is_owner, error_message)
    """
    try:
        bot = context.bot
        # Check bot admin status
        bot_member = await bot.get_chat_member(group_id, bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            return False, False, "❌ Bot must be admin in the group to manage premium features. Please add the bot as admin."
        # Check user owner status
        user_member = await bot.get_chat_member(group_id, user_id)
        if user_member.status != "creator":
            return True, False, "❌ Only the group owner can set or manage premium links."
        return True, True, None
    except Exception as e:
        return False, False, f"❌ Could not verify admin/owner status: {e}"

async def handle_premium_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle premium button click - start the improved premium flow with group sharing."""
    try:
        query = update.callback_query
        if query and hasattr(query, 'answer'):
            await query.answer()
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        # Rate limiting for premium button clicks
        try:
            from rate_limiter import can_user_use_command
            can_use, seconds_remaining = can_user_use_command(user_id, chat_id, "premium_button")
            
            if not can_use:
                # User is rate limited
                if query and hasattr(query, 'message'):
                    await query.message.reply_text(
                        f"⏰ Please wait {seconds_remaining} seconds before clicking Premium again.",
                        reply_to_message_id=query.message.message_id
                    )
                else:
                    await update.message.reply_text(
                        f"⏰ Please wait {seconds_remaining} seconds before clicking Premium again."
                    )
                return
        except ImportError:
            # Rate limiter not available, continue without rate limiting
            logger.warning("Rate limiter not available, continuing without rate limiting")

        # Check if user is in private chat (required for payment)
        if update.effective_chat.type != "private":
            if query and hasattr(query, 'message'):
                await query.message.reply_text(
                    "💫 Premium subscriptions can only be purchased in private chat.\n"
                    "Please message me privately to continue.",
                    reply_to_message_id=query.message.message_id
                )
            return

        # Check if user already has an active premium subscription
        user_groups = premium_system.get_user_premium_groups(user_id)
        if user_groups:
            # Check for missing links in each group
            missing_links = []
            group_id = user_groups[0]['group_id']  # If multiple, just use the first for now
            links = premium_system.get_premium_links(group_id)
            if not links:
                # Something went wrong with the database
                if query and hasattr(query, 'message'):
                    await query.message.reply_text(
                        "❌ Error retrieving your premium subscription. Please contact support.",
                        reply_to_message_id=query.message.message_id
                    )
                else:
                    await update.message.reply_text(
                        "❌ Error retrieving your premium subscription. Please contact support."
                    )
                return
                
            link_names = [
                ('mrkt_link', 'MRKT', 'https://t.me/mrkt/app?startapp='),
                ('palace_link', 'Palace', 'https://t.me/palacenftbot/app?startapp='),
                ('tonnel_link', 'Tonnel', 'https://t.me/tonnel_network_bot/gifts?startapp=ref_'),
                ('portal_link', 'Portal', 'https://t.me/portals/market?startapp=')
            ]
            for key, label, example in link_names:
                if not links.get(key):
                    missing_links.append((label, example))
            if missing_links:
                msg = "You have premium, but some referral links are missing. Please provide the following:\n\n"
                for label, example in missing_links:
                    msg += f"- {label}: Example: {example}...\n"
                msg += "\nSend the missing links one by one in the format: <type> <link>\nFor example: MRKT https://t.me/mrkt/app?startapp=800092886"
                if query and hasattr(query, 'message'):
                    await query.message.reply_text(msg, reply_to_message_id=query.message.message_id)
                else:
                    await update.message.reply_text(msg)
                context.user_data['premium_setup_step'] = 'complete_missing_links'
                context.user_data['premium_group_id'] = group_id
                context.user_data['premium_missing_links'] = [label.lower() for label, _ in missing_links]
                return
            else:
                msg = (
                    "💫 You already have an active premium subscription!\n\n"
                    "All your referral links are set. Use /configure to update any link."
                )
                if query and hasattr(query, 'message'):
                    await query.message.reply_text(msg, reply_to_message_id=query.message.message_id)
                else:
                    await update.message.reply_text(msg)
                return

        # Check if user is already in setup process
        if context.user_data.get('premium_setup_step'):
            msg = (
                "⚙️ You are already in the middle of premium setup.\n"
                "Please complete the setup or use /cancel_premium to cancel."
            )
            if query and hasattr(query, 'message'):
                await query.message.reply_text(msg, reply_to_message_id=query.message.message_id)
            else:
                await update.message.reply_text(msg)
            return

        # Start the improved premium flow - ask user to share their group
        share_group_button = KeyboardButton(
            text="📤 Share Group to Upgrade",
            request_chat=KeyboardButtonRequestChat(
                request_id=1,
                chat_is_channel=False,      # Groups only, not channels
                chat_is_created=True        # Only groups the user created/owns
            )
        )
        share_keyboard = ReplyKeyboardMarkup(
            [[share_group_button]], 
            resize_keyboard=True,
            one_time_keyboard=True
        )

        welcome_msg = (
            "**Premium Group Features**\n\n"
            "**What you get:**\n"
            "• Custom referral links for all platforms\n"
            "• Branded gift price cards\n"
            "• Clean, professional appearance\n"
            "• Priority support\n\n"
            "**Price:** 99 Stars\n"
            "**Duration:** 30 days\n\n"
            "💡 **Earn 35% commission** on purchases through your referral links using Telegram's commission plan!\n\n"
            "**Requirements:**\n"
            "• Group owner/creator\n\n"
            "Share your group to continue:"
        )

        # Get the path to the premium image
        script_dir = os.path.dirname(os.path.abspath(__file__))
        premium_image_path = os.path.join(script_dir, "assets", "premium.jpg")
        
        if query and hasattr(query, 'message'):
            await query.message.reply_photo(
                photo=open(premium_image_path, 'rb'),
                caption=welcome_msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=share_keyboard,
                reply_to_message_id=query.message.message_id
            )
        else:
            await update.message.reply_photo(
                photo=open(premium_image_path, 'rb'),
                caption=welcome_msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=share_keyboard
            )

        # Set the setup step to waiting for group share
        context.user_data['premium_setup_step'] = 'waiting_for_group_share'
        context.user_data['premium_flow_started'] = True

    except Exception as e:
        logger.error(f"Error in handle_premium_button: {e}")
        error_msg = "❌ An error occurred while starting premium setup. Please try again."
        if query and hasattr(query, 'message'):
            await query.message.reply_text(error_msg, reply_to_message_id=query.message.message_id)
        else:
            await update.message.reply_text(error_msg)

async def handle_pre_checkout_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pre-checkout query for premium payment."""
    query = update.pre_checkout_query
    payment_id = query.invoice_payload
    
    logger.info(f"Pre-checkout query received for payment ID: {payment_id}")
    
    # Verify payment exists and is not expired
    if premium_system.verify_payment_exists(payment_id):
        # Accept the payment
        await query.answer(ok=True)
        logger.info(f"Pre-checkout query approved for payment ID: {payment_id}")
    else:
        # Reject the payment
        await query.answer(ok=False, error_message="Payment request expired or not found. Please try again.")
        logger.warning(f"Pre-checkout query rejected for payment ID: {payment_id}")

async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle successful payment for premium subscription."""
    try:
        payment = update.message.successful_payment
        payment_id = payment.invoice_payload
        telegram_payment_charge_id = payment.telegram_payment_charge_id
        user_id = update.effective_user.id
        
        logger.info(f"Payment successful for user {user_id} with payment ID {payment_id}")
        
        # Mark payment as completed
        if not premium_system.mark_payment_completed(payment_id):
            logger.error(f"Failed to mark payment {payment_id} as completed")
            await update.message.reply_text(
                "❌ Error processing payment. Please contact support."
            )
            return
        
        # Get the group ID from context (set during group share)
        group_id = context.user_data.get('premium_group_id')
        if not group_id:
            logger.error(f"No group ID found in context for user {user_id}")
            await update.message.reply_text(
                "❌ Error: Group information not found. Please contact support."
            )
            return
        
        # Add the premium subscription to database
        success = premium_system.add_premium_subscription(
            owner_id=user_id,
            group_id=group_id,
            payment_id=payment_id,
            telegram_payment_charge_id=telegram_payment_charge_id
        )
        
        if not success:
            logger.error(f"Failed to add premium subscription for user {user_id}, group {group_id}")
            await update.message.reply_text(
                "❌ Error creating premium subscription. Please contact support."
            )
            return
        
        # Clear the payment step and start referral setup
        context.user_data['premium_setup_step'] = 'mrkt_link'
        
        await update.message.reply_text(
            "✅ Payment successful!\n\n"
            "📤 Send MRKT link:"
        )
        
        logger.info(f"Premium subscription activated for user {user_id}, group {group_id}")
        
    except Exception as e:
        logger.error(f"Error in successful payment handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing your payment. Please contact support."
        )

async def handle_premium_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle premium payment cancellation."""
    query = update.callback_query
    await query.answer()
    
    # Clear any stored payment data
    if 'premium_payment_id' in context.user_data:
        del context.user_data['premium_payment_id']
    if 'premium_setup_step' in context.user_data:
        del context.user_data['premium_setup_step']
    
    await query.message.edit_text(
        "❌ *Premium Purchase Cancelled*\n\n"
        "You can try again anytime by clicking the Premium button.",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_premium_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle premium group setup flow for referral link collection after payment."""
    try:
        user_id = update.effective_user.id
        step = context.user_data.get('premium_setup_step')
        logger.info(f"Premium setup step: {step}, user_id: {user_id}")
        logger.info(f"Context data: {dict(context.user_data)}")
        
        if not step:
            await update.message.reply_text(
                "⚠️ Use /premium to start setup"
            )
            context.user_data.clear()
            return
        
        # Handle referral link collection steps
        if step == 'mrkt_link':
            mrkt_link = update.message.text.strip()
            if not is_valid_link(mrkt_link, 'mrkt'):
                await update.message.reply_text(
                    "❌ Invalid format. Example: t.me/mrkt/app?startapp=..."
                )
                return
            context.user_data['premium_mrkt_link'] = mrkt_link
            context.user_data['premium_setup_step'] = 'palace_link'
            await update.message.reply_text(
                "✅ MRKT saved!\n\n📤 Send Palace link:"
            )
        
        elif step == 'palace_link':
            palace_link = update.message.text.strip()
            logger.info(f"Palace link received: {palace_link}")
            
            try:
                # Test link validation first
                logger.info("Testing Palace link validation...")
                if not is_valid_link(palace_link, 'palace'):
                    logger.warning(f"Invalid Palace link: {palace_link}")
                    await update.message.reply_text(
                        "❌ Invalid format. Example: t.me/palacenftbot/app?startapp=..."
                    )
                    return
                
                logger.info("Palace link validation passed, saving to context...")
                context.user_data['premium_palace_link'] = palace_link
                
                logger.info("Updating setup step to tonnel_link...")
                context.user_data['premium_setup_step'] = 'tonnel_link'
                
                logger.info("Sending success message...")
                try:
                    await update.message.reply_text(
                        "✅ Palace saved!\n\n📤 Send Tonnel link:"
                    )
                    logger.info("Palace link step completed successfully")
                except Exception as reply_error:
                    logger.error(f"Error sending reply message: {reply_error}")
                    raise reply_error
                
            except Exception as palace_error:
                logger.error(f"Error in Palace link step: {palace_error}")
                logger.exception("Palace link step exception")
                raise palace_error  # Re-raise to be caught by outer exception handler
        
        elif step == 'tonnel_link':
            try:
                logger.info(f"Processing tonnel_link step for user {user_id}")
                tonnel_link = update.message.text.strip()
                logger.info(f"Tonnel link received: {tonnel_link}")
                
                # Validate link format
                logger.info("Validating tonnel link...")
                if not is_valid_link(tonnel_link, 'tonnel'):
                    logger.warning(f"Invalid tonnel link format: {tonnel_link}")
                    await update.message.reply_text(
                        "❌ Invalid format. Example: t.me/tonnel_network_bot/gifts?startapp=ref_..."
                    )
                    return
                
                logger.info("Tonnel link validation passed, saving to context...")
                context.user_data['premium_tonnel_link'] = tonnel_link
                
                logger.info("Updating setup step to portal_link...")
                context.user_data['premium_setup_step'] = 'portal_link'
                
                logger.info("Sending success message...")
                await update.message.reply_text(
                    "✅ Tonnel saved!\n\n📤 Send Portal link:"
                )
                logger.info("Tonnel link step completed successfully")
                
            except Exception as tonnel_error:
                logger.error(f"Error in tonnel link step: {tonnel_error}")
                logger.exception("Tonnel link step exception details")
                await update.message.reply_text(
                    f"❌ Error in tonnel link step: {str(tonnel_error)}\n\n"
                    "Please try again with /premium."
                )
                context.user_data.clear()
        
        elif step == 'portal_link':
            try:
                logger.info(f"Processing portal_link step for user {user_id}")
                portal_link = update.message.text.strip()
                logger.info(f"Portal link received: {portal_link}")
                
                # Validate link format
                logger.info("Validating portal link...")
                if not is_valid_link(portal_link, 'portal'):
                    logger.warning(f"Invalid portal link format: {portal_link}")
                    await update.message.reply_text(
                        "❌ Invalid format. Example: t.me/portals/market?startapp=..."
                    )
                    return
                
                logger.info("Portal link validation passed")
                
                # Save all premium data
                logger.info("Getting data from context...")
                payment_id = context.user_data.get('premium_payment_id')
                group_id = context.user_data.get('premium_group_id')
                mrkt_link = context.user_data.get('premium_mrkt_link')
                palace_link = context.user_data.get('premium_palace_link')
                tonnel_link = context.user_data.get('premium_tonnel_link')
                
                logger.info(f"Context data retrieved: payment_id={payment_id}, group_id={group_id}")
                logger.info(f"Links: MRKT={mrkt_link}, Palace={palace_link}, Tonnel={tonnel_link}, Portal={portal_link}")
                
                # Verify all required data is present
                if not all([payment_id, group_id, mrkt_link, palace_link, tonnel_link, portal_link]):
                    missing_items = []
                    if not payment_id: missing_items.append("payment_id")
                    if not group_id: missing_items.append("group_id") 
                    if not mrkt_link: missing_items.append("mrkt_link")
                    if not palace_link: missing_items.append("palace_link")
                    if not tonnel_link: missing_items.append("tonnel_link")
                    if not portal_link: missing_items.append("portal_link")
                    
                    logger.error(f"Missing data in premium setup: {missing_items}")
                    logger.error(f"Context data: payment_id={payment_id}, group_id={group_id}, mrkt={mrkt_link}, palace={palace_link}, tonnel={tonnel_link}, portal={portal_link}")
                    
                    await update.message.reply_text(
                        "❌ Missing data. Restart with /premium."
                    )
                    context.user_data.clear()
                    return
                
                logger.info("All required data is present, updating premium subscription...")
                
                # Update the premium subscription with referral links
                try:
                    success = premium_system.add_premium_subscription(
                        owner_id=user_id,
                        group_id=group_id,
                        payment_id=payment_id,
                        telegram_payment_charge_id=payment_id,  # Use payment_id as telegram_payment_charge_id for updates
                        mrkt_link=mrkt_link,
                        palace_link=palace_link,
                        tonnel_link=tonnel_link,
                        portal_link=portal_link
                    )
                    
                    if success:
                        # Clear setup data
                        context.user_data.clear()
                        
                        # Send success message with photo
                        success_msg = (
                            "**Premium Activated!** 🎉\n\n"
                            "**Your group now has:**\n"
                            "• Custom referral links\n"
                            "• Branded gift cards\n"
                            "• Clean appearance\n"
                            "• Priority support\n\n"
                            "**How to use:**\n"
                            "Type any gift name in your group (like 'tama', 'pepe') and enjoy premium features!\n\n"
                            "**Commands:**\n"
                            "• `/premium_status` - Check status\n"
                            "• `/configure` - Update links\n"
                            "• `/refund` - Refund info\n\n"
                            "**Duration:** 30 days"
                        )
                        
                        # Get the path to the premium active image
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        premium_active_image_path = os.path.join(script_dir, "assets", "premiumactive.png")
                        
                        await update.message.reply_photo(
                            photo=open(premium_active_image_path, 'rb'),
                            caption=success_msg,
                            parse_mode=ParseMode.MARKDOWN
                        )
                        
                        logger.info(f"Premium setup completed successfully for user {user_id}, group {group_id}")
                    else:
                        await update.message.reply_text(
                            "❌ Error saving links. Contact support."
                        )
                        context.user_data.clear()
                        
                except Exception as save_error:
                    logger.error(f"Error saving premium subscription: {save_error}")
                    await update.message.reply_text(
                        "❌ Error saving links. Contact support."
                    )
                    context.user_data.clear()
                
            except Exception as portal_error:
                logger.error(f"Error in portal link step: {portal_error}")
                logger.exception("Portal link step exception details")
                await update.message.reply_text(
                    f"❌ Error in portal link step: {str(portal_error)}\n\n"
                    "Please try again with /premium."
                )
                context.user_data.clear()
        
        else:
            # Unknown step
            await update.message.reply_text(
                "❌ Error in {step} step. Try /premium again."
            )
            context.user_data.clear()
            
    except Exception as e:
        logger.error(f"Error in premium setup handler: {e}")
        logger.exception("Premium setup exception details")
        await update.message.reply_text(
            "❌ Setup error. Try /premium again."
        )
        context.user_data.clear()

def get_premium_keyboard(group_id: int = None) -> InlineKeyboardMarkup:
    """Get keyboard with premium button for gift cards."""
    keyboard = []
    
    # Check if this group has premium
    if group_id and premium_system.is_group_premium(group_id):
        # Group has premium, show premium indicator
        keyboard.append([
            InlineKeyboardButton("💫 Premium Active", callback_data="premium_info")
        ])
    else:
        # Group doesn't have premium, show premium button
        keyboard.append([
            InlineKeyboardButton("💫 Get Premium", callback_data="premium_button")
        ])
    
    return InlineKeyboardMarkup(keyboard)

async def handle_configure_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the premium configuration flow for updating referral links with admin/owner checks."""
    try:
        user_id = update.effective_user.id
        step = context.user_data.get('configure_step')
        if not step:
            await update.message.reply_text(
                "⚠️ Configuration not started. Please use /configure to begin."
            )
            return
        if step in ["group_select", "edit_menu", "link_update"]:
            group_id = context.user_data.get('configure_group_id')
            if not group_id and step == "group_select":
                group_id_text = update.message.text.strip()
                if group_id_text.startswith('-100'):
                    group_id = int(group_id_text)
                else:
                    group_id = None
            # No admin check needed - ownership is verified by database
        if step == 'group_select':
            group_id = update.message.text.strip()
            groups = premium_system.get_user_premium_groups(user_id)
            
            if not groups:
                await update.message.reply_text(
                    "❌ You do not own any premium groups. Purchase premium with /premium first.",
                    reply_markup=ReplyKeyboardRemove()
                )
                context.user_data.clear()
                return
                
            if not any(str(g['group_id']) == group_id for g in groups):
                await update.message.reply_text(
                    "❌ You do not own this group or it is not premium. Try again.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return
                
            context.user_data['configure_group_id'] = int(group_id)
            context.user_data['configure_step'] = 'edit_menu'
            
            # Show 4-button inline keyboard
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("MRKT", callback_data="edit_mrkt")],
                [InlineKeyboardButton("Tonnel", callback_data="edit_tonnel")],
                [InlineKeyboardButton("Portal", callback_data="edit_portal")],
                [InlineKeyboardButton("Palace", callback_data="edit_palace")],
            ])
            
            await update.message.reply_text(
                "Edit your referral links for this group:",
                reply_markup=keyboard
            )
            return
            
        if step == 'link_update':
            link_type = context.user_data.get('configure_link_type')
            
            if not link_type:
                await update.message.reply_text(
                    "❌ Link type not specified. Please use /configure to start again.",
                    reply_markup=ReplyKeyboardRemove()
                )
                context.user_data.clear()
                return
                
            new_link = update.message.text.strip()
            
            if not is_valid_link(new_link, link_type):
                example = (
                    "https://t.me/mrkt/app?startapp=..." if link_type == 'mrkt' else
                    "https://t.me/tonnel_network_bot/gifts?startapp=ref_..." if link_type == 'tonnel' else
                    "https://t.me/portals/market?startapp=..." if link_type == 'portal' else
                    "https://t.me/palacenftbot/app?startapp=..."
                )
                await update.message.reply_text(
                    f"❌ Invalid {link_type.upper()} link format. Example: {example}",
                    reply_markup=ReplyKeyboardRemove()
                )
                return
                
            group_id = context.user_data.get('configure_group_id')
            
            if not group_id:
                await update.message.reply_text(
                    "❌ Group ID not found. Please use /configure to start again.",
                    reply_markup=ReplyKeyboardRemove()
                )
                context.user_data.clear()
                return
                
            links = premium_system.get_premium_links(group_id)
            
            if not links:
                await update.message.reply_text(
                    "❌ Could not find premium subscription for this group. Please use /configure to start again.",
                    reply_markup=ReplyKeyboardRemove()
                )
                context.user_data.clear()
                return
                
            mrkt = new_link if link_type == 'mrkt' else links['mrkt_link']
            palace = new_link if link_type == 'palace' else links['palace_link']
            tonnel = new_link if link_type == 'tonnel' else links['tonnel_link']
            portal = new_link if link_type == 'portal' else links['portal_link']
            owner_id = user_id
            payment_id = 'update'
            
            success = premium_system.add_premium_subscription(
                owner_id=owner_id,
                group_id=group_id,
                payment_id=payment_id,
                telegram_payment_charge_id=payment_id,
                mrkt_link=mrkt,
                palace_link=palace,
                tonnel_link=tonnel,
                portal_link=portal
            )
            
            if not success:
                await update.message.reply_text(
                    "❌ Failed to update link. Please try again later.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return
                
            await update.message.reply_text(
                f"✅ {link_type.upper()} link updated for group {group_id}.",
                reply_markup=ReplyKeyboardRemove()
            )
            
            # Return to 4-button menu
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("MRKT", callback_data="edit_mrkt")],
                [InlineKeyboardButton("Tonnel", callback_data="edit_tonnel")],
                [InlineKeyboardButton("Portal", callback_data="edit_portal")],
                [InlineKeyboardButton("Palace", callback_data="edit_palace")],
            ])
            
            await update.message.reply_text(
                "Edit another link or close this menu.",
                reply_markup=keyboard
            )
            
            context.user_data['configure_step'] = 'edit_menu'
            return
        
        # Unknown step
        await update.message.reply_text(
            "❌ Invalid configuration step. Please use /configure to start again.",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        
    except Exception as e:
        logger.error(f"Error in configure flow: {e}")
        await update.message.reply_text(
            "❌ An error occurred during configuration. Please try again or contact support.",
            reply_markup=ReplyKeyboardRemove()
        )
        # Don't clear context data to allow for retry

async def handle_premium_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user's current premium configuration including group ID and referral links."""
    try:
        user_id = update.effective_user.id
        logger.info(f"Handling premium status for user {user_id}")
        
        if not user_id:
            await update.message.reply_text(
                "❌ Unable to identify user. Please try again."
            )
            return
        
        # Query database for user's premium subscriptions
        try:
            logger.info(f"Connecting to premium_subscriptions.db")
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            
            logger.info(f"Executing query for owner_id={user_id}")
            cursor.execute('''
                SELECT group_id, mrkt_link, palace_link, tonnel_link, portal_link, 
                       expires_at, is_active
                FROM premium_subscriptions 
                WHERE owner_id = ? AND is_active = 1
                ORDER BY expires_at DESC
            ''', (user_id,))
            
            subscriptions = cursor.fetchall()
            logger.info(f"Found {len(subscriptions)} premium subscriptions")
            conn.close()
        except Exception as db_error:
            logger.error(f"Database error in premium_status: {db_error}")
            logger.exception("Database error details")
            await update.message.reply_text(
                "❌ Database error while fetching your premium status. Please try again or contact support."
            )
            return
        
        if not subscriptions:
            await update.message.reply_text(
                "📊 Your Premium Groups & Links\n\n"
                "❌ No active premium subscriptions found.\n\n"
                "💡 To set up premium:\n"
                "1. Add your bot as admin in your group\n"
                "2. Use /premium to start setup\n"
                "3. Make sure you're the group owner\n\n"
                "🔧 Troubleshooting:\n"
                "• You must be the group creator/owner\n"
                "• Group ID should start with -100"
            )
            return
        
        # Format the status message
        status_message = "📊 Your Premium Groups & Links\n\n"
        status_message += f"👑 You are the owner of {len(subscriptions)} premium group(s):\n\n"
        
        for i, (group_id, mrkt_link, palace_link, tonnel_link, portal_link, expires_at, is_active) in enumerate(subscriptions, 1):
            status_message += f"🏢 Group #{i}:\n"
            status_message += f"🆔 Group ID: {group_id}\n"
            
            # Format the expiration date nicely
            try:
                from datetime import datetime
                if isinstance(expires_at, str):
                    exp_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                else:
                    exp_date = datetime.fromtimestamp(expires_at)
                formatted_date = exp_date.strftime("%Y-%m-%d %H:%M")
                status_message += f"⏰ Expires: {formatted_date}\n"
            except Exception as date_error:
                logger.error(f"Date formatting error: {date_error}")
                status_message += f"⏰ Expires: {expires_at}\n"
                
            status_message += f"✅ Status: {'Active' if is_active else 'Inactive'}\n\n"
            
            status_message += "🔗 Referral Links:\n"
            if mrkt_link:
                status_message += f"🏪 MRKT: {mrkt_link}\n"
            else:
                status_message += f"🏪 MRKT: ❌ Not set\n"
                
            if palace_link:
                status_message += f"🏰 Palace: {palace_link}\n"
            else:
                status_message += f"🏰 Palace: ❌ Not set\n"
                
            if tonnel_link:
                status_message += f"🚇 Tonnel: {tonnel_link}\n"
            else:
                status_message += f"🚇 Tonnel: ❌ Not set\n"
                
            if portal_link:
                status_message += f"🌀 Portal: {portal_link}\n"
            else:
                status_message += f"🌀 Portal: ❌ Not set\n"
            
            status_message += "\n" + "─" * 20 + "\n\n"
        
        status_message += "💡 Commands:\n"
        status_message += "• /premium_status - Check status\n"
        status_message += "• /configure - Update links\n"
        status_message += "• /refund - Refund info\n"
        status_message += "• /terms - Terms of service"
        
        logger.info("Sending premium status message")
        
        # Send photo with status text
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        photo_path = os.path.join(script_dir, "assets", "statues.png")
        if os.path.exists(photo_path):
            await update.message.reply_photo(
                photo=open(photo_path, 'rb'),
                caption=status_message
            )
        else:
            # Fallback to text only if image not found
            await update.message.reply_text(status_message)
        
    except Exception as e:
        logger.error(f"Error in handle_premium_status: {e}")
        logger.exception("Premium status exception details")
        await update.message.reply_text(
            f"❌ Error in premium status: {str(e)}\n\nPlease try again or contact support."
        )

async def pending_payment_monitor(application, reminder_minutes=25, check_interval=60):
    """
    Periodically check for pending payments:
    - Send reminders if payment is about to expire (e.g., 5 minutes left)
    - Auto-cancel expired payments and notify users
    """
    from telegram.constants import ParseMode
    while True:
        try:
            now = int(time.time())
            conn = sqlite3.connect(PREMIUM_DB_FILE)
            cursor = conn.cursor()
            # Reminders: payments expiring in 5 minutes (25 minutes old)
            reminder_time = now + (5 * 60)
            cursor.execute(
                "SELECT owner_id, payment_id, expires_at FROM pending_payments WHERE expires_at BETWEEN ? AND ?",
                (now, reminder_time)
            )
            reminders = cursor.fetchall()
            for owner_id, payment_id, expires_at in reminders:
                try:
                    user_chat_id = owner_id
                    minutes_left = int((expires_at - now) / 60)
                    await application.bot.send_message(
                        chat_id=user_chat_id,
                        text=f"⏰ Your premium payment is still pending. Please complete it within {minutes_left} minutes, or it will be cancelled.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.error(f"Error sending pending payment reminder to {owner_id}: {e}")
            # Expired: payments past expiry
            cursor.execute(
                "SELECT owner_id, payment_id FROM pending_payments WHERE expires_at <= ?",
                (now,)
            )
            expired = cursor.fetchall()
            for owner_id, payment_id in expired:
                try:
                    user_chat_id = owner_id
                    await application.bot.send_message(
                        chat_id=user_chat_id,
                        text="❌ Your pending premium payment has expired. Please start again if you still want premium.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.error(f"Error sending expired payment notification to {owner_id}: {e}")
            # Remove expired payments
            cursor.execute(
                "DELETE FROM pending_payments WHERE expires_at <= ?",
                (now,)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error in pending payment monitor: {e}")
        await asyncio.sleep(check_interval)

def start_pending_payment_monitor(application):
    loop = asyncio.get_event_loop()
    loop.create_task(pending_payment_monitor(application))
async def handle_premium_group_share(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle when user shares their group via the Share Group button."""
    try:
        # Check if this is a group share for premium flow
        if not update.message.chat_shared or update.message.chat_shared.request_id != 1:
            return  # Not a premium group share
        
        user_id = update.effective_user.id
        group_id = update.message.chat_shared.chat_id
        
        # Remove the keyboard
        await update.message.reply_text(
            "🔍 Checking eligibility...",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Check if bot is in the group
        try:
            chat_info = await context.bot.get_chat(group_id)
            bot_is_member = True
        except Exception as e:
            logger.error(f"Bot not in group {group_id}: {e}")
            bot_is_member = False
        
        if not bot_is_member:
            await update.message.reply_text(
                "❌ **Bot Not in Group**\n\n"
                "The bot must be added to your group first.\n\n"
                "**To add the bot:**\n"
                "1. Go to your group settings\n"
                "2. Add @giftschart as a member\n"
                "3. Try again with /premium\n\n"
                "💡 The bot needs to be in your group to provide premium features."
            )
            # Clear the setup state
            context.user_data.clear()
            return
        
        # ✅ Ownership guaranteed by chat_is_created=True - proceed to payment
        await update.message.reply_text(
            "✅ Ownership verified!\n\n"
            "💰 Price: 99 Telegram Stars\n"
            "⏰ 30 minutes to complete payment"
        )
        
        # Store the group ID for later use
        context.user_data['premium_group_id'] = group_id
        context.user_data['premium_setup_step'] = 'payment_pending'
        
        # Create payment request
        payment_data = premium_system.create_payment_request(user_id)
        if not payment_data:
            await update.message.reply_text(
                "❌ Error creating payment request. Please try again later."
            )
            context.user_data.clear()
            return
        
        context.user_data['premium_payment_id'] = payment_data['payment_id']
        
        # Send the payment invoice
        title = "💫 Premium Subscription"
        description = "Custom referral links for your group"
        prices = [LabeledPrice("Premium Subscription", PREMIUM_PRICE_STARS)]
        
        try:
            await context.bot.send_invoice(
                chat_id=update.effective_chat.id,
                title=title,
                description=description,
                payload=payment_data['payment_id'],
                provider_token="",  # Empty string for Stars payments
                currency="XTR",
                prices=prices,
                start_parameter="premium_subscription"
            )
            logger.info(f"Sent premium invoice to user {user_id} for group {group_id} with payment ID {payment_data['payment_id']}")
            
        except Exception as e:
            logger.error(f"Error sending premium invoice: {e}")
            await update.message.reply_text(
                "❌ Error creating payment invoice. Please try again later."
            )
            context.user_data.clear()
            return
            
    except Exception as e:
        logger.error(f"Error in handle_premium_group_share: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing your group. Please try again."
        )
        context.user_data.clear()

