import sys
print("Python starting...", flush=True)

import os
import requests
import schedule
import time
from datetime import date, timedelta
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
from atproto import Client as BskyClient
import torch

load_dotenv()
print("All imports done", flush=True)

# ── Check secrets ────────────────────────────────────────────────
print("--- Checking secrets ---", flush=True)
print("FOOTBALL_API_KEY present:", "FOOTBALL_API_KEY" in os.environ, flush=True)
print("HF_TOKEN present:",         "HF_TOKEN"         in os.environ, flush=True)
print("BSKY_HANDLE present:",      "BSKY_HANDLE"      in os.environ, flush=True)
print("BSKY_APP_PASS present:",    "BSKY_APP_PASS"    in os.environ, flush=True)

# ── Load secrets ─────────────────────────────────────────────────
FOOTBALL_KEY  = os.environ.get("FOOTBALL_API_KEY", "NOT SET")
HF_TOKEN      = os.environ.get("HF_TOKEN",         "NOT SET")
BSKY_HANDLE   = os.environ.get("BSKY_HANDLE",      "NOT SET")
BSKY_APP_PASS = os.environ.get("BSKY_APP_PASS",    "NOT SET")

print("FOOTBALL_KEY:", FOOTBALL_KEY[:6] if FOOTBALL_KEY != "NOT SET" else "NOT SET", flush=True)
print("HF_TOKEN:",     HF_TOKEN[:6]     if HF_TOKEN     != "NOT SET" else "NOT SET", flush=True)
print("BSKY_HANDLE:",  BSKY_HANDLE,                                                  flush=True)

# ── Abort if any secret missing ──────────────────────────────────
missing = [k for k, v in {
    "FOOTBALL_API_KEY": FOOTBALL_KEY,
    "HF_TOKEN":         HF_TOKEN,
    "BSKY_HANDLE":      BSKY_HANDLE,
    "BSKY_APP_PASS":    BSKY_APP_PASS,
}.items() if v == "NOT SET"]

if missing:
    print(f"MISSING SECRETS: {missing}", flush=True)
    print("Add them to your .env file.", flush=True)
    sys.exit(1)

print("All secrets loaded", flush=True)

# ── Load Genzify model ───────────────────────────────────────────
print("Loading Genzify model...", flush=True)
tokenizer = AutoTokenizer.from_pretrained("somendrew/genz-qwen-2.5-1.5B", token=HF_TOKEN)
model = AutoModelForCausalLM.from_pretrained(
    "somendrew/genz-qwen-2.5-1.5B",
    token=HF_TOKEN,
    dtype=torch.bfloat16,
    device_map="cpu",
    low_cpu_mem_usage=True,
)
model.eval()
model.config.use_cache = True
print("Model loaded!", flush=True)

# ── Competitions to track ────────────────────────────────────────
LEAGUES = {
    "PL":  "Premier League",
    "CL":  "UEFA Champions League",
}

# ── Fetch today's finished matches ───────────────────────────────
def get_finished_matches():
    headers  = {"X-Auth-Token": FOOTBALL_KEY}
    today    = str(date.today())
    tomorrow = str(date.today() + timedelta(days=1))

    try:
        url = (
            f"https://api.football-data.org/v4/matches"
            f"?dateFrom={today}&dateTo={tomorrow}"
            f"&status=FINISHED&competitions=PL,CL"
        )
        r = requests.get(url, headers=headers, timeout=10)
        print(f"API status code: {r.status_code}", flush=True)
        r.raise_for_status()

        matches = r.json().get("matches", [])
        results = []
        for m in matches:
            comp_code = m.get("competition", {}).get("code", "")
            comp_name = LEAGUES.get(comp_code)
            if comp_name:
                results.append((comp_name, m))

        print(f"Finished PL/CL matches today: {len(results)}", flush=True)
        return results

    except Exception as e:
        print(f"Error fetching matches: {e}", flush=True)
        return []

# ── Genzify the result ───────────────────────────────────────────
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
        inputs = tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=80,
                temperature=0.9,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        tweet = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True
        ).strip()[:300]
        print(f"Genzify output: {tweet}", flush=True)
        return tweet, context

    except Exception as e:
        print(f"Genzify error: {e}", flush=True)
        return None, context

# ── Post to Bluesky ──────────────────────────────────────────────
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

# ── Track posted matches ─────────────────────────────────────────
posted = set()
MAX_POSTS_PER_RUN = 3

# ── Main run loop ────────────────────────────────────────────────
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

# ── Scheduler ────────────────────────────────────────────────────
schedule.every(30).minutes.do(run_bot)

print("Bot is running. Checking every 30 minutes.", flush=True)
run_bot()  # run once immediately on startup

while True:
    schedule.run_pending()
    time.sleep(60)