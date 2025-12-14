"""Configuration for Quant Marketplace API"""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram credentials
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'quantom_session')

# Quant Marketplace settings
BOT_USERNAME = 'QuantMarketRobot'
API_BASE = 'https://quant-marketplace.com'
GIFTS_ENDPOINT = '/api/gifts/gifts'
