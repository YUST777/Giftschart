import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.paths import PORTAL_SESSION_FILE, PROJECT_ROOT

load_dotenv()

API_ID = os.getenv("PORTAL_API_ID")
API_HASH = os.getenv("PORTAL_API_HASH")

async def main():
    try:
        from aportalsmp.auth import update_auth
        print(f"Starting auth with API_ID={API_ID}...")
        print("Please enter your phone number when prompted.")
        
        # update_auth usually handles the interaction via input()
        # We need to make sure we capture stdout/stdin correctly
        
        token = await update_auth(
            api_id=API_ID, 
            api_hash=API_HASH,
            session_path=PROJECT_ROOT, 
            session_name="account"
        )
        
        if token:
            print(f"Success! Token received: {token[:10]}...")
            # We also want to save the session string if possible?
            # update_auth returns the Auth Token for Portal API, NOT the Telethon session string usually.
            # But the side effect is creating 'account.session' file in PROJECT_ROOT.
            
            # services/portal_api.py uses session file OR session string.
            # If account.session is created, we serve.
            
            print("Authentication successful.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
