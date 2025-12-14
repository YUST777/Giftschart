#!/usr/bin/env python3
"""
Premarket Gift Price Scheduler
Automatically fetches prices for all 4 premarket gifts every 32 minutes
Uses advanced CloudFlare bypass for maximum success rate
"""

import asyncio
import time
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional

# Import our advanced bypass system
from advanced_cloudflare_bypass import AdvancedTonnelAPI, get_bypass_stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('premarket_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PremarketScheduler:
    def __init__(self):
        self.api = AdvancedTonnelAPI()
        self.running = True
        self.last_run = None
        self.run_count = 0
        
        # All premarket gifts (new 2025 releases)
        self.premarket_gifts = [
            "Happy_Brownie",
            "Spring_Basket",
            "Instant_Ramen",
            "Faith_Amulet",
            "Mousse_Cake",
            "Ice_Cream"
        ]
        
        # Timing configuration
        self.interval_minutes = 32
        self.interval_seconds = self.interval_minutes * 60
        
        # Statistics tracking
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'gift_success_count': {gift: 0 for gift in self.premarket_gifts},
            'gift_failure_count': {gift: 0 for gift in self.premarket_gifts},
            'last_successful_prices': {},
            'last_run_time': None,
            'next_run_time': None
        }
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.running = False
    
    async def fetch_single_gift(self, gift_name: str) -> Optional[float]:
        """Fetch price for a single gift with error handling."""
        try:
            logger.info(f"🔍 Fetching {gift_name}...")
            start_time = time.time()
            
            price = await self.api.get_gift_price_advanced(gift_name)
            elapsed_time = time.time() - start_time
            
            if price is not None:
                logger.info(f"✅ {gift_name}: {price} TON (in {elapsed_time:.1f}s)")
                self.stats['gift_success_count'][gift_name] += 1
                self.stats['last_successful_prices'][gift_name] = {
                    'price': price,
                    'timestamp': datetime.now().isoformat(),
                    'response_time': elapsed_time
                }
                return price
            else:
                logger.warning(f"❌ {gift_name}: Price unavailable (in {elapsed_time:.1f}s)")
                self.stats['gift_failure_count'][gift_name] += 1
                return None
                
        except Exception as e:
            logger.error(f"💥 {gift_name}: Error - {e}")
            self.stats['gift_failure_count'][gift_name] += 1
            return None
    
    async def fetch_all_premarket_gifts(self) -> Dict[str, Optional[float]]:
        """Fetch prices for all premarket gifts."""
        logger.info("🚀 Starting premarket gift price collection...")
        logger.info(f"📊 Run #{self.run_count + 1} - Fetching {len(self.premarket_gifts)} gifts")
        
        start_time = time.time()
        results = {}
        
        # Fetch all gifts (can be done concurrently but we'll do them sequentially 
        # to avoid overwhelming the API)
        for gift in self.premarket_gifts:
            results[gift] = await self.fetch_single_gift(gift)
            
            # Add small delay between gifts to be respectful to the API
            await asyncio.sleep(2)
        
        elapsed_time = time.time() - start_time
        
        # Calculate success rate for this run
        successful_gifts = sum(1 for price in results.values() if price is not None)
        success_rate = (successful_gifts / len(self.premarket_gifts)) * 100
        
        logger.info("=" * 60)
        logger.info(f"📈 RUN SUMMARY #{self.run_count + 1}")
        logger.info("=" * 60)
        logger.info(f"🎯 Success Rate: {success_rate:.1f}% ({successful_gifts}/{len(self.premarket_gifts)})")
        logger.info(f"⏱️ Total Time: {elapsed_time:.1f}s")
        
        # Log individual results
        for gift, price in results.items():
            status = f"{price} TON" if price is not None else "UNAVAILABLE"
            logger.info(f"   {gift:12} {status}")
        
        logger.info("=" * 60)
        
        return results
    
    def get_comprehensive_stats(self) -> Dict:
        """Get comprehensive statistics about the scheduler performance."""
        total_attempts = sum(self.stats['gift_success_count'].values()) + sum(self.stats['gift_failure_count'].values())
        total_successes = sum(self.stats['gift_success_count'].values())
        
        overall_success_rate = (total_successes / total_attempts * 100) if total_attempts > 0 else 0
        
        # Get bypass method statistics
        bypass_stats = get_bypass_stats()
        
        return {
            'scheduler_stats': self.stats,
            'overall_success_rate': overall_success_rate,
            'total_attempts': total_attempts,
            'total_successes': total_successes,
            'bypass_method_stats': bypass_stats,
            'uptime': (datetime.now() - self.start_time).total_seconds() if hasattr(self, 'start_time') else 0
        }
    
    def log_periodic_stats(self):
        """Log periodic statistics."""
        stats = self.get_comprehensive_stats()
        
        logger.info("📊 SCHEDULER STATISTICS")
        logger.info(f"   Total Runs: {self.stats['total_runs']}")
        logger.info(f"   Successful Runs: {self.stats['successful_runs']}")
        logger.info(f"   Overall Success Rate: {stats['overall_success_rate']:.1f}%")
        
        if self.stats['last_run_time']:
            logger.info(f"   Last Run: {self.stats['last_run_time']}")
        if self.stats['next_run_time']:
            logger.info(f"   Next Run: {self.stats['next_run_time']}")
        
        # Top performing gifts
        top_gifts = sorted(
            self.stats['gift_success_count'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        if top_gifts:
            logger.info("   Top Performing Gifts:")
            for gift, count in top_gifts:
                total = count + self.stats['gift_failure_count'][gift]
                rate = (count / total * 100) if total > 0 else 0
                logger.info(f"     {gift}: {rate:.1f}% ({count} successes)")
    
    async def run_scheduled_task(self):
        """Run the scheduled task once."""
        self.run_count += 1
        self.stats['total_runs'] += 1
        self.stats['last_run_time'] = datetime.now().isoformat()
        
        try:
            results = await self.fetch_all_premarket_gifts()
            
            # Check if this run was successful (at least 50% of gifts fetched)
            successful_gifts = sum(1 for price in results.values() if price is not None)
            if successful_gifts >= len(self.premarket_gifts) * 0.5:
                self.stats['successful_runs'] += 1
                logger.info("✅ Run completed successfully")
            else:
                self.stats['failed_runs'] += 1
                logger.warning("⚠️ Run completed with low success rate")
            
            # Log stats every 5 runs
            if self.run_count % 5 == 0:
                self.log_periodic_stats()
                
        except Exception as e:
            logger.error(f"💥 Run failed with error: {e}")
            self.stats['failed_runs'] += 1
    
    async def run(self):
        """Main scheduler loop."""
        logger.info("🚀 Premarket Price Scheduler Starting")
        logger.info(f"📅 Interval: {self.interval_minutes} minutes")
        logger.info(f"🎯 Gifts to monitor: {len(self.premarket_gifts)}")
        logger.info("=" * 60)
        
        self.start_time = datetime.now()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Run first fetch immediately
        logger.info("🏃 Running initial fetch...")
        await self.run_scheduled_task()
        
        # Main scheduler loop
        while self.running:
            # Calculate next run time
            next_run = datetime.now() + timedelta(seconds=self.interval_seconds)
            self.stats['next_run_time'] = next_run.isoformat()
            
            logger.info(f"⏰ Next run scheduled for: {next_run.strftime('%H:%M:%S')} ({self.interval_minutes} minutes)")
            
            # Wait for the interval (with periodic checks for shutdown)
            wait_time = 0
            while wait_time < self.interval_seconds and self.running:
                await asyncio.sleep(10)  # Check every 10 seconds
                wait_time += 10
                
                # Show countdown every 5 minutes
                remaining = self.interval_seconds - wait_time
                if remaining > 0 and remaining % 300 == 0:  # Every 5 minutes
                    logger.info(f"⏳ Next run in {remaining // 60} minutes...")
            
            if self.running:
                await self.run_scheduled_task()
        
        logger.info("👋 Scheduler stopped gracefully")
        self.log_periodic_stats()

async def main():
    """Main entry point."""
    scheduler = PremarketScheduler()
    
    try:
        await scheduler.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Scheduler crashed: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Premarket Gift Price Scheduler")
    print("=" * 50)
    print("This scheduler will fetch prices for all 4 premarket gifts every 32 minutes")
    print("Using advanced CloudFlare bypass for maximum success rate")
    print("")
    print("Press Ctrl+C to stop gracefully")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Scheduler stopped by user")
    except Exception as e:
        print(f"\n💥 Scheduler crashed: {e}")
        sys.exit(1) 