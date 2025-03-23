# Matchmaker Bot (with SQLite + Render)

### 🧠 Features:
- Persistent user storage with SQLite
- Anonymous match/chat
- Hosted on Render (24x7)

### 🚀 Steps to Run:

1. Rename `.env.example` to `.env` and add your Bot Token
2. Run:
```
pip install -r requirements.txt
python main.py
```

### ☁️ Deploy on Render:
1. Push to GitHub
2. Go to [https://render.com](https://render.com) → New Web Service
3. Connect repo → Set build command `pip install -r requirements.txt`
4. Start command: `python main.py`
5. Add env var: `BOT_TOKEN`
6. Done!"# telegaram_bot" 
