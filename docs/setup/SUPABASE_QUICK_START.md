# 🚀 Supabase Backup - Quick Start

## 5-Minute Setup

### 1. Reset Password (CRITICAL!)
```
https://supabase.com/dashboard/project/fmfijzvsfaimrizzipfu/settings/database
→ Click "Reset Database Password"
→ Copy new password
```

### 2. Update .env
```bash
nano GiftsChart-ALL/.env
```

Change this line:
```
SUPABASE_DB_PASSWORD=YOUR_NEW_PASSWORD_HERE
```

### 3. Install Dependencies
```bash
cd GiftsChart-ALL
pip install psycopg2-binary
```

### 4. Test Connection
```bash
python3 test_supabase_backup.py
```

Expected: `🎉 All Tests Passed!`

### 5. Run Initial Backup
```bash
python3 schedulers/supabase_backup_sync.py
```

### 6. Start Auto-Backup (Every 6 Hours)
```bash
nohup python3 schedulers/run_supabase_backup.py > supabase_backup.log 2>&1 &
```

## Done! ✅

Your bot now has:
- ⚡ Fast SQLite (primary)
- ☁️ Cloud backup every 6 hours
- 🔒 Disaster recovery ready

## Quick Commands

```bash
# Check backup status
tail -f supabase_backup.log

# Manual backup
python3 schedulers/supabase_backup_sync.py

# Restore from cloud (CAREFUL!)
python3 restore_from_supabase.py

# Check if scheduler is running
ps aux | grep run_supabase_backup
```

## Troubleshooting

**Connection failed?**
- Reset password again
- Check `.env` file
- Verify network connection

**psycopg2 error?**
```bash
pip install psycopg2-binary
```

**Need help?**
Read full guide: `SUPABASE_BACKUP_GUIDE.md`

---

**Architecture**: SQLite (primary) + Supabase (backup)  
**Backup Frequency**: Every 6 hours  
**Zero Downtime**: Runs in background  
