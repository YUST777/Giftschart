"""API client for Quant Marketplace"""

import cloudscraper
from config import API_BASE, GIFTS_ENDPOINT


class QuantAPI:
    """Quant Marketplace API client"""
    
    def __init__(self, init_data):
        """Initialize API client with authentication data"""
        self.init_data = init_data
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'ios',
                'mobile': True,
            }
        )
    
    def _get_headers(self):
        """Get request headers with authentication"""
        return {
            'Authorization': f'Bearer {self.init_data}',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
            'Origin': API_BASE,
            'Referer': f'{API_BASE}/',
        }
    
    def get_gifts(self):
        """Get gifts data from API"""
        url = f"{API_BASE}{GIFTS_ENDPOINT}"
        response = self.scraper.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()
        return response.json()
