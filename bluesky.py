from atproto import Client as BskyClient
from config import BSKY_HANDLE, BSKY_APP_PASS

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