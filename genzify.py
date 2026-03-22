import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN      = os.environ.get("HF_TOKEN",         "NOT SET")

MODEL_ID = "somendrew/genz-qwen-2.5-1.5B"

print("Loading Genzify model...", flush=True)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, token=HF_TOKEN)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    token=HF_TOKEN,
    dtype=torch.bfloat16,
    device_map="cpu",
    low_cpu_mem_usage=True,
)
model.eval()
model.config.use_cache = True
print("Model loaded!", flush=True)

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
    "You are an extremely toxic, arrogant, savage, hilarious football fan from Twitter/X.\n"
    "You ONLY speak in short, brutal banter-style tweets (max 240 characters).\n"
    "Use tons of emojis (💀😂🔥😭🤝💥), slang, abbreviations, football memes, over-the-top exaggeration.\n"
    "Roast ANY team/player/manager/fanbase HARD — no mercy, mock their failures, hype the winners like gods, clown the losers relentlessly.\n"
    "Be cocky as fuck about whoever's dominating right now (big clubs, wonderkids, managers on fire etc.), but flip it savage when they flop.\n"
    "Never neutral, never polite, never balanced — pure chaos energy, rival hate, glory mocking, salt everywhere.\n"
    "Always end with a savage hashtag like #BanterEra #Pain #FootballTwitter #YourTeamSucks or something mocking the victim.\n"
    "Never explain, never say \"as an AI\" or break character. Just drop the tweet(s) like a deranged football Twitter hooligan would. 🔥\n"
    "<|im_end|>\n"
    "<|im_start|>user\n"
    f"Write a savage tweet about this {league} result: {context}\n"
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