# ⚽ GenZ Football Bot

A fully automated football news bot that fetches live match results and posts them in **Gen Z slang** to Bluesky — powered by a custom fine-tuned LLM.

---

## 🧠 How It Works

```
football-data.org API
        ↓
  Fetch PL / CL results
        ↓
  GenZ Qwen 2.5 1.5B model
        ↓
  "bro arsenal just COOKED chelsea 2-1 no cap 💀🔥"
        ↓
  Posted to Bluesky automatically
  every 30 minutes
```

---

## 🛠️ Tech Stack

| Component | Tool |
|-----------|------|
| Match data | [football-data.org](https://football-data.org) free tier |
| AI model | Custom fine-tuned [genz-qwen-2.5-1.5B](https://huggingface.co/somendrew/genz-qwen-2.5-1.5B) |
| Posting | [Bluesky](https://bsky.social) via `atproto` |
| Hosting | Hugging Face Spaces (Docker) |
| Scheduler | `schedule` library, runs every 30 mins |

---

## 📁 Project Structure

```
genz-football-bot/
├── bot.py            ← main entry point + scheduler
├── football.py       ← fetch PL/CL finished matches
├── genzify.py        ← load model + generate tweet
├── bluesky.py        ← post to Bluesky
├── Dockerfile        ← container setup
├── requirements.txt  ← dependencies
├── .env              ← secrets (never committed)
└── .gitignore
```

---

## 🔐 Environment Variables

Create a `.env` file locally or add these as Secrets in HF Spaces:

```
FOOTBALL_API_KEY=your_football_data_key
HF_TOKEN=your_huggingface_token
BSKY_HANDLE=yourhandle.bsky.social
BSKY_APP_PASS=your_bluesky_app_password
```

---

## 🚀 Running Locally

```bash
# Clone the repo
git clone https://huggingface.co/spaces/somendrew/genz-football-bot
cd genz-football-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Add your .env file and run
python3 bot.py
```

---

## 📦 Requirements

```
requests
schedule
transformers
torch
accelerate
atproto
python-dotenv
```

---

## 🤖 The Model

The bot uses [`somendrew/genz-qwen-2.5-1.5B`](https://huggingface.co/somendrew/genz-qwen-2.5-1.5B) — a custom fine-tune of Qwen 2.5 1.5B trained to convert boring football results into Gen Z Twitter slang.

**Example:**
```
Input:  Arsenal beat Chelsea 2-1 in the Premier League
Output: bro arsenal just VIOLATED chelsea 2-1 in the prem no cap 💀🔥
```

---

## 📅 Coverage

Currently tracks:
- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 **Premier League**
- 🏆 **UEFA Champions League**

---

## 🔮 Roadmap

- [ ] Add Twitter/X posting when credits reset
- [ ] Add more leagues (La Liga, Serie A, Bundesliga)
- [ ] Add live match updates (not just final scores)
- [ ] Add player goal scorers in the tweet
- [ ] Add image generation for match cards

---

## 👤 Author

Built by [@somendrew](https://huggingface.co/somendrew)