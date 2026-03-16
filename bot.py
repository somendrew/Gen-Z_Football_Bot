import os
import requests
import tweepy
import schedule
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# ── Load secrets ──────────────────────────────────────────
FOOTBALL_KEY    = os.environ["FOOTBALL_API_KEY"]
TW_API_KEY      = os.environ["TWITTER_API_KEY"]
TW_API_SECRET   = os.environ["TWITTER_API_SECRET"]
TW_ACCESS_TOKEN = os.environ["TWITTER_ACCESS_TOKEN"]
TW_ACCESS_SEC   = os.environ["TWITTER_ACCESS_SECRET"]

# ── Load your GenZ model (4-bit to save RAM) ──────────────
print("Loading model...")
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(load_in_4bit=True)

tokenizer = AutoTokenizer.from_pretrained("somendrew/genz-qwen-2.5-1.5B")
model = AutoModelForCausalLM.from_pretrained(
    "somendrew/genz-qwen-2.5-1.5B",
    quantization_config = bnb_config,
    device_map = "auto"
)
print("Model loaded ✅")

# ── Twitter client ─────────────────────────────────────────

twitter = tweepy.Client(
    consumer_key=TW_API_KEY,
    consumer_secret=TW_API_SECRET,
    access_token=TW_ACCESS_TOKEN,
    access_token_secret=TW_ACCESS_SEC
)

# ── League IDs on football-data.org ───────────────────────
LEAGUES = {
    "PL":  "Premier League",
    "CL":  "Champions League"
}

# ── Fetch today's finished matches ────────────────────────

def get_finished_matches():
    headers = {"X-Auth-Token": FOOTBALL_KEY}
    results = []

    for code, name in LEAGUES.items():
        url = f"https://api.football-data.org/v4/competitions/{code}/matches?status=FINISHED"
        r = requests.get(url, headers=headers).json()
        matches = r.get("matches", [])

        # Only today's matches
        from datetime import date
        today = str(date.today())
        todays = [m for m in matches if m["utcDate"][:10] == today]
        results.extend([(name, m) for m in todays])

    return results

# ── GenZify the score ──────────────────────────────────────
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

    prompt = f"""<|im_start|>system You are a GenZ football fan on Twitter. Write a single hype tweet in GenZ slang with emojis. Max 220 characters. No hashtags needed.
<|im_end|>
<|im_start|>user
Write a tweet about this {league} result: {context}
<|im_end|>
<|im_start|>assistant
"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    out = model.generate(
        **inputs,
        max_new_tokens=80,
        temperature=0.9,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
    tweet = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    return tweet[:220]  # hard cap for safety

# ── Track posted matches to avoid duplicates ──────────────
posted = set()

def post_scores():
    print("Checking for finished matches...")
    matches = get_finished_matches()

    if not matches:
        print("No matches today.")
        return

    for league, match in matches:
        match_id = match["id"]
        if match_id in posted:
            continue

        tweet = genzify(league, match)
        try:
            twitter.create_tweet(text=tweet)
            posted.add(match_id)
            print(f"✅ Tweeted: {tweet}")
        except Exception as e:
            print(f"❌ Twitter error: {e}")

        time.sleep(5)

# ── Schedule: check every 30 minutes ──────────────────────
schedule.every(30).minutes.do(post_scores)
    
print("Bot is running 🚀")
post_scores()  # run once immediately on startup

while True:
    schedule.run_pending()
    time.sleep(60)













