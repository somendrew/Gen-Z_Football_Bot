import time
import schedule
import json
import os

print("Python starting...", flush=True)

from football import get_finished_matches
from genzify import genzify
from bluesky import post_to_bluesky
from huggingface_hub import HfApi, hf_hub_download

print("All imports done", flush=True)

# ── HuggingFace Dataset repo for persistence ─────────────────────────
HF_TOKEN = os.environ.get("HF_TOKEN", "NOT SET")
REPO_ID  = "somendrew/bot-state"   # create this as a private Dataset repo on HF
API      = HfApi(token=HF_TOKEN)
LOCAL_POSTED_FILE = "/app/posted.json"

def load_posted():
    try:
        path = hf_hub_download(
            repo_id=REPO_ID,
            filename="posted.json",
            repo_type="dataset",
            token=HF_TOKEN,
            local_dir="/app"
        )
        with open(path) as f:
            data = set(json.load(f))
            print(f"Loaded {len(data)} posted match IDs from HF repo.", flush=True)
            return data
    except Exception as e:
        print(f"Could not load posted.json from HF repo (starting fresh): {e}", flush=True)
        return set()

def save_posted(posted):
    try:
        with open(LOCAL_POSTED_FILE, "w") as f:
            json.dump(list(posted), f)
        API.upload_file(
            path_or_fileobj=LOCAL_POSTED_FILE,
            path_in_repo="posted.json",
            repo_id=REPO_ID,
            repo_type="dataset",
            token=HF_TOKEN,
            commit_message="update posted matches"
        )
        print(f"Saved {len(posted)} posted match IDs to HF repo.", flush=True)
    except Exception as e:
        print(f"Failed to save posted.json to HF repo: {e}", flush=True)

# ── Health server ─────────────────────────────────────────────────────
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args): pass

threading.Thread(
    target=lambda: HTTPServer(("0.0.0.0", 7860), Health).serve_forever(),
    daemon=True
).start()

# ── State ─────────────────────────────────────────────────────────────
posted = load_posted()
MAX_POSTS_PER_RUN = 10

# ── Main bot loop ─────────────────────────────────────────────────────
def run_bot():
    print("\n--- Checking for finished matches ---", flush=True)
    matches = get_finished_matches()

    if not matches:
        print("No PL/CL matches today.", flush=True)
        return

    posted_this_run = 0

    for league, match in matches:
        if posted_this_run >= MAX_POSTS_PER_RUN:
            print("Max posts per run reached, stopping.", flush=True)
            break

        match_id = match["id"]
        if match_id in posted:
            print(f"Already posted match {match_id}, skipping.", flush=True)
            continue

        tweet, context = genzify(league, match)
        if not tweet:
            print(f"No tweet generated for: {context}", flush=True)
            continue

        print(f"Attempting to post: {tweet}", flush=True)
        uri = post_to_bluesky(tweet)

        if uri:
            posted.add(match_id)
            save_posted(posted)   # persist immediately after each successful post
            posted_this_run += 1

        time.sleep(5)

schedule.every(15).minutes.do(run_bot)

print("Bot is running. Checking every 15 minutes.", flush=True)
run_bot()

while True:
    schedule.run_pending()
    time.sleep(60)