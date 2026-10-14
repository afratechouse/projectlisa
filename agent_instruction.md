```markdown
# Project "Lisa" – Autonomous Agent Implementation Blueprint

## 1. Project Overview & Objective
You are acting as the Lead AI Architect and Senior Full-Stack Engineer. Your task is to build, configure, and deploy **Project "Lisa"**, a secure, voice-and-text interactive personal AI assistant agent. Lisa runs on **Gemini Pro**, connects via **Evolution API (WhatsApp Business)**, uses **FastAPI** as the backend engine, **Redis** for state/session management, **Qdrant** for long-term memory, and incorporates a strict **Human-in-the-Loop (HITL) PIN authorization** flow for sensitive operations.

---

## 2. Technology Stack Specifications
- **Core Orchestrator:** Python 3.10+, FastAPI (Async Webhook & REST API)
- **AI Model:** Google Gemini Pro (`google-generativeai`)
- **Messaging Gateway:** Evolution API (Dockerized WhatsApp Business API)
- **Databases:** 
  - Redis (Session state, conversation history, PIN verification states)
  - Qdrant (Vector database for long-term semantic user memory)
- **Voice Pipeline:** Deepgram (STT - Speech-to-Text) + ElevenLabs (TTS - Text-to-Speech)
- **Security:** HMAC signature verification, phone number whitelisting middleware, bcrypt PIN hashing, HashiCorp Vault / `.env` isolation.

---

## 3. Step-by-Step Autonomous Execution Checklist for the AI

### Phase 1: Project Scaffolding & Structure
1. Create the modular directory structure:
   ```text
   project-lisa/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py                # FastAPI entry point
   │   ├── config.py              # Environment variables & settings
   │   ├── security.py            # Whitelisting & PIN authentication logic
   │   ├── services/
   │   │   ├── gemini_client.py   # Gemini Pro interaction & system prompt
   │   │   ├── voice_handler.py   # Deepgram & ElevenLabs integration
   │   │   ├── memory.py          # Redis & Qdrant memory layers
   │   │   └── tools.py           # Function calling schemas (Meta Ads, Calendar, Search)
   │   └── webhooks/
   │       └── whatsapp.py        # Evolution API webhook listener
   ├── docker-compose.yml         # Evolution API, Redis, Qdrant
   ├── requirements.txt
   └── .env.example

```

2. Populate `requirements.txt` with required packages (`fastapi`, `uvicorn`, `requests`, `python-dotenv`, `google-generativeai`, `redis`, `qdrant-client`, `bcrypt`).

### Phase 2: Core FastAPI & Gemini Integration (`app/main.py` & `app/services/gemini_client.py`)

1. Initialize FastAPI app with CORS middleware.
2. Build the Gemini Pro wrapper incorporating Lisa's core persona system prompt:
* Direct, warm, concise, professional tone.
* Always addresses the user by name.
* Strict rule to trigger tool calls or ask clarifying questions when parameters are missing.



### Phase 3: Security & Whitelisting Middleware (`app/security.py`)

1. Implement FastAPI middleware to inspect incoming WhatsApp webhook payloads.
2. Validate sender `remoteJid` against the whitelist stored in environment variables (`AUTHORIZED_PHONE_NUMBER`). Drop unlisted requests with HTTP 200 and a warning log.
3. Implement 4-digit master PIN verification using `bcrypt` for sensitive tool executions (e.g., Meta Ads spending).

### Phase 4: WhatsApp Webhook & Voice Pipeline (`app/webhooks/whatsapp.py` & `app/services/voice_handler.py`)

1. Create a POST endpoint `/webhook/evolution` to handle `MESSAGES_UPSERT` events from Evolution API.
2. If the message type is audio (`audioMessage`):
* Fetch base64 audio stream from Evolution API.
* Transcribe audio via Deepgram API.


3. Feed transcribed text or direct text message into Gemini Pro along with Redis short-term context.
4. If the response requires voice output, convert text to `.mp3` via ElevenLabs and send back via Evolution API's `/message/sendWhatsAppAudio` endpoint.

### Phase 5: Tool Calling & HITL State Machine (`app/services/tools.py`)

1. Define the 4 core tool schemas:
* `publish_video_to_social_media`
* `boost_social_media_post` (Requires HITL PIN)
* `manage_calendar_and_reminders`
* `web_search_and_summarize`


2. Implement the state interception logic: When `boost_social_media_post` is invoked, cache arguments in Redis under status `PENDING_AUTH_PIN`, and reply to user asking for their secure PIN.

---

## 4. Coding & Architecture Guidelines

* Write clean, fully typed asynchronous Python code (`async def`).
* Handle all network errors gracefully with try/except blocks and descriptive logging.
* Never hardcode API keys; always reference `os.getenv()`.
* Ensure all webhook endpoints return immediate HTTP 200 responses to prevent gateway timeout loops.

```

```