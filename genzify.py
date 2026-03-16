import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from config import HF_TOKEN

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