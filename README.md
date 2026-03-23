---
title: Genz Football Bot
emoji: ⚽
colorFrom: red
colorTo: yellow
sdk: docker
pinned: false
license: apache-2.0
---

# GenZ Football Bot 🤖⚽🔥

A fully automated football bot that watches live matches, detects goals and match events in real time, and posts savage GenZ-style commentary to **Bluesky** using a fine-tuned LLM.

---

## What it does

- 📅 **Schedules triggers** for today's watched team matches at kickoff time
- ⚽ **Detects goals in real time** by polling football-data.org every 2 minutes during live matches
- 🔥 **Generates savage GenZ tweets** using a fine-tuned Qwen 2.5 1.5B model
- 🐦 **Posts to Bluesky** automatically after every goal and at full time
- 💾 **Persists posted match IDs** to a private HuggingFace Dataset repo to avoid duplicate posts across container restarts

---

## Watched Teams

The bot only posts about matches involving these clubs:

| Club | League |
|------|--------|
| Arsenal FC | Premier League |
| Liverpool FC | Premier League |
| Manchester City FC | Premier League |
| Manchester United FC | Premier League |
| Chelsea FC | Premier League |
| FC Barcelona | La Liga |
| Real Madrid CF | La Liga |
| Atlético de Madrid | La Liga |
| FC Bayern München | Bundesliga |
| Juventus FC | Serie A |
| AC Milan | Serie A |
| Inter Milan | Serie A |

---

## Leagues Covered

- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League
- 🇪🇸 La Liga
- 🇮🇹 Serie A
- 🏆 UEFA Champions League

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Bot runtime | Python 3.10 |
| LLM | Fine-tuned Qwen 2.5 1.5B (`somendrew/genz-qwen-2.5-1.5B`) |
| Football data | football-data.org free tier |
| Social posting | Bluesky via `atproto` |
| Persistence | HuggingFace Dataset repo |
| Hosting | HuggingFace Spaces (Docker) |
| Scheduling | `schedule` library |

---

## Project Structure

```
genz-football-bot/
├── bot.py          # Main orchestrator, scheduling, live match polling
├── football.py     # Fetches finished/scheduled matches from football-data.org
├── genzify.py      # Loads LLM locally, generates GenZ tweets
├── bluesky.py      # Bluesky client, posts tweets
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Environment Variables

Set these as **Secrets** in your HuggingFace Space settings:

| Variable | Description |
|----------|-------------|
| `FOOTBALL_API_KEY` | football-data.org API key |
| `BSKY_HANDLE` | Bluesky handle (e.g. `yourbot.bsky.social`) |
| `BSKY_APP_PASS` | Bluesky app password |
| `HF_TOKEN` | HuggingFace token (for loading model + saving state) |

---

## How it works

### 1. Smart match triggers
At startup, the bot fetches today's scheduled matches for watched teams and calculates `kickoff + 105 mins` as the trigger time for each match. At trigger time it starts polling the match every 2 minutes.

### 2. Live goal detection
During a live match, the bot compares the current goal list against what it has already seen. If new goals are detected it immediately fires the LLM and posts to Bluesky.

### 3. Full time summary
When the match status changes to `FINISHED`, the bot generates a full time summary tweet and stops polling that match.

### 4. Fallback polling
Every 15 minutes the bot also runs a fallback check for any finished watched matches — catching anything the smart triggers may have missed.

### 5. Duplicate prevention
Every successfully posted match ID is saved to a private HuggingFace Dataset repo (`somendrew/bot-state`). On container restart, the bot loads this list so it never reposts the same match.

---

## Local Development

```bash
# clone the repo
git clone https://github.com/somendrew/Gen-Z_Football_Bot.git
cd Gen-Z_Football_Bot

# create virtual environment
python -m venv venv
source venv/bin/activate

# install dependencies
pip install -r requirements.txt

# create .env file
cp .env.example .env
# fill in your API keys in .env

# run the bot
python bot.py
```

---

## Follow the Bot on Bluesky

All match updates, goal alerts and full time reactions are posted here:

👉 **[https://bsky.app/profile/somendrew.bsky.social](https://bsky.app/profile/somendrew.bsky.social)**

---

## Model

The LLM used is [`somendrew/genz-qwen-2.5-1.5B`](https://huggingface.co/somendrew/genz-qwen-2.5-1.5B) — a fine-tuned version of Qwen 2.5 1.5B trained to generate savage, toxic, hilarious GenZ football commentary.

---

## License

Apache 2.0