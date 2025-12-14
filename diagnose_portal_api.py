import sys
import os
import subprocess
import requests
import asyncio
import importlib.util

print("\n=== Portal API Diagnostic Tool ===\n")

# 1. Python version
print(f"Python version: {sys.version}")

# 2. Installed packages
print("\nChecking for 'aportalsmp' package...")
try:
    import aportalsmp
    print("aportalsmp is installed.")
except ImportError:
    print("aportalsmp is NOT installed! Run: pip install aportalsmp")

print("\nChecking for 'requests' package...")
try:
    import requests
    print("requests is installed.")
except ImportError:
    print("requests is NOT installed! Run: pip install requests")

# 3. Network connectivity
print("\nTesting network connectivity to Portal API...")
try:
    resp = requests.get("https://api.portals.market/", timeout=10)
    print(f"Portal API reachable, status code: {resp.status_code}")
except Exception as e:
    print(f"Network error: {e}")

# 4. aportalsmp import and version
print("\nTesting aportalsmp import and version...")
try:
    import aportalsmp
    print(f"aportalsmp version: {getattr(aportalsmp, '__version__', 'unknown')}")
except Exception as e:
    print(f"aportalsmp import failed: {e}")

# 5. Check for auth token (try environment variable or config file)
auth_token = os.environ.get("PORTALS_AUTH_TOKEN")
if auth_token:
    print("Auth token found in environment variable PORTALS_AUTH_TOKEN.")
else:
    print("Auth token NOT found in environment variable PORTALS_AUTH_TOKEN.")
    # Try to find in a file
    if os.path.exists("portal_auth.txt"):
        with open("portal_auth.txt") as f:
            auth_token = f.read().strip()
        print("Auth token loaded from portal_auth.txt.")
    else:
        print("Auth token NOT found in portal_auth.txt either.")

# 6. Try actual Portal API call (if possible)
async def test_portal_api():
    print("\nTesting actual Portal API call for a known gift (e.g., 'Xmas Stocking')...")
    if not auth_token:
        print("No auth token available, skipping actual API call.")
        return
    try:
        from aportalsmp.gifts import search
        results = await search(gift_name="Xmas Stocking", limit=1, authData=auth_token)
        if results and len(results) > 0:
            gift = results[0]
            print(f"Portal API call succeeded. Gift: {getattr(gift, 'name', str(gift))}, Price: {getattr(gift, 'price', 'N/A')}")
        else:
            print("Portal API call returned no results.")
    except Exception as e:
        print(f"Portal API call failed: {e}")

try:
    asyncio.run(test_portal_api())
except Exception as e:
    print(f"Asyncio run failed: {e}")

print("\n=== Diagnostic Complete ===\n") 