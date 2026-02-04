# 🔄 Supabase Backup System Guide

## Overview

Your bot uses a **hybrid database architecture**:
- **Primary Database**: SQLite (fast, local, production)
- **Backup Database**: Supabase (cloud, disaster recovery)

Every 6 hours, your SQLite data automatically syncs to Supabase as a cloud backup.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GiftsChart Bot                        │
│                                                          │
│  ┌──────────────┐         ┌──────────────┐             │
│  │   SQLite     │         │   Supabase   │             │
│  │  (Primary)   │ ──────> │   (Backup)   │             │
│  │              │  Sync   │              │             │
│  │  • Fast      │  Every  │  • Cloud     │             │
│  │  • Local     │  6 hrs  │  • Recovery  │             │
│  │  • 1200+     │         │  • Analytics │             │
│  │    users     │         │              │             │
│  └──────────────┘         └──────────────┘             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Benefits

✅ **Fast Performance**: SQLite for real-time operations  
✅ **Cloud Backup**: Automatic Supabase sync every 6 hours  
✅ **Disaster Recovery**: Restore from cloud if server crashes  
✅ **Zero Downtime**: Backup runs in background  
✅ **Analytics Ready**: Query Supabase for insights  

## Setup Instructions

### Step 1: Reset Supabase Password (CRITICAL)

⚠️ **Your password was exposed publicly - MUST reset it!**

1. Go to: https://supabase.com/dashboard/project/fmfijzvsfaimrizzipfu/settings/database
2. Click "Reset Database Password"
3. Generate a new strong password
4. Copy the new password

### Step 2: Update .env File

Edit `GiftsChart-ALL/.env` and update:

```bash
# Supabase Configuration
SUPABASE_URL=https://fmfijzvsfaimrizzipfu.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_DB_HOST=aws-1-us-east-2.pooler.supabase.com
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres.fmfijzvsfaimrizzipfu
SUPABASE_DB_PASSWORD=YOUR_NEW_PASSWORD_HERE
```

Replace `YOUR_NEW_PASSWORD_HERE` with the password from Step 1.

### Step 3: Install Dependencies

```bash
cd GiftsChart-ALL
pip install psycopg2-binary
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### Step 4: Test Supabase Connection

```bash
python3 setup_supabase.py
```

Expected output:
```
✅ Supabase configuration found
✅ Connection successful!
✅ All tables created!
🎉 Supabase Setup Complete!
```

### Step 5: Run Initial Backup

```bash
python3 schedulers/supabase_backup_sync.py
```

This will sync your current SQLite data to Supabase.

### Step 6: Start Automatic Backup Scheduler

```bash
# Run in background with nohup
nohup python3 schedulers/run_supabase_backup.py > supabase_backup.log 2>&1 &

# Or use screen/tmux for better control
screen -S supabase_backup
python3 schedulers/run_supabase_backup.py
# Press Ctrl+A then D to detach
```

## Usage

### Check Backup Status

```bash
# View backup logs
tail -f supabase_backup.log

# Check if scheduler is running
ps aux | grep run_supabase_backup
```

### Manual Backup

Run a backup anytime:
```bash
python3 schedulers/supabase_backup_sync.py
```

### Restore from Supabase

⚠️ **WARNING: This overwrites your local SQLite databases!**

```bash
python3 restore_from_supabase.py
```

The script will:
1. Backup your current SQLite files
2. Download data from Supabase
3. Overwrite local databases
4. Prompt for confirmation

## Files Overview

| File | Purpose |
|------|---------|
| `schedulers/supabase_backup_sync.py` | One-time backup sync script |
| `schedulers/run_supabase_backup.py` | Automatic scheduler (every 6 hours) |
| `restore_from_supabase.py` | Emergency restore from cloud |
| `core/supabase_client.py` | Supabase connection manager |
| `setup_supabase.py` | Initial setup and testing |

## Database Tables Synced

### Premium Database (`premium_system.db`)
- `premium_subscriptions` - Active premium groups
- `payment_history` - Payment records
- `refunds` - Refund requests
- `refunded_groups` - Groups that got refunds

### User Requests Database (`user_requests.db`)
- `user_requests` - Rate limiting for gifts
- `command_requests` - Rate limiting for commands
- `message_owners` - Message ownership tracking

## Backup Schedule

- **Frequency**: Every 6 hours
- **First Run**: Immediately when scheduler starts
- **Next Runs**: 6, 12, 18, 24 hours, etc.

Example schedule:
```
00:00 - Initial backup
06:00 - Automatic backup
12:00 - Automatic backup
18:00 - Automatic backup
00:00 - Automatic backup (next day)
```

## Monitoring

### Check Last Backup Time

```bash
# View scheduler logs
tail -20 supabase_backup.log
```

Look for:
```
✅ Backup sync completed successfully!
Last Sync: 2026-02-03 12:00:00
```

### Verify Data in Supabase

1. Go to: https://supabase.com/dashboard/project/fmfijzvsfaimrizzipfu
2. Click "Table Editor"
3. Check tables: `premium_subscriptions`, `user_requests`, etc.

## Troubleshooting

### Connection Failed

**Error**: `❌ Supabase connection test failed`

**Solutions**:
1. Check if password was reset correctly
2. Verify `.env` has correct credentials
3. Check network/firewall settings
4. Ensure Supabase project is not paused

### psycopg2 Not Installed

**Error**: `❌ psycopg2 not installed`

**Solution**:
```bash
pip install psycopg2-binary
```

### Backup Scheduler Not Running

**Check**:
```bash
ps aux | grep run_supabase_backup
```

**Restart**:
```bash
# Kill old process
pkill -f run_supabase_backup

# Start new one
nohup python3 schedulers/run_supabase_backup.py > supabase_backup.log 2>&1 &
```

### Tables Not Created

**Error**: `❌ Failed to create table`

**Solution**:
```bash
# Re-run setup
python3 setup_supabase.py
```

## Production Deployment

### Recommended Setup

1. **Bot Process**: Main bot running
2. **Backup Scheduler**: Automatic Supabase sync every 6 hours
3. **Monitoring**: Check logs daily

### Using PM2 (Recommended)

```bash
# Install PM2
npm install -g pm2

# Start bot
pm2 start core/telegram_bot.py --name giftschart-bot --interpreter python3

# Start backup scheduler
pm2 start schedulers/run_supabase_backup.py --name supabase-backup --interpreter python3

# Save configuration
pm2 save

# Auto-start on reboot
pm2 startup
```

### Using systemd

Create `/etc/systemd/system/supabase-backup.service`:

```ini
[Unit]
Description=GiftsChart Supabase Backup Scheduler
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/GiftsChart-ALL
ExecStart=/usr/bin/python3 schedulers/run_supabase_backup.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable supabase-backup
sudo systemctl start supabase-backup
sudo systemctl status supabase-backup
```

## Security Notes

🔒 **Never commit `.env` to Git**  
🔒 **Reset Supabase password immediately**  
🔒 **Use strong passwords (20+ characters)**  
🔒 **Restrict Supabase access to your IP if possible**  

## FAQ

**Q: Will backups slow down my bot?**  
A: No! Backups run in a separate process and don't affect bot performance.

**Q: How much does Supabase cost?**  
A: Free tier includes 500MB database + 2GB bandwidth. More than enough for this bot.

**Q: Can I change backup frequency?**  
A: Yes! Edit `schedulers/run_supabase_backup.py` and change `schedule.every(6).hours` to your preferred interval.

**Q: What if Supabase is down?**  
A: Your bot keeps working! SQLite is the primary database. Supabase is just backup.

**Q: Can I use Supabase for analytics?**  
A: Yes! Connect any SQL client to Supabase and run queries on your data.

## Support

If you encounter issues:
1. Check logs: `tail -f supabase_backup.log`
2. Verify credentials in `.env`
3. Test connection: `python3 setup_supabase.py`
4. Check Supabase dashboard for errors

---

**System Status**: ✅ Production Ready  
**Architecture**: Hybrid (SQLite + Supabase)  
**Backup Frequency**: Every 6 hours  
**Users Supported**: 1200+  
