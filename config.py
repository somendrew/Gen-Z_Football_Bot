import os
import sys
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_KEY  = os.environ.get("FOOTBALL_API_KEY", "NOT SET")
HF_TOKEN      = os.environ.get("HF_TOKEN",         "NOT SET")
BSKY_HANDLE   = os.environ.get("BSKY_HANDLE",      "NOT SET")
BSKY_APP_PASS = os.environ.get("BSKY_APP_PASS",    "NOT SET")

missing = [k for k, v in {
    "FOOTBALL_API_KEY": FOOTBALL_KEY,
    "HF_TOKEN":         HF_TOKEN,
    "BSKY_HANDLE":      BSKY_HANDLE,
    "BSKY_APP_PASS":    BSKY_APP_PASS,
}.items() if v == "NOT SET"]

if missing:
    print(f"MISSING SECRETS: {missing}", flush=True)
    sys.exit(1)

print("All secrets loaded", flush=True)