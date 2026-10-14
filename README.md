# Project Lisa – Autonomous Personal AI Executive Assistant

Lisa is an autonomous, high-IQ personal AI executive assistant designed to run 24/7 over **WhatsApp (via Evolution API)** with full support for **Voice Notes** (Deepgram STT & ElevenLabs TTS), **Gemini Pro** intelligence, **Redis** session memory, and **Human-in-the-Loop (HITL) PIN Authorization** for critical operations.

---

## 🏗️ Architecture & Features

1. **Dual Interaction Modes**:
   - **Text Chat:** Fast, concise, executive replies.
   - **Voice Notes:** Incoming `.ogg`/voice notes are transcribed via **Deepgram Nova-2**. If requested via voice, Lisa responds in realistic spoken voice via **ElevenLabs Multilingual**.
2. **Security & Whitelisting**:
   - Incoming webhook middleware filters calls by `AUTHORIZED_PHONE_NUMBER`.
   - Unauthorized numbers are instantly discarded with `HTTP 200` to prevent WhatsApp gateway retries.
3. **Autonomous Tool Calling**:
   - `publish_video_to_social_media`
   - `boost_social_media_post` (Meta Ads spend - requires PIN authorization)
   - `manage_calendar_and_reminders`
   - `web_search_and_summarize`
4. **Official Visual Model & Interactive Talking Avatar**:
   - Lisa's official visual appearance is embedded as an executive AI avatar with holographic displays.
   - **Interactive Web Studio (`http://localhost:8000/avatar` or `/`)**: Real-time talking avatar with synchronized ElevenLabs voice playback, pulsing holographic soundwaves, microphone speech input, and dynamic speech bubbles.
   - **Talking Video Clips on WhatsApp**: Ability to generate and send video notes via avatar video pipeline.
   - **WhatsApp Avatar Sync**: Syncs Lisa's exact visual model directly to Evolution API's profile picture.
5. **Semantic Long-Term Memory (Qdrant) & Session Context (Redis)**:
   - Redis manages real-time session history, context caching, and 5-minute PIN verification timers.
   - Qdrant vector database stores semantic memories and user facts using Gemini `text-embedding-004` embeddings, enabling Lisa to retain long-term memory across sessions.
6. **Human-in-the-Loop (HITL) State Machine**:
   - When a financial or sensitive action (e.g., boosting a post) is triggered, Lisa caches the parameters into Redis under state `pending_auth` and asks the user for their 4-digit Master PIN.
   - Upon entering the matching PIN (verified via `bcrypt`), Lisa executes the action and confirms completion.

---

## 📁 Project Structure

```text
asistant-lisa/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI entry point & CORS
│   ├── config.py                # Pydantic Settings & environment variables
│   ├── security.py              # Whitelisting middleware & bcrypt PIN validation
│   ├── services/
│   │   ├── gemini_client.py     # Gemini Pro wrapper & Lisa persona
│   │   ├── tools.py             # 4 core tools & HITL rules
│   │   ├── memory.py            # Redis short-term context & state machine
│   │   ├── voice_handler.py     # Deepgram (STT) & ElevenLabs (TTS)
│   │   └── evolution_client.py  # Evolution API WhatsApp integration
│   └── webhooks/
│       └── whatsapp.py          # /webhook/evolution listener
├── docker-compose.yml           # Redis, Qdrant, Evolution API containers
├── requirements.txt             # Python dependencies
├── generate_pin_hash.py         # Utility to generate bcrypt PIN hashes
├── .env.example                 # Environment configuration template
└── agent_instruction.md         # Original project blueprint
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- Docker & Docker Compose (for Evolution API, Redis, and Qdrant)

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Update your keys in `.env`:
- `AUTHORIZED_PHONE_NUMBER`: Your WhatsApp number with country code (e.g., `8801700000000`).
- `GEMINI_API_KEY`: Google AI Studio Gemini API key.
- `DEEPGRAM_API_KEY` & `ELEVENLABS_API_KEY`: Voice pipeline credentials.
- `MASTER_PIN_HASH`: Generate using:
  ```bash
  python generate_pin_hash.py 1234
  ```

### 3. Start Support Services (Docker)
```bash
docker compose up -d
```
This boots:
- **Redis:** `localhost:6379`
- **Qdrant:** `localhost:6333`
- **Evolution API:** `localhost:8080`

### 4. Install Dependencies & Run Backend
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Connect WhatsApp in Evolution API
1. Open Evolution API manager or send a POST request to `/instance/create` to pair your WhatsApp account via QR code.
2. Set the Evolution webhook URL to:
   ```
   http://<your-server-or-ngrok-ip>:8000/webhook/evolution
   ```
   and subscribe to `MESSAGES_UPSERT`.
