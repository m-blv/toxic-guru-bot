# toxic-guru-bot

🤖 **Himalayan Guru Telegram Bot (The Cynical Shrink)**  
An asynchronous Telegram bot powered by the advanced **Llama 3.3 70B** LLM. It acts as a cynical digital mystic, an esoteric guru, and a rogue therapist with a black belt in sarcasm. The bot maintains a rock-solid roleplay persona, addresses users directly, and ironically tears down mental illusions, laziness, and procrastination.

---

## ✨ Architecture & Key Features

* **Advanced AI Engine:** Seamless integration with the `llama-3.3-70b-versatile` model via Groq's high-speed API.
* **Persistent Context (Memory):** Local conversation history tracking (up to 20 messages per user) powered by SQLite, featuring automated context pruning to optimize token usage.
* **Thread-Safe DB Ops:** Heavy SQLite read/write operations are offloaded to isolated background threads via `asyncio.to_thread`, keeping the core async event loop entirely non-blocking.
* **Environment Isolation:** Zero hardcoded secrets. All sensitive keys and tokens are strictly decoupled into environment variables via a `.env` file.
* **Production-Ready:** Includes a ready-to-use service configuration file for daemonization, process control, and persistent autostart via `systemd` on Linux servers.

---

## 🛠 Tech Stack

* **Language:** Python 3.10+
* **Framework:** `aiogram 3.x` (Asynchronous Telegram Bot API wrapper)
* **AI Client:** `openai` (Async client, Groq API compatible)
* **Database:** `sqlite3`
* **Target Environment:** Linux Ubuntu, `systemd`, Python `venv`

---

## 🚀 Quick Start & Deployment

### 1. Server Environment Setup (Linux)
```bash
mkdir toxic_bot && cd toxic_bot
python3 -m venv venv
source venv/bin/activate
pip install aiogram openai

```

### 2. Configuration

Create a `.env` file in the project root directory on your server and add your API tokens (this file is securely excluded from version control via `.gitignore`):

```env
TG_TOKEN=your_telegram_bot_token_from_botfather
GROQ_API_KEY=your_groq_api_key

```

### 3. Autostart Daemon Setup (systemd)

Create a system service configuration file at `/etc/systemd/system/toxic_bot.service`:

```ini
[Unit]
Description=Toxic Guru Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/toxic_bot
EnvironmentFile=/root/toxic_bot/.env
ExecStart=/root/toxic_bot/venv/bin/python3 bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

```

Initialize, enable, and spin up the service on your server:

```bash
systemctl daemon-reload
systemctl enable toxic_bot
systemctl start toxic_bot

```

---

## 📊 Service Management

* **Check status and runtime logs:**
`systemctl status toxic_bot`
* **Restart the bot after making code edits:**
`systemctl restart toxic_bot`
* **Monitor incoming AI logs and stream output in real-time:**
`journalctl -u toxic_bot -f`

```
