import time
import schedule

print("Python starting...", flush=True)

from football import get_finished_matches
from genzify import genzify
from bluesky import post_to_bluesky

print("All imports done", flush=True)

posted = set()
MAX_POSTS_PER_RUN = 3

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
            posted_this_run += 1

        time.sleep(5)

schedule.every(30).minutes.do(run_bot)

print("Bot is running. Checking every 30 minutes.", flush=True)
run_bot()

while True:
    schedule.run_pending()
    time.sleep(60)