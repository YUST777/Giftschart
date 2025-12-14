#!/usr/bin/env python3
"""
Portal API Authentication Refresh Script

This script refreshes the Portal API authentication token.
Use this in production when tokens expire.

Usage: python3 refresh_auth.py
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def refresh_auth():
    """Refresh Portal API authentication token."""
    try:
        print("🔄 Refreshing Portal API authentication token...")
        
        # Import Portal API functions
        from portal_api import get_fresh_auth_token, save_token
        
        print("📡 Requesting fresh token from Portal API...")
        
        # Get a fresh token
        new_token = await get_fresh_auth_token()
        
        if new_token:
            print(f"✅ Successfully obtained new token: {new_token[:50]}...")
            
            # Save the new token
            await save_token(new_token)
            print("💾 New token saved to portal_auth_token.txt")
            
            # Test the token
            print("🧪 Testing new token...")
            from portal_api import validate_and_refresh_portal_connection
            
            is_valid = await validate_and_refresh_portal_connection()
            if is_valid:
                print("✅ Portal API connection is now working!")
                print("🎉 Authentication refresh completed successfully!")
                return True
            else:
                print("❌ Token refresh failed validation")
                return False
        else:
            print("❌ Failed to obtain new token")
            return False
            
    except Exception as e:
        print(f"❌ Error refreshing authentication: {e}")
        return False

async def main():
    """Main function."""
    print("🚀 Portal API Authentication Refresh Tool")
    print("=" * 50)
    
    # Check if Portal API is available
    try:
        from portal_api import PORTAL_API_AVAILABLE
        if not PORTAL_API_AVAILABLE:
            print("❌ Portal API (aportalsmp) is not available")
            print("Please install with: pip install aportalsmp")
            return
    except ImportError:
        print("❌ Cannot import portal_api module")
        return
    
    # Refresh authentication
    success = await refresh_auth()
    
    if success:
        print("\n📋 Summary:")
        print("- ✅ Authentication token refreshed")
        print("- ✅ New token saved to portal_auth_token.txt")
        print("- ✅ Portal API is now working")
        print("\n💡 You can now generate price cards with real-time Portal API data")
    else:
        print("\n❌ Failed to refresh Portal API authentication")
        print("💡 The system will continue using Legacy API fallback")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
