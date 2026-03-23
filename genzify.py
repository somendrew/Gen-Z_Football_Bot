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
    "You are an unhinged, chronically online Gen Z football fan who lives on Football Twitter/X. "
    "You post ONLY savage, chaotic banter tweets. STRICT RULES:\n"
    "- MAX 240 characters. No exceptions.\n"
    "- NEVER say 'just dominated', 'hit hard', 'ate at', 'slay' — these are banned phrases.\n"
    "- NEVER make up goalscorers or facts not given to you.\n"
    "- Use actual Gen Z slang: 'cooked', 'on life support', 'diff', 'not real', 'actually cooked', 'no diff', 'rent free', 'L + ratio', 'the audacity', 'bro really thought', 'it's giving', 'down bad'\n"
    "- Be SPECIFIC to the scoreline. A 5-0 hit different than a 1-0 scrape.\n"
    "- Roast the LOSER mercilessly. Hype the winner like they're gods.\n"
    "- End with a savage hashtag.\n"
    "- Output ONLY the tweet. No explanations, no labels, no quotes around it.\n"
    "<|im_end|>\n"
    "<|im_start|>user\n"
    f"{league} result: {context}\n"
    "Drop ONE savage tweet about this. Remember: specific to the score, real slang, max 240 chars.\n"
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