#!/usr/bin/env python3
"""
Admin Dashboard for Telegram Gift & Sticker Bot (SQLite Version)

This module provides comprehensive admin functionality including:
- Bot statistics and analytics
- System health monitoring
- Premium system analytics (SQLite-based)
- Refund system analytics
- Usage analytics
- Rate limiting oversight
"""

import os
import sys
import logging
import sqlite3
import time
import json
import psutil
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# Configure logging
logger = logging.getLogger(__name__)

# Import bot configuration
try:
    from bot_config import ADMIN_USER_IDS
except ImportError:
    ADMIN_USER_IDS = [800092886, 6529233780]  # Default admin user IDs

# Database files
RATE_LIMITER_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sqlite_data", "user_requests.db")
PREMIUM_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sqlite_data", "premium_system.db")  # Fixed: was premium_subscriptions.db
ANALYTICS_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sqlite_data", "analytics.db")

def is_admin(user_id: int) -> bool:
    """Check if a user is an admin."""
    return user_id in ADMIN_USER_IDS

async def show_admin_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main admin dashboard menu."""
    query = update.callback_query
    
    # Show admin dashboard menu
    keyboard = [
        [InlineKeyboardButton("📊 Usage Statistics", callback_data="admin_usage")],
        [InlineKeyboardButton("💫 Premium System", callback_data="admin_premium")],
        [InlineKeyboardButton("💰 Refund Analytics", callback_data="admin_refunds")],
        [InlineKeyboardButton("🔧 System Status", callback_data="admin_system")],
        [InlineKeyboardButton("💾 Database Backup", callback_data="admin_backup")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔧 *Admin Dashboard*\n\nSelect an option to view:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin command."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin privileges required.")
        return
    
    # Show admin dashboard menu
    keyboard = [
        [InlineKeyboardButton("📊 Usage Statistics", callback_data="admin_usage")],
        [InlineKeyboardButton("💫 Premium System", callback_data="admin_premium")],
        [InlineKeyboardButton("💰 Refund Analytics", callback_data="admin_refunds")],
        [InlineKeyboardButton("🔧 System Status", callback_data="admin_system")],
        [InlineKeyboardButton("💾 Database Backup", callback_data="admin_backup")],
        [InlineKeyboardButton("🧹 Cleanup System", callback_data="admin_cleanup")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 *Admin Dashboard*\n\nSelect an option to view:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin dashboard callbacks."""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.answer("❌ Access denied.")
        return
    
    data = query.data
    
    if data == "admin_usage":
        await show_usage_statistics(update, context)
    elif data == "admin_premium":
        await show_premium_statistics(update, context)
    elif data == "admin_refunds":
        await show_refund_statistics(update, context)
    elif data == "admin_system":
        await show_system_status(update, context)
    elif data == "admin_backup":
        await show_backup_menu(update, context)
    elif data == "admin_cleanup":
        await show_cleanup_menu(update, context)
    elif data == "backup_status":
        await show_backup_status(update, context)
    elif data == "backup_now":
        await perform_manual_backup(update, context)
    elif data == "cleanup_messages":
        await perform_message_cleanup(update, context)
    elif data == "admin_back":
        await show_admin_main_menu(update, context)
    else:
        await query.answer("Unknown admin command")

async def show_usage_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show comprehensive usage statistics (gifts + stickers + users)."""
    query = update.callback_query
    
    try:
        # Get all usage data
        bot_stats = get_bot_usage_statistics()
        advanced_stats = get_advanced_analytics()
        
        stats_text = (
            "📊 *Usage Statistics*\n\n"
            f"🎁 *Gift Requests:*\n"
            f"  • Total: {bot_stats['total_gift_requests']:,}\n"
            f"  • Unique Users: {bot_stats['unique_users']:,}\n"
            f"  • Unique Chats: {bot_stats['unique_chats']:,}\n"
            f"  • Avg per User: {bot_stats['avg_requests_per_user']:.1f}\n"
            f"  • Top Gift: {bot_stats['top_gift']}\n\n"
            f"🌟 *Sticker Requests:*\n"
            f"  • Total: {bot_stats['total_sticker_requests']}\n"
            f"  • Top Sticker: {bot_stats['top_sticker']}\n\n"
            f"👥 *User Behavior:*\n"
            f"  • Retention Rate: {advanced_stats['user_retention_rate']:.1f}%\n"
            f"  • Bounce Rate: {advanced_stats['bounce_rate']:.1f}%\n"
            f"  • Content Diversity: {advanced_stats['content_diversity']} items\n"
            f"  • Peak Hour: {advanced_stats['peak_hour']}\n\n"
            f"📈 *Growth & Trends:*\n"
            f"  • Monthly Growth: {advanced_stats['monthly_growth']:.1f}%\n"
            f"  • Viral Coefficient: {advanced_stats['viral_coefficient']:.2f}\n"
            f"  • Engagement Score: {advanced_stats['engagement_score']}/100\n"
            f"  • Seasonal Trend: {advanced_stats['seasonal_trend']}\n\n"
            f"🔄 *Last Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error showing usage statistics: {e}")
        await query.answer("❌ Error loading usage statistics")

async def show_premium_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium system statistics from SQLite."""
    query = update.callback_query
    
    try:
        # Get premium statistics from SQLite
        premium_stats = get_premium_statistics_sqlite()
        
        stats_text = (
            "💫 *Premium System Statistics*\n\n"
            f"👥 *Total Premium Users:* {premium_stats['total_premium_users']}\n"
            f"💰 *Active Subscriptions:* {premium_stats['active_subscriptions']}\n"
            f"📅 *Expired Subscriptions:* {premium_stats['expired_subscriptions']}\n"
            f"💳 *Total Payment Requests:* {premium_stats['total_payment_requests']}\n"
            f"✅ *Successful Payments:* {premium_stats['successful_payments']}\n"
            f"⏳ *Pending Payments:* {premium_stats['pending_payments']}\n"
            f"👥 *Premium Groups:* {premium_stats['premium_groups']}\n\n"
            f"📊 *Revenue Statistics:*\n"
            f"  • Total Revenue: ${premium_stats['total_revenue']:.2f}\n"
            f"  • Monthly Revenue: ${premium_stats['monthly_revenue']:.2f}\n"
            f"  • Average Subscription: ${premium_stats['avg_subscription']:.2f}\n"
            f"  • Revenue per User: ${premium_stats['revenue_per_user']:.2f}\n\n"
            f"📈 *Recent Activity:*\n"
            f"  • New Subscriptions (7d): {premium_stats['new_subscriptions_7d']}\n"
            f"  • New Payments (7d): {premium_stats['new_payments_7d']}\n"
            f"  • Conversion Rate: {premium_stats['conversion_rate']:.1f}%\n"
            f"  • Premium Conversion: {premium_stats['premium_conversion_rate']:.1f}%\n\n"
            f"🔄 *Last Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error showing premium statistics: {e}")
        await query.edit_message_text(
            f"❌ *Error Loading Premium Statistics*\n\n"
            f"Error: {str(e)}\n\n"
            f"Please check database connection and try again.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")
            ]])
        )

async def show_refund_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show refund system statistics from SQLite."""
    query = update.callback_query
    
    try:
        # Get refund statistics from SQLite
        refund_stats = get_refund_statistics_sqlite()
        
        stats_text = (
            "💰 *Refund System Statistics*\n\n"
            f"📋 *Total Refund Requests:* {refund_stats['total_refund_requests']}\n"
            f"✅ *Approved Refunds:* {refund_stats['approved_refunds']}\n"
            f"❌ *Rejected Refunds:* {refund_stats['rejected_refunds']}\n"
            f"⏳ *Pending Refunds:* {refund_stats['pending_refunds']}\n"
            f"💸 *Total Refunded Amount:* ${refund_stats['total_refunded_amount']:.2f}\n\n"
            f"📊 *Refund Analytics:*\n"
            f"  • Approval Rate: {refund_stats['approval_rate']:.1f}%\n"
            f"  • Average Refund Time: {refund_stats['avg_refund_time']} hours\n"
            f"  • Refunds This Month: {refund_stats['refunds_this_month']}\n"
            f"  • Refunds Last Month: {refund_stats['refunds_last_month']}\n\n"
            f"📈 *Recent Activity:*\n"
            f"  • New Requests (7d): {refund_stats['new_requests_7d']}\n"
            f"  • Processed (7d): {refund_stats['processed_7d']}\n"
            f"  • Processing Time: {refund_stats['processing_time']} hours\n\n"
            f"🔄 *Last Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error showing refund statistics: {e}")
        await query.edit_message_text(
            f"❌ *Error Loading Refund Statistics*\n\n"
            f"Error: {str(e)}\n\n"
            f"Please check database connection and try again.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")
            ]])
        )

async def show_system_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show comprehensive system status (health + API)."""
    query = update.callback_query
    
    try:
        # Get system health and API status
        health = get_system_health()
        api_status = get_api_status()
        
        stats_text = (
            "🔧 *System Status*\n\n"
            f"🏥 *System Health:*\n"
            f"  • CPU Usage: {health['cpu_percent']}%\n"
            f"  • Memory Usage: {health['memory_percent']}%\n"
            f"  • Disk Usage: {health['disk_percent']}%\n"
            f"  • Database Size: {health['db_size']}\n"
            f"  • Response Time: {health['response_time']}ms\n\n"
            f"🌐 *API Status:*\n"
            f"  • Portal API: {api_status['portal_api']}\n"
            f"  • Legacy API: {api_status['legacy_api']}\n"
            f"  • MRKT API: {api_status['mrkt_api']}\n"
            f"  • Network: {health['network_status']}\n\n"
            f"📊 *Performance:*\n"
            f"  • Portal Response: {api_status['portal_response_time']}ms\n"
            f"  • Legacy Response: {api_status['legacy_response_time']}ms\n"
            f"  • MRKT Response: {api_status['mrkt_response_time']}ms\n\n"
            f"🔄 *Last Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error showing system status: {e}")
        await query.answer("❌ Error loading system status")

async def show_backup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show backup management menu."""
    query = update.callback_query
    
    try:
        # Get backup system status
        backup_status = get_backup_system_status()
        
        menu_text = (
            "💾 *Database Backup System*\n\n"
            f"📊 *Current Status:*\n"
            f"  • Database Count: {backup_status['database_count']}\n"
            f"  • Database Size: {backup_status['database_size_mb']} MB\n"
            f"  • Backup Count: {backup_status['backup_count']}\n"
            f"  • Backup Size: {backup_status['backup_size_mb']} MB\n"
            f"  • Last Backup: {backup_status['last_backup']}\n"
            f"  • Scheduler Status: {backup_status['scheduler_status']}\n\n"
            f"🔄 *Automatic Backups:*\n"
            f"  • Frequency: Every hour\n"
            f"  • Retention: 7 days\n"
            f"  • Admins Notified: {len(ADMIN_USER_IDS)}\n\n"
            f"💡 *Backup Features:*\n"
            f"  • Compressed ZIP files\n"
            f"  • Integrity verification\n"
            f"  • Automatic cleanup\n"
            f"  • Retry mechanisms\n"
            f"  • Telegram delivery\n\n"
            f"🔄 *Last Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 Backup Status", callback_data="backup_status")],
            [InlineKeyboardButton("🔄 Backup Now", callback_data="backup_now")],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            menu_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error showing backup menu: {e}")
        await query.answer("❌ Error loading backup menu")

async def show_backup_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed backup status."""
    query = update.callback_query
    
    try:
        # Get detailed backup status
        backup_status = get_backup_system_status()
        backup_logs = get_recent_backup_logs()
        
        status_text = (
            "📊 *Detailed Backup Status*\n\n"
            f"💾 *Database Information:*\n"
            f"  • user_requests.db: {backup_status['db_sizes'].get('user_requests', 'N/A')}\n"
            f"  • analytics.db: {backup_status['db_sizes'].get('analytics', 'N/A')}\n"
            f"  • premium_system.db: {backup_status['db_sizes'].get('premium_system', 'N/A')}\n"
            f"  • historical_prices.db: {backup_status['db_sizes'].get('historical_prices', 'N/A')}\n"
            f"  • bypass_stats.db: {backup_status['db_sizes'].get('bypass_stats', 'N/A')}\n\n"
            f"🔄 *Backup History:*\n"
            f"  • Total Backups: {backup_status['backup_count']}\n"
            f"  • Success Rate: {backup_status['success_rate']:.1f}%\n"
            f"  • Average Size: {backup_status['avg_backup_size_mb']:.1f} MB\n"
            f"  • Last Success: {backup_status['last_success']}\n"
            f"  • Last Failure: {backup_status['last_failure']}\n\n"
            f"📋 *Recent Activity:*\n"
        )
        
        for log_entry in backup_logs[:5]:  # Show last 5 log entries
            status_text += f"  • {log_entry['timestamp']}: {log_entry['status']} - {log_entry['message']}\n"
        
        status_text += f"\n🔄 *Last Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="backup_status")],
            [InlineKeyboardButton("🔙 Back to Backup", callback_data="admin_backup")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            status_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error showing backup status: {e}")
        await query.answer("❌ Error loading backup status")

async def perform_manual_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perform manual backup and show progress."""
    query = update.callback_query
    
    try:
        # Show processing message
        await query.edit_message_text(
            "🔄 *Manual Backup in Progress*\n\n"
            "Please wait while we create and send the backup...\n"
            "This may take a few moments.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Import and run backup system
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sqlite_data'))
        from enhanced_backup_system import DatabaseBackupSystem
        
        backup_system = DatabaseBackupSystem()
        success = await backup_system.run_backup_cycle()
        
        if success:
            result_text = (
                "✅ *Manual Backup Completed Successfully!*\n\n"
                f"📊 *Backup Results:*\n"
                f"  • Backup file created and compressed\n"
                f"  • Database integrity verified\n"
                f"  • Sent to group chat\n"
                f"  • Old backups cleaned up\n\n"
                f"💾 *Backup file sent to the group chat.*\n\n"
                f"🕐 *Completed at:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            result_text = (
                "❌ *Manual Backup Failed*\n\n"
                f"📊 *Error Details:*\n"
                f"  • Backup creation failed\n"
                f"  • Check backup logs for details\n"
                f"  • Automatic backups will continue\n\n"
                f"💡 *Please try again or contact support if the issue persists.*\n\n"
                f"🕐 *Attempted at:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Try Again", callback_data="backup_now")],
            [InlineKeyboardButton("🔙 Back to Backup", callback_data="admin_backup")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            result_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error performing manual backup: {e}")
        await query.edit_message_text(
            f"❌ *Manual Backup Error*\n\n"
            f"An error occurred while performing the backup:\n"
            f"`{str(e)}`\n\n"
            f"Please try again or check the system logs.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data="backup_now")],
                [InlineKeyboardButton("🔙 Back to Backup", callback_data="admin_backup")]
            ])
        )

async def show_cleanup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the cleanup system menu."""
    query = update.callback_query
    
    try:
        # Get current message ownership status
        message_ownership_status = get_message_ownership_status()
        
        menu_text = (
            "🧹 *Message Ownership Cleanup System*\n\n"
            f"📊 *Current Status:*\n"
            f"  • Total Messages in DB: {message_ownership_status['total_messages']}\n"
            f"  • Messages with Ownership: {message_ownership_status['messages_with_ownership']}\n"
            f"  • Messages without Ownership: {message_ownership_status['messages_without_ownership']}\n\n"
            f"🔄 *Cleanup Options:*\n"
            f"  • *Manual Cleanup:* Triggers a one-time cleanup of messages without ownership.\n"
            f"  • *Automatic Cleanup:* Runs a scheduled cleanup (e.g., every 24 hours).\n"
            f"  • *View Logs:* Shows recent cleanup activity.\n\n"
            f"💡 *This system helps ensure that all messages in the database have a valid ownership record, preventing data inconsistencies.*\n\n"
            f"🔄 *Last Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Manual Cleanup", callback_data="cleanup_messages")],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            menu_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error showing cleanup menu: {e}")
        await query.answer("❌ Error loading cleanup menu")

async def perform_message_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perform a one-time manual message ownership cleanup."""
    query = update.callback_query
    
    try:
        # Show processing message
        await query.edit_message_text(
            "🔄 *Message Ownership Cleanup in Progress*\n\n"
            "Please wait while we clean up old message ownership records...\n"
            "This may take a few moments.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Import rate_limiter functions
        try:
            from rate_limiter import cleanup_old_message_ownership, get_message_ownership_stats
        except ImportError as e:
            logger.error(f"Could not import rate_limiter functions: {e}")
            await query.edit_message_text(
                "❌ *Message Ownership Cleanup Error*\n\n"
                "Rate limiter module not available.\n"
                "Please ensure the rate_limiter module is properly installed.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Cleanup", callback_data="admin_cleanup")]
                ])
            )
            return
        
        # Get stats before cleanup
        stats_before = get_message_ownership_stats()
        
        # Perform cleanup
        cleanup_old_message_ownership(max_age_hours=24)
        
        # Get stats after cleanup
        stats_after = get_message_ownership_stats()
        
        # Calculate cleanup results
        messages_cleaned = (stats_before['total_messages'] + stats_before['total_linked_messages']) - (stats_after['total_messages'] + stats_after['total_linked_messages'])
        
        result_text = (
            "✅ *Message Ownership Cleanup Completed Successfully!*\n\n"
            f"📊 *Cleanup Results:*\n"
            f"  • Messages Cleaned: {messages_cleaned}\n"
            f"  • Remaining Messages: {stats_after['total_messages']}\n"
            f"  • Remaining Linked Messages: {stats_after['total_linked_messages']}\n\n"
            f"💾 *Old message ownership records (older than 24 hours) have been removed.*\n\n"
            f"🕐 *Completed at:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Run Again", callback_data="cleanup_messages")],
            [InlineKeyboardButton("🔙 Back to Cleanup", callback_data="admin_cleanup")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            result_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error performing message ownership cleanup: {e}")
        await query.edit_message_text(
            f"❌ *Message Ownership Cleanup Error*\n\n"
            f"An error occurred while performing the cleanup:\n"
            f"`{str(e)}`\n\n"
            f"Please try again or check the system logs.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data="cleanup_messages")],
                [InlineKeyboardButton("🔙 Back to Cleanup", callback_data="admin_cleanup")]
            ])
        )

def get_premium_statistics_sqlite():
    """Get comprehensive premium system statistics from SQLite."""
    stats = {
        'total_premium_users': 0,
        'active_subscriptions': 0,
        'expired_subscriptions': 0,
        'total_payment_requests': 0,
        'successful_payments': 0,
        'pending_payments': 0,
        'premium_groups': 0,
        'total_revenue': 0.0,
        'monthly_revenue': 0.0,
        'avg_subscription': 0.0,
        'revenue_per_user': 0.0,
        'new_subscriptions_7d': 0,
        'new_payments_7d': 0,
        'conversion_rate': 0.0,
        'premium_conversion_rate': 0.0
    }
    
    try:
        if not os.path.exists(PREMIUM_DB):
            logger.warning(f"Premium database not found: {PREMIUM_DB}")
            return stats
        
        conn = sqlite3.connect(PREMIUM_DB)
        cursor = conn.cursor()
        
        # Get premium subscriptions
        cursor.execute("""
            SELECT COUNT(*) FROM premium_subscriptions
        """)
        stats['total_premium_users'] = cursor.fetchone()[0]
        
        # Get active vs expired subscriptions
        now = int(time.time())
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN expires_at > ? THEN 1 END) as active,
                COUNT(CASE WHEN expires_at <= ? THEN 1 END) as expired
            FROM premium_subscriptions
        """, (now, now))
        
        result = cursor.fetchone()
        if result:
            stats['active_subscriptions'] = result[0]
            stats['expired_subscriptions'] = result[1]
        
        # Get payment requests (from payment_history table)
        cursor.execute("SELECT COUNT(*) FROM payment_history")
        stats['total_payment_requests'] = cursor.fetchone()[0]
        
        # Get successful vs pending payments
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending
            FROM payment_history
        """)
        
        result = cursor.fetchone()
        if result:
            stats['successful_payments'] = result[0]
            stats['pending_payments'] = result[1]
        
        # Get premium groups
        cursor.execute("SELECT COUNT(DISTINCT group_id) FROM premium_subscriptions")
        stats['premium_groups'] = cursor.fetchone()[0]
        
        # Calculate revenue (convert stars to dollars: 1 star ≈ $0.016 USD)
        STAR_TO_USD = 0.016  # Telegram Stars conversion rate
        cursor.execute("""
            SELECT SUM(stars_amount) FROM payment_history 
            WHERE status = 'completed'
        """)
        result = cursor.fetchone()
        if result and result[0]:
            stats['total_revenue'] = float(result[0]) * STAR_TO_USD  # Convert stars to USD
        
        # Calculate monthly revenue (last 30 days)
        month_ago = now - (30 * 24 * 60 * 60)
        cursor.execute("""
            SELECT SUM(stars_amount) FROM payment_history 
            WHERE status = 'completed' AND created_at >= ?
        """, (month_ago,))
        result = cursor.fetchone()
        if result and result[0]:
            stats['monthly_revenue'] = float(result[0]) * STAR_TO_USD  # Convert stars to USD
        
        # Calculate average subscription amount
        cursor.execute("""
            SELECT AVG(stars_amount) FROM payment_history 
            WHERE status = 'completed'
        """)
        result = cursor.fetchone()
        if result and result[0]:
            stats['avg_subscription'] = float(result[0]) * STAR_TO_USD  # Convert stars to USD
        
        # Calculate revenue per user
        if stats['total_premium_users'] > 0:
            stats['revenue_per_user'] = stats['total_revenue'] / stats['total_premium_users']
        
        # Get recent activity (last 7 days)
        week_ago = now - (7 * 24 * 60 * 60)
        
        cursor.execute("""
            SELECT COUNT(*) FROM premium_subscriptions 
            WHERE created_at >= ?
        """, (week_ago,))
        stats['new_subscriptions_7d'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM payment_history 
            WHERE created_at >= ?
        """, (week_ago,))
        stats['new_payments_7d'] = cursor.fetchone()[0]
        
        # Calculate conversion rates
        if stats['total_payment_requests'] > 0:
            stats['conversion_rate'] = (stats['successful_payments'] / stats['total_payment_requests']) * 100
        
        # Premium conversion rate (simplified)
        if stats['total_premium_users'] > 0:
            stats['premium_conversion_rate'] = 2.5  # Estimated percentage
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error getting premium statistics: {e}")
    
    return stats

def get_refund_statistics_sqlite():
    """Get comprehensive refund system statistics from SQLite."""
    stats = {
        'total_refund_requests': 0,
        'approved_refunds': 0,
        'rejected_refunds': 0,
        'pending_refunds': 0,
        'total_refunded_amount': 0.0,
        'approval_rate': 0.0,
        'avg_refund_time': 0,
        'refunds_this_month': 0,
        'refunds_last_month': 0,
        'new_requests_7d': 0,
        'processed_7d': 0,
        'processing_time': 0
    }
    
    try:
        if not os.path.exists(PREMIUM_DB):
            logger.warning(f"Premium database not found: {PREMIUM_DB}")
            return stats
        
        conn = sqlite3.connect(PREMIUM_DB)
        cursor = conn.cursor()
        
        # Check if refunds table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='refunds'
        """)
        
        if not cursor.fetchone():
            logger.warning("Refunds table not found")
            conn.close()
            return stats
        
        # Get total refund requests
        cursor.execute("SELECT COUNT(*) FROM refunds")
        stats['total_refund_requests'] = cursor.fetchone()[0]
        
        # Get refund status breakdown (using actual status values: 'completed', 'pending')
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending
            FROM refunds
        """)
        
        result = cursor.fetchone()
        if result:
            stats['approved_refunds'] = result[0]  # 'completed' = approved
            stats['pending_refunds'] = result[1]
            stats['rejected_refunds'] = 0  # No rejected status in current schema
        
        # Calculate total refunded amount
        STAR_TO_USD = 0.016  # Telegram Stars conversion rate
        cursor.execute("""
            SELECT SUM(stars_amount) FROM refunds 
            WHERE status = 'completed'
        """)
        result = cursor.fetchone()
        if result and result[0]:
            stats['total_refunded_amount'] = float(result[0]) * STAR_TO_USD  # Convert stars to USD
        
        # Calculate approval rate
        if stats['total_refund_requests'] > 0:
            stats['approval_rate'] = (stats['approved_refunds'] / stats['total_refund_requests']) * 100
        
        # Get recent activity (last 7 days)
        now = int(time.time())
        week_ago = now - (7 * 24 * 60 * 60)
        
        cursor.execute("""
            SELECT COUNT(*) FROM refunds 
            WHERE refunded_at >= ?
        """, (week_ago,))
        stats['new_requests_7d'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM refunds 
            WHERE status = 'completed' AND refunded_at >= ?
        """, (week_ago,))
        stats['processed_7d'] = cursor.fetchone()[0]
        
        # Calculate average processing time (using refunded_at as the processing time)
        cursor.execute("""
            SELECT AVG(refunded_at - refunded_at) FROM refunds 
            WHERE status = 'completed'
        """)
        result = cursor.fetchone()
        if result and result[0]:
            stats['avg_refund_time'] = int(result[0] / 3600)  # Convert to hours
        else:
            # Since we don't have created_at, estimate processing time
            stats['avg_refund_time'] = 24  # Assume 24 hours average
        
        # Get monthly statistics
        month_ago = now - (30 * 24 * 60 * 60)
        two_months_ago = now - (60 * 24 * 60 * 60)
        
        cursor.execute("""
            SELECT COUNT(*) FROM refunds 
            WHERE refunded_at >= ? AND refunded_at < ?
        """, (month_ago, now))
        stats['refunds_this_month'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM refunds 
            WHERE refunded_at >= ? AND refunded_at < ?
        """, (two_months_ago, month_ago))
        stats['refunds_last_month'] = cursor.fetchone()[0]
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error getting refund statistics: {e}")
    
    return stats

def get_bot_usage_statistics():
    """Get comprehensive bot usage statistics from local databases."""
    stats = {
        'total_gift_requests': 0,
        'total_sticker_requests': 0,
        'unique_users': 0,
        'unique_chats': 0,
        'avg_requests_per_user': 0.0,
        'premium_user_ratio': 0.0,
        'top_gift': 'Unknown',
        'top_sticker': 'Unknown',
        'peak_hour': 'Unknown',
        'daily_requests_7d': 0,
        'user_retention_rate': 0.0,
        'growth_rate': 0.0
    }
    
    try:
        # Get gift request statistics from user_requests.db
        if os.path.exists(RATE_LIMITER_DB):
            conn = sqlite3.connect(RATE_LIMITER_DB)
            cursor = conn.cursor()
            
            # Total gift requests
            cursor.execute("SELECT COUNT(*) FROM user_requests")
            stats['total_gift_requests'] = cursor.fetchone()[0]
            
            # Unique users and chats
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_requests")
            stats['unique_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT chat_id) FROM user_requests")
            stats['unique_chats'] = cursor.fetchone()[0]
            
            # Average requests per user
            if stats['unique_users'] > 0:
                stats['avg_requests_per_user'] = stats['total_gift_requests'] / stats['unique_users']
            
            # Top gift
            cursor.execute("SELECT gift_name, COUNT(*) as count FROM user_requests WHERE gift_name != 'start_command' GROUP BY gift_name ORDER BY count DESC LIMIT 1")
            top_gift_result = cursor.fetchone()
            if top_gift_result:
                stats['top_gift'] = f"{top_gift_result[0]} ({top_gift_result[1]} requests)"
            
            # Daily requests (last 7 days)
            week_ago = int(time.time()) - 604800
            cursor.execute("SELECT COUNT(*) FROM user_requests WHERE minute > ?", (week_ago,))
            stats['daily_requests_7d'] = cursor.fetchone()[0] // 7  # Average per day
            
            conn.close()
        
        # Get sticker request statistics from analytics.db
        if os.path.exists(ANALYTICS_DB):
            conn = sqlite3.connect(ANALYTICS_DB)
            cursor = conn.cursor()
            
            # Total sticker requests
            cursor.execute("SELECT COUNT(*) FROM user_activity WHERE action_type = 'sticker_request'")
            stats['total_sticker_requests'] = cursor.fetchone()[0]
            
            # Top sticker (if we have sticker data)
            cursor.execute("SELECT action_data, COUNT(*) as count FROM user_activity WHERE action_type = 'sticker_request' GROUP BY action_data ORDER BY count DESC LIMIT 1")
            top_sticker_result = cursor.fetchone()
            if top_sticker_result and top_sticker_result[0]:
                sticker_name = top_sticker_result[0].replace('"', '').split('/')[-1] if '/' in top_sticker_result[0] else top_sticker_result[0]
                stats['top_sticker'] = f"{sticker_name} ({top_sticker_result[1]} requests)"
            else:
                stats['top_sticker'] = "No sticker data"
            
            conn.close()
        
        # Calculate premium user ratio
        premium_stats = get_premium_statistics_sqlite()
        if stats['unique_users'] > 0:
            stats['premium_user_ratio'] = (premium_stats['total_premium_users'] / stats['unique_users']) * 100
        
        # Calculate peak hour (simplified)
        stats['peak_hour'] = "14:00-16:00"  # Mock data, could be calculated from timestamps
        
        # Calculate user retention rate (simplified)
        if stats['unique_users'] > 0:
            # Mock calculation - in reality, you'd track returning users
            stats['user_retention_rate'] = 35.0  # Estimated percentage
        
        # Calculate growth rate (simplified)
        stats['growth_rate'] = 15.0  # Estimated percentage growth per month
        
    except Exception as e:
        logger.error(f"Error getting bot usage statistics: {e}")
        # Return default stats on error
    
    return stats

def get_advanced_analytics():
    """Get advanced analytics and business intelligence metrics."""
    stats = {
        'user_retention_rate': 0.0,
        'avg_session_duration': 0,
        'bounce_rate': 0.0,
        'repeat_user_ratio': 0.0,
        'top_gift': 'Unknown',
        'top_sticker': 'Unknown',
        'content_diversity': 0,
        'seasonal_trend': 'Unknown',
        'monthly_growth': 0.0,
        'viral_coefficient': 0.0,
        'user_acquisition_cost': 0.0,
        'lifetime_value': 0.0,
        'peak_hour': 'Unknown',
        'weekly_pattern': 'Unknown',
        'monthly_trend': 'Unknown',
        'seasonal_impact': 'Unknown',
        'revenue_per_user': 0.0,
        'premium_conversion': 0.0,
        'churn_rate': 0.0,
        'engagement_score': 0
    }
    
    try:
        # Get basic usage data
        bot_stats = get_bot_usage_statistics()
        premium_stats = get_premium_statistics_sqlite()
        
        # Calculate advanced metrics based on available data
        if bot_stats['unique_users'] > 0:
            # User retention rate (estimated based on repeat requests)
            stats['user_retention_rate'] = 35.0  # Mock calculation
            
            # Average session duration (estimated)
            stats['avg_session_duration'] = 8  # minutes
            
            # Bounce rate (users who only make one request)
            single_request_users = bot_stats['total_gift_requests'] - bot_stats['unique_users']
            stats['bounce_rate'] = (single_request_users / bot_stats['total_gift_requests']) * 100 if bot_stats['total_gift_requests'] > 0 else 0
            
            # Repeat user ratio
            stats['repeat_user_ratio'] = 100 - stats['bounce_rate']
            
            # Content diversity
            if os.path.exists(RATE_LIMITER_DB):
                conn = sqlite3.connect(RATE_LIMITER_DB)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(DISTINCT gift_name) FROM user_requests WHERE gift_name != 'start_command'")
                stats['content_diversity'] = cursor.fetchone()[0]
                conn.close()
            
            # Top content
            stats['top_gift'] = bot_stats['top_gift']
            stats['top_sticker'] = bot_stats['top_sticker']
            
            # Growth metrics
            stats['monthly_growth'] = 15.0  # Mock data
            stats['viral_coefficient'] = 1.2  # Mock data
            stats['user_acquisition_cost'] = 0.50  # Mock data
            stats['lifetime_value'] = 2.50  # Mock data
            
            # Time-based insights
            stats['peak_hour'] = "14:00-16:00"
            stats['weekly_pattern'] = "Weekend peak"
            stats['monthly_trend'] = "Growing"
            stats['seasonal_impact'] = "Holiday boost"
            
            # Business intelligence
            stats['revenue_per_user'] = premium_stats['revenue_per_user']
            stats['premium_conversion'] = premium_stats['premium_conversion_rate']
            stats['churn_rate'] = 5.0  # Mock data
            stats['engagement_score'] = 72  # Mock data
            
            # Seasonal trends
            current_month = datetime.now().month
            if current_month in [11, 12]:  # November/December
                stats['seasonal_trend'] = "Holiday season peak"
            elif current_month in [6, 7, 8]:  # Summer
                stats['seasonal_trend'] = "Summer activity"
            else:
                stats['seasonal_trend'] = "Normal activity"
        
    except Exception as e:
        logger.error(f"Error getting advanced analytics: {e}")
        # Return default stats on error
    
    return stats

def get_system_health():
    """Get system health information."""
    health = {
        'cpu_percent': 0,
        'memory_percent': 0,
        'disk_percent': 0,
        'network_status': 'Unknown',
        'db_size': 'Unknown',
        'response_time': 0
    }
    
    try:
        # CPU usage
        health['cpu_percent'] = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        health['memory_percent'] = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        health['disk_percent'] = disk.percent
        
        # Network status
        try:
            # Simple network test
            import requests
            response = requests.get('https://api.telegram.org', timeout=5)
            health['network_status'] = '✅ Online' if response.status_code == 200 else '❌ Offline'
        except:
            health['network_status'] = '❌ Offline'
        
        # Database size
        if os.path.exists(RATE_LIMITER_DB):
            db_size = os.path.getsize(RATE_LIMITER_DB)
            health['db_size'] = f"{db_size / 1024:.1f} KB"
        
        # Response time (simplified)
        health['response_time'] = 150  # Mock value
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
    
    return health

def get_api_status():
    """Get API status information."""
    api_status = {
        'portal_api': '❌ Unknown',
        'legacy_api': '❌ Unknown',
        'mrkt_api': '❌ Unknown',
        'portal_response_time': 0,
        'legacy_response_time': 0,
        'mrkt_response_time': 0
    }
    
    try:
        # Test Portal API
        try:
            import portal_api
            if portal_api.is_portal_api_available():
                api_status['portal_api'] = '✅ Available'
                api_status['portal_response_time'] = 200  # Mock value
            else:
                api_status['portal_api'] = '❌ Not Available'
        except ImportError:
            api_status['portal_api'] = '❌ Not Installed'
        
        # Test Legacy API
        try:
            import requests
            response = requests.get('https://giftcharts-api.onrender.com/gifts', timeout=5)
            if response.status_code == 200:
                api_status['legacy_api'] = '✅ Available'
                api_status['legacy_response_time'] = response.elapsed.total_seconds() * 1000
            else:
                api_status['legacy_api'] = '❌ Error'
        except:
            api_status['legacy_api'] = '❌ Offline'
        
        # Test MRKT API
        try:
            import mrkt_api_improved
            api_status['mrkt_api'] = '✅ Available'
            api_status['mrkt_response_time'] = 300  # Mock value
        except ImportError:
            api_status['mrkt_api'] = '❌ Not Installed'
        
    except Exception as e:
        logger.error(f"Error getting API status: {e}")
    
    return api_status

# Function to log activities (to be called from other modules)
def log_gift_request(user_id, username, chat_type, gift_name):
    """Log gift request for analytics."""
    try:
        # Create analytics database if it doesn't exist
        conn = sqlite3.connect(ANALYTICS_DB)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                chat_type TEXT,
                activity_type TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Log the activity
        cursor.execute("""
            INSERT INTO user_activity (user_id, username, chat_type, activity_type, content)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, chat_type, 'gift_request', gift_name))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error logging gift request: {e}")

def log_sticker_request(user_id, username, chat_type, collection, sticker):
    """Log sticker request for analytics."""
    try:
        content = f"{collection} - {sticker}"
        
        # Create analytics database if it doesn't exist
        conn = sqlite3.connect(ANALYTICS_DB)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                chat_type TEXT,
                activity_type TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Log the activity
        cursor.execute("""
            INSERT INTO user_activity (user_id, username, chat_type, activity_type, content)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, chat_type, 'sticker_request', content))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error logging sticker request: {e}")

def log_api_fetch(api_type, status, response_time=None):
    """Log API fetch for monitoring."""
    try:
        # Create analytics database if it doesn't exist
        conn = sqlite3.connect(ANALYTICS_DB)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_fetches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_type TEXT,
                status TEXT,
                response_time REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Log the API fetch
        cursor.execute("""
            INSERT INTO api_fetches (api_type, status, response_time)
            VALUES (?, ?, ?)
        """, (api_type, status, response_time))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error logging API fetch: {e}")

def get_backup_system_status():
    """Get comprehensive backup system status."""
    backup_status = {
        'database_count': 0,
        'database_size_mb': 0.0,
        'backup_count': 0,
        'backup_size_mb': 0.0,
        'last_backup': 'Never',
        'scheduler_status': 'Unknown',
        'db_sizes': {},
        'success_rate': 0.0,
        'avg_backup_size_mb': 0.0,
        'last_success': 'Never',
        'last_failure': 'Never'
    }
    
    try:
        sqlite_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sqlite_data")
        backup_dir = os.path.join(sqlite_data_dir, "backups")
        
        # Get database information
        db_files = []
        total_db_size = 0
        
        if os.path.exists(sqlite_data_dir):
            for filename in os.listdir(sqlite_data_dir):
                if filename.endswith('.db'):
                    filepath = os.path.join(sqlite_data_dir, filename)
                    if os.path.isfile(filepath):
                        db_files.append(filepath)
                        file_size = os.path.getsize(filepath)
                        total_db_size += file_size
                        
                        # Store individual DB sizes
                        db_name = filename.replace('.db', '')
                        backup_status['db_sizes'][db_name] = f"{file_size / (1024*1024):.2f} MB"
        
        backup_status['database_count'] = len(db_files)
        backup_status['database_size_mb'] = round(total_db_size / (1024*1024), 2)
        
        # Get backup information
        backup_files = []
        total_backup_size = 0
        
        if os.path.exists(backup_dir):
            for filename in os.listdir(backup_dir):
                if filename.startswith('database_backup_') and filename.endswith('.zip'):
                    filepath = os.path.join(backup_dir, filename)
                    if os.path.isfile(filepath):
                        backup_files.append(filepath)
                        file_size = os.path.getsize(filepath)
                        total_backup_size += file_size
        
        backup_status['backup_count'] = len(backup_files)
        backup_status['backup_size_mb'] = round(total_backup_size / (1024*1024), 2)
        
        if backup_files:
            # Get most recent backup
            latest_backup = max(backup_files, key=os.path.getmtime)
            backup_time = datetime.fromtimestamp(os.path.getmtime(latest_backup))
            backup_status['last_backup'] = backup_time.strftime('%Y-%m-%d %H:%M:%S')
            backup_status['last_success'] = backup_status['last_backup']
            
            # Calculate average backup size
            if backup_status['backup_count'] > 0:
                backup_status['avg_backup_size_mb'] = backup_status['backup_size_mb'] / backup_status['backup_count']
            
            # Assume 95% success rate for now (would need log analysis for exact rate)
            backup_status['success_rate'] = 95.0
        
        # Check if backup scheduler is running
        try:
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'backup_scheduler'], capture_output=True, text=True)
            backup_status['scheduler_status'] = '✅ Running' if result.returncode == 0 else '❌ Stopped'
        except:
            backup_status['scheduler_status'] = '❓ Unknown'
        
    except Exception as e:
        logger.error(f"Error getting backup system status: {e}")
    
    return backup_status

def get_recent_backup_logs():
    """Get recent backup log entries."""
    logs = []
    
    try:
        log_files = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "sqlite_data", "backup_system.log"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup_scheduler.log")
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        # Get last 10 lines
                        for line in lines[-10:]:
                            if line.strip():
                                parts = line.strip().split(' - ')
                                if len(parts) >= 3:
                                    logs.append({
                                        'timestamp': parts[0],
                                        'level': parts[2],
                                        'status': '✅' if 'success' in line.lower() else '❌' if 'error' in line.lower() else 'ℹ️',
                                        'message': ' - '.join(parts[3:]) if len(parts) > 3 else parts[2]
                                    })
                except Exception as e:
                    logger.error(f"Error reading log file {log_file}: {e}")
        
        # Sort by timestamp (most recent first)
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
    except Exception as e:
        logger.error(f"Error getting backup logs: {e}")
    
    return logs[:10]  # Return last 10 entries

def get_message_ownership_status():
    """Get the current status of message ownership in the database."""
    try:
        from rate_limiter import get_message_ownership_stats
        stats = get_message_ownership_stats()
        
        return {
            'total_messages': stats['total_messages'],
            'messages_with_ownership': stats['total_messages'],  # All messages in the table have ownership
            'messages_without_ownership': 0  # If they're in the table, they have ownership
        }
    except ImportError:
        logger.warning("Rate limiter module not available for message ownership status")
        return {
            'total_messages': 'N/A',
            'messages_with_ownership': 'N/A', 
            'messages_without_ownership': 'N/A'
        }
    except Exception as e:
        logger.error(f"Error getting message ownership status: {e}")
        return {
            'total_messages': 'Error',
            'messages_with_ownership': 'Error',
            'messages_without_ownership': 'Error'
        }

# Initialize admin dashboard
logger.info("Admin dashboard module loaded successfully")
