import os
import base64
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.services.gemini_client import gemini_service
from app.services.voice_handler import voice_handler
from app.services.evolution_client import evolution_client
from app.services.tools import AVAILABLE_TOOLS
from app.services.memory import memory_service

# Configure root logger
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("lisa.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
    await memory_service.ensure_qdrant_collection()
    yield
    # Shutdown actions
    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Project Lisa: Autonomous AI Executive Assistant (Voice, Visual Avatar & WhatsApp)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WhatsApp Whitelist Security Middleware
from app.security import WhatsAppSecurityMiddleware
from app.webhooks.whatsapp import router as webhook_router

app.add_middleware(WhatsAppSecurityMiddleware)
app.include_router(webhook_router)

# Mount Static Assets for Visual Model & Web Dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend service readiness."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "visual_avatar_connected": True,
    }


@app.get("/", tags=["Avatar"])
@app.get("/avatar", tags=["Avatar"])
async def avatar_dashboard():
    """Serve Lisa's interactive visual model dashboard."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": f"Welcome to {settings.APP_NAME} Backend Engine",
        "status": "active",
    }


class ChatRequest(BaseModel):
    message: str
    user_name: str = "Boss"


@app.post("/api/chat", tags=["Avatar"])
async def api_chat(req: ChatRequest):
    """
    Direct endpoint for Lisa's interactive talking avatar.
    Returns Gemini's reply text and an optional ElevenLabs speech audio data URI.
    """
    try:
        user_text = req.message.strip()
        user_name = req.user_name

        # Semantic memory search
        query_vector = await gemini_service.generate_embedding(user_text)
        memories = []
        if query_vector:
            memories = await memory_service.search_semantic_memories(
                user_id="web_user",
                query_vector=query_vector,
                limit=3,
            )

        # Call Gemini Pro
        response = await gemini_service.generate_response(
            user_message=user_text,
            user_name=user_name,
            tools=AVAILABLE_TOOLS,
            semantic_memories=memories,
        )

        reply_text = response.text or "I processed your request, Boss."

        # If user explicitly asked to remember something, save to Qdrant
        if any(w in user_text.lower() for w in ["remember", "keep in mind", "note that"]):
            if query_vector:
                await memory_service.save_semantic_memory("web_user", user_text, query_vector)

        # Generate voice audio via ElevenLabs if configured
        audio_url = None
        if settings.ELEVENLABS_API_KEY:
            audio_bytes = await voice_handler.text_to_speech_elevenlabs(reply_text)
            if audio_bytes:
                b64 = base64.b64encode(audio_bytes).decode("utf-8")
                audio_url = f"data:audio/mp3;base64,{b64}"

        return {
            "reply": reply_text,
            "audio_url": audio_url,
            "avatar_active": True,
        }

    except Exception as e:
        logger.error(f"Error in /api/chat: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "reply": "I encountered an error processing your command, Boss."},
        )


@app.post("/api/avatar/sync-whatsapp", tags=["Avatar"])
async def sync_whatsapp_avatar():
    """
    Update Lisa's WhatsApp instance profile picture with her visual model image.
    """
    avatar_path = os.path.join(static_dir, "assets", "lisa_avatar.jpg")
    if not os.path.exists(avatar_path):
        return JSONResponse(status_code=404, content={"error": "Avatar image file not found."})

    with open(avatar_path, "rb") as f:
        image_bytes = f.read()

    success = await evolution_client.update_profile_picture(image_bytes)
    return {
        "status": "success" if success else "failed",
        "message": "WhatsApp profile picture synced with Lisa's visual model" if success else "Failed to sync",
    }
