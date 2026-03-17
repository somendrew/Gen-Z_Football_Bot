from atproto import Client as BskyClient
import os
from dotenv import load_dotenv

load_dotenv()

BSKY_HANDLE   = os.environ.get("BSKY_HANDLE",      "NOT SET")
BSKY_APP_PASS = os.environ.get("BSKY_APP_PASS",    "NOT SET")

def post_to_bluesky(text):
    try:
        client = BskyClient()
        client.login(BSKY_HANDLE, BSKY_APP_PASS)
        response = client.send_post(text=text)
        print(f"Posted to Bluesky: {text[:60]}...", flush=True)
        return response.uri
    except Exception as e:
        print(f"Bluesky error: {e}", flush=True)
        return None