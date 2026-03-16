FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

CMD ["python", "bot.py"]
```

---

## STEP 4: Deploy
1. After adding all 3 files, HF Spaces will **automatically build and run** the Docker container
2. Go to the **Logs tab** in your Space to watch it boot up
3. You'll see:
```
   Loading model...
   Model loaded ✅
   Bot is running 🚀