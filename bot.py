import time
import schedule
import json

print("Python starting...", flush=True)

from football import get_finished_matches
from genzify import genzify
from bluesky import post_to_bluesky

print("All imports done", flush=True)

#tracking server health
#########################################################################
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
#########################################################################
# We want to avoid reposting the same match multiple times, so we keep track of posted match IDs in a JSON file.
POSTED_FILE = "/data/posted.json"
def load_posted():
    try:
        with open(POSTED_FILE) as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()
    
def save_posted(posted):
    with open(POSTED_FILE, "w") as f:
        json.dump(list(posted), f)

posted = load_posted()

##########################################################################
MAX_POSTS_PER_RUN = 10

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
            save_posted()
            posted_this_run += 1

        time.sleep(5)

schedule.every(15).minutes.do(run_bot)

print("Bot is running. Checking every 15 minutes.", flush=True)
run_bot()

while True:
    schedule.run_pending()
    time.sleep(60)