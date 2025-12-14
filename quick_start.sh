#!/bin/bash
# GiftsChart Bot - Quick Start Script
# This script automates the setup process

set -e  # Exit on error

echo "=========================================="
echo "🎁 GiftsChart Bot - Quick Start"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed!"
    echo "Please install pip"
    exit 1
fi

echo "✅ pip found"
echo ""

# Step 1: Install dependencies
echo "📦 Step 1: Installing dependencies..."
echo "This may take a few minutes..."
echo ""

if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
else
    pip install -r requirements.txt
fi

echo ""
echo "✅ Dependencies installed"
echo ""

# Step 2: Check .env file
echo "🔍 Step 2: Checking .env file..."
echo ""

if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo ""
    echo "Please create .env file with:"
    echo "  TELEGRAM_BOT_TOKEN=your_bot_token"
    echo "  PORTAL_API_ID=22307634"
    echo "  PORTAL_API_HASH=your_api_hash"
    echo "  TELEGRAM_API_ID=22307634"
    echo "  TELEGRAM_API_HASH=your_api_hash"
    echo ""
    exit 1
fi

echo "✅ .env file found"
echo ""

# Step 3: Check Portal authentication
echo "🔐 Step 3: Checking Portal authentication..."
echo ""

if [ ! -f "portal_session_string.txt" ] && [ ! -f "account.session" ]; then
    echo "⚠️  Portal authentication not setup!"
    echo ""
    echo "You need to setup Portal API authentication."
    echo "This requires your Telegram phone number and verification code."
    echo ""
    read -p "Setup now? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 setup_portal_auth.py
    else
        echo ""
        echo "❌ Cannot start without Portal authentication"
        echo "Run manually: python3 setup_portal_auth.py"
        exit 1
    fi
else
    echo "✅ Portal authentication found"
fi

echo ""

# Step 4: Run health check
echo "🔬 Step 4: Running system health check..."
echo ""

python3 check_system.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Health check failed!"
    echo "Please fix the issues above before starting"
    exit 1
fi

echo ""
echo "=========================================="
echo "🎉 Setup Complete!"
echo "=========================================="
echo ""
echo "The bot is ready to start."
echo ""
echo "Start the bot with:"
echo "  python3 core/telegram_bot.py"
echo ""
echo "Or use Docker:"
echo "  docker-compose up -d"
echo ""
echo "Monitor logs:"
echo "  tail -f data/logs/telegram_bot.log"
echo ""
echo "=========================================="
echo ""

# Ask if user wants to start the bot now
read -p "Start the bot now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting bot..."
    echo ""
    python3 core/telegram_bot.py
fi
