import os
import base64
import logging
import httpx
from typing import Optional
from app.config import settings

logger = logging.getLogger("lisa.voice")


class VoiceHandler:
    def __init__(self):
        self.deepgram_api_key = settings.DEEPGRAM_API_KEY
        self.elevenlabs_api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID

    async def transcribe_audio_deepgram(self, audio_bytes: bytes, mimetype: str = "audio/ogg") -> Optional[str]:
        """
        Transcribe audio bytes using Deepgram's REST API.
        """
        if not self.deepgram_api_key:
            logger.warning("DEEPGRAM_API_KEY not configured. Cannot transcribe audio.")
            return None

        url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"
        headers = {
            "Authorization": f"Token {self.deepgram_api_key}",
            "Content-Type": mimetype,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, content=audio_bytes)
                if response.status_code == 200:
                    data = response.json()
                    transcript = (
                        data.get("results", {})
                        .get("channels", [{}])[0]
                        .get("alternatives", [{}])[0]
                        .get("transcript", "")
                    )
                    logger.info(f"Deepgram transcription successful: '{transcript}'")
                    return transcript
                else:
                    logger.error(f"Deepgram API error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Exception during Deepgram transcription: {e}", exc_info=True)
            return None

    async def text_to_speech_elevenlabs(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech audio bytes using ElevenLabs API.
        """
        if not self.elevenlabs_api_key:
            logger.warning("ELEVENLABS_API_KEY not configured. Cannot generate speech.")
            return None

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    logger.info("ElevenLabs audio generation successful.")
                    return response.content
                else:
                    logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Exception during ElevenLabs TTS: {e}", exc_info=True)
            return None


voice_handler = VoiceHandler()
