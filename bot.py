import sys
print("Python starting...", flush=True)

import os
import requests
import tweepy
import schedule
import time
from datetime import date

print("All imports done", flush=True)

# ── Check secrets BEFORE assigning (so we see what's missing) ──
print("--- Checking secrets ---", flush=True)
print("FOOTBALL_API_KEY present:",   "FOOTBALL_API_KEY"    in os.environ, flush=True)
print("TWITTER_API_KEY present:",    "TWITTER_API_KEY"     in os.environ, flush=True)
print("TWITTER_API_SECRET present:", "TWITTER_API_SECRET"  in os.environ, flush=True)
print("TWITTER_ACCESS_TOKEN present:", "TWITTER_ACCESS_TOKEN" in os.environ, flush=True)
print("TWITTER_ACCESS_SECRET present:", "TWITTER_ACCESS_SECRET" in os.environ, flush=True)
print("HF_TOKEN present:",           "HF_TOKEN"            in os.environ, flush=True)

# ── Load secrets safely (won't crash if missing) ────────────────
FOOTBALL_KEY    = os.environ.get("FOOTBALL_API_KEY",     "NOT SET")
TW_API_KEY      = os.environ.get("TWITTER_API_KEY",      "NOT SET")
TW_API_SECRET   = os.environ.get("TWITTER_API_SECRET",   "NOT SET")
TW_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "NOT SET")
TW_ACCESS_SEC   = os.environ.get("TWITTER_ACCESS_SECRET","NOT SET")
HF_TOKEN        = os.environ.get("HF_TOKEN",             "NOT SET")

# Print first 6 chars to confirm loaded without exposing full key
print("FOOTBALL_KEY:",    FOOTBALL_KEY[:6]    if FOOTBALL_KEY    != "NOT SET" else "NOT SET", flush=True)
print("TW_API_KEY:",      TW_API_KEY[:6]      if TW_API_KEY      != "NOT SET" else "NOT SET", flush=True)
print("TW_API_SECRET:",   TW_API_SECRET[:6]   if TW_API_SECRET   != "NOT SET" else "NOT SET", flush=True)
print("TW_ACCESS_TOKEN:", TW_ACCESS_TOKEN[:6] if TW_ACCESS_TOKEN != "NOT SET" else "NOT SET", flush=True)
print("TW_ACCESS_SEC:",   TW_ACCESS_SEC[:6]   if TW_ACCESS_SEC   != "NOT SET" else "NOT SET", flush=True)
print("HF_TOKEN:",        HF_TOKEN[:6]        if HF_TOKEN        != "NOT SET" else "NOT SET", flush=True)

# ── Abort early if any secret is missing ────────────────────────
missing = [k for k, v in {
    "FOOTBALL_API_KEY":     FOOTBALL_KEY,
    "TWITTER_API_KEY":      TW_API_KEY,
    "TWITTER_API_SECRET":   TW_API_SECRET,
    "TWITTER_ACCESS_TOKEN": TW_ACCESS_TOKEN,
    "TWITTER_ACCESS_SECRET":TW_ACCESS_SEC,
    "HF_TOKEN":             HF_TOKEN,
}.items() if v == "NOT SET"]

if missing:
    print(f"MISSING SECRETS: {missing}", flush=True)
    print("Go to Space Settings → Secrets and add the missing keys.", flush=True)
    sys.exit(1)

print("All secrets loaded", flush=True)

# ── Twitter client ───────────────────────────────────────────────
try:
    twitter = tweepy.Client(
        consumer_key=TW_API_KEY,
        consumer_secret=TW_API_SECRET,
        access_token=TW_ACCESS_TOKEN,
        access_token_secret=TW_ACCESS_SEC
    )
    print("Twitter client ready", flush=True)
except Exception as e:
    print(f"Twitter client failed: {e}", flush=True)
    sys.exit(1)

# ── League IDs on football-data.org ─────────────────────────────
LEAGUES = {
    "PL": "Premier League",
    "CL": "Champions League",
}

# ── Fetch today's finished matches ──────────────────────────────
def get_finished_matches():
    headers = {"X-Auth-Token": FOOTBALL_KEY}
    today   = str(date.today())
    results = []

    for code, name in LEAGUES.items():
        try:
            url = f"https://api.football-data.org/v4/competitions/{code}/matches?status=FINISHED"
            r   = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            matches = r.json().get("matches", [])
            todays  = [m for m in matches if m["utcDate"][:10] == today]
            results.extend([(name, m) for m in todays])
            print(f"{name}: {len(todays)} finished matches today", flush=True)
            time.sleep(6)  # stay within 10 calls/min free tier limit
        except Exception as e:
            print(f"Error fetching {name}: {e}", flush=True)

    return results

# ── Genzify via HF Inference API ────────────────────────────────
def genzify(league, match):
    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    hg   = match["score"]["fullTime"]["home"]
    ag   = match["score"]["fullTime"]["away"]

    if hg > ag:
        context = f"{home} beat {away} {hg}-{ag}"
    elif ag > hg:
        context = f"{away} beat {home} {ag}-{hg}"
    else:
        context = f"{home} and {away} drew {hg}-{ag}"

    prompt = (
        "<|im_start|>system\n"
        "You are a GenZ football fan on Twitter. "
        "Write a single hype tweet in GenZ slang with emojis. "
        "Max 220 characters. No hashtags needed.\n"
        "<|im_end|>\n"
        "<|im_start|>user\n"
        f"Write a tweet about this {league} result: {context}\n"
        "<|im_end|>\n"
        "<|im_start|>assistant\n"
    )

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/somendrew/genz-qwen-2.5-1.5B",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 80,
                    "temperature": 0.9,
                    "do_sample": True,
                    "return_full_text": False,
                },
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        # Handle model loading / error responses from HF
        if isinstance(data, dict) and "error" in data:
            print(f"HF model error: {data['error']}", flush=True)
            return None, context

        tweet = data[0]["generated_text"].strip()
        tweet = tweet[:220]
        return tweet, context

    except Exception as e:
        print(f"Genzify error: {e}", flush=True)
        return None, context

# ── Track posted matches to avoid duplicates ────────────────────
posted = set()

MAX_POSTS_PER_RUN = 5

# ── Main run loop ────────────────────────────────────────────────
def post_scores():
    print("\n--- Checking for finished matches ---", flush=True)
    matches = get_finished_matches()

    if not matches:
        print("No matches today.", flush=True)
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

        tweet, context = genzify(league, match)  # FIX: unpack tuple correctly

        if not tweet:
            print(f"No tweet generated for: {context}", flush=True)
            continue

        print(f"Attempting to post: {tweet}", flush=True)

        try:
            twitter.create_tweet(text=tweet)
            posted.add(match_id)
            posted_this_run += 1
            print(f"Tweeted: {tweet}", flush=True)
        except tweepy.errors.TooManyRequests:
            print("Twitter rate limit hit, stopping this run.", flush=True)
            break
        except tweepy.errors.Forbidden as e:
            print(f"Twitter forbidden error (check app permissions): {e}", flush=True)
            break
        except Exception as e:
            print(f"Twitter error: {e}", flush=True)

        time.sleep(30)  # gap between posts

# ── Schedule every 30 minutes ────────────────────────────────────
schedule.every(30).minutes.do(post_scores)

print("Bot is running. Running now and then every 30 minutes.", flush=True)
post_scores()  # run once immediately on startup

while True:
    schedule.run_pending()
    time.sleep(60)