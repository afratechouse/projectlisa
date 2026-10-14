import base64
import logging
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger("lisa.evolution")


class EvolutionClient:
    def __init__(self):
        self.base_url = settings.EVOLUTION_API_BASE_URL.rstrip("/")
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance_name = settings.EVOLUTION_INSTANCE_NAME

    def _headers(self):
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json",
        }

    async def send_text_message(self, remote_jid: str, text: str) -> bool:
        """Send a plain text WhatsApp message."""
        url = f"{self.base_url}/message/sendText/{self.instance_name}"
        payload = {
            "number": remote_jid.split("@")[0],
            "text": text,
            "options": {
                "delay": 500,
                "presence": "composing",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, headers=self._headers(), json=payload)
                if res.status_code in (200, 201):
                    logger.info(f"Message sent successfully to {remote_jid}")
                    return True
                else:
                    logger.error(f"Failed to send text message: {res.status_code} - {res.text}")
                    return False
        except Exception as e:
            logger.error(f"Error in send_text_message: {e}")
            return False

    async def send_audio_message(self, remote_jid: str, audio_bytes: bytes) -> bool:
        """Send an audio/voice note message to WhatsApp."""
        url = f"{self.base_url}/message/sendWhatsAppAudio/{self.instance_name}"
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        payload = {
            "number": remote_jid.split("@")[0],
            "audio": f"data:audio/mp3;base64,{b64_audio}",
            "options": {
                "delay": 800,
                "presence": "recording",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=self._headers(), json=payload)
                if res.status_code in (200, 201):
                    logger.info(f"Audio sent successfully to {remote_jid}")
                    return True
                else:
                    logger.error(f"Failed to send audio message: {res.status_code} - {res.text}")
                    return False
        except Exception as e:
            logger.error(f"Error in send_audio_message: {e}")
            return False

    async def get_base64_media(self, message_id: str) -> Optional[bytes]:
        """Fetch media file bytes from Evolution API by message ID."""
        url = f"{self.base_url}/chat/getBase64FromMediaMessage/{self.instance_name}"
        payload = {
            "message": {
                "key": {
                    "id": message_id,
                }
            },
            "convertToMp4": False,
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(url, headers=self._headers(), json=payload)
                if res.status_code == 200:
                    data = res.json()
                    base64_data = data.get("base64")
                    if base64_data:
                        # Strip data URI header if present
                        if "," in base64_data:
                            base64_data = base64_data.split(",")[1]
                        return base64.b64decode(base64_data)
                logger.error(f"Failed to fetch base64 media: {res.status_code} - {res.text}")
                return None
        except Exception as e:
            logger.error(f"Error fetching base64 media: {e}")
            return None

    async def send_video_message(self, remote_jid: str, video_url: str, caption: str = "") -> bool:
        """Send a video message (e.g. talking avatar clip) to WhatsApp."""
        url = f"{self.base_url}/message/sendMedia/{self.instance_name}"
        payload = {
            "number": remote_jid.split("@")[0],
            "mediatype": "video",
            "mimetype": "video/mp4",
            "caption": caption,
            "media": video_url,
        }

        try:
            async with httpx.AsyncClient(timeout=40.0) as client:
                res = await client.post(url, headers=self._headers(), json=payload)
                if res.status_code in (200, 201):
                    logger.info(f"Video sent successfully to {remote_jid}")
                    return True
                else:
                    logger.error(f"Failed to send video message: {res.status_code} - {res.text}")
                    return False
        except Exception as e:
            logger.error(f"Error in send_video_message: {e}")
            return False

    async def update_profile_picture(self, image_bytes: bytes) -> bool:
        """Update Lisa's WhatsApp instance profile picture with her visual model."""
        url = f"{self.base_url}/chat/updateProfilePicture/{self.instance_name}"
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "picture": f"data:image/jpeg;base64,{b64_image}"
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, headers=self._headers(), json=payload)
                if res.status_code in (200, 201):
                    logger.info("Successfully updated Lisa's WhatsApp profile picture.")
                    return True
                else:
                    logger.error(f"Failed to update profile picture: {res.status_code} - {res.text}")
                    return False
        except Exception as e:
            logger.error(f"Error updating profile picture: {e}")
            return False


evolution_client = EvolutionClient()
