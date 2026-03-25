"""
TikTok OAuth2 Setup — runs the browser-based auth flow once to create
tiktok_token.json. Run this once after adding TIKTOK_CLIENT_KEY and
TIKTOK_CLIENT_SECRET to your .env file.

Usage:
    python scripts/setup_tiktok_auth.py
"""

import sys
import json
import secrets
import hashlib
import base64
import urllib.parse
import webbrowser
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from config.settings import settings
from loguru import logger

TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
REDIRECT_URI = "https://wiredwrong.local/callback"
SCOPES = "video.publish,video.upload"


def _pkce_pair():
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


def setup_auth():
    if not settings.tiktok_client_key or not settings.tiktok_client_secret:
        print("\nERROR: TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET not set in .env")
        print("\nSteps to get them:")
        print("  1. Go to https://developers.tiktok.com")
        print("  2. Open your app -> Login Kit -> set Redirect URI to: https://wiredwrong.local/callback")
        print("  3. Copy Client Key + Client Secret into .env")
        print("  4. Re-run this script")
        sys.exit(1)

    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)

    params = {
        "client_key": settings.tiktok_client_key,
        "response_type": "code",
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    auth_url = TIKTOK_AUTH_URL + "?" + urllib.parse.urlencode(params)

    print("\n" + "="*60)
    print("Opening TikTok authorization in your browser...")
    print("="*60)
    webbrowser.open(auth_url)

    print("\nAfter you authorize, your browser will show an error page.")
    print("That's expected! Just copy the FULL URL from your browser's address bar")
    print("and paste it here.\n")
    callback_url = input("Paste the full redirect URL here: ").strip()

    parsed = urllib.parse.urlparse(callback_url)
    params_returned = dict(urllib.parse.parse_qsl(parsed.query))
    code = params_returned.get("code")
    returned_state = params_returned.get("state")

    if not code:
        logger.error("No authorization code found in URL.")
        sys.exit(1)

    if returned_state != state:
        logger.error("State mismatch — possible CSRF. Aborting.")
        sys.exit(1)

    # Exchange code for tokens
    import requests
    resp = requests.post(TIKTOK_TOKEN_URL, data={
        "client_key": settings.tiktok_client_key,
        "client_secret": settings.tiktok_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})

    if resp.status_code != 200:
        logger.error(f"Token exchange failed: {resp.status_code} {resp.text}")
        sys.exit(1)

    token_data = resp.json()
    if "error" in token_data:
        logger.error(f"Token error: {token_data}")
        sys.exit(1)

    # Save token
    token_path = Path(settings.tiktok_token_path)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_data["saved_at"] = datetime.utcnow().isoformat()
    token_path.write_text(json.dumps(token_data, indent=2))

    logger.info(f"TikTok token saved to: {token_path}")
    logger.info(f"Authenticated as open_id: {token_data.get('open_id', 'unknown')}")
    print("\nTikTok auth complete. You can now cross-post to TikTok.")


if __name__ == "__main__":
    setup_auth()
