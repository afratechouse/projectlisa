import os
import base64
import logging
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger("lisa.avatar_video")


class AvatarVideoService:
    """
    Service to generate animated talking avatar videos from Lisa's visual model
    combined with ElevenLabs TTS speech audio. Supports D-ID, HeyGen, or local pipeline.
    """

    def __init__(self):
        self.avatar_image_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "static", "assets", "lisa_avatar.jpg"
        )
        self.did_api_key = os.getenv("DID_API_KEY")

    def get_avatar_base64(self) -> Optional[str]:
        """Read and encode Lisa's avatar image as Base64."""
        if not os.path.exists(self.avatar_image_path):
            logger.error(f"Avatar image not found at {self.avatar_image_path}")
            return None
        with open(self.avatar_image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def generate_talking_video(
        self,
        text: str,
        audio_url: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a talking video of Lisa using D-ID or configured avatar engine.
        Returns the video MP4 download URL.
        """
        if not self.did_api_key:
            logger.info("DID_API_KEY not set. Talking video generation requires D-ID/HeyGen API key.")
            return None

        url = "https://api.d-id.com/talks"
        headers = {
            "Authorization": f"Basic {self.did_api_key}",
            "Content-Type": "application/json",
        }

        # If we have a public or hosted avatar URL, use it; otherwise use source_url
        avatar_b64 = self.get_avatar_base64()
        if not avatar_b64:
            return None

        payload = {
            "source_url": f"data:image/jpeg;base64,{avatar_b64}",
            "script": {
                "type": "text",
                "subtitles": False,
                "provider": {
                    "type": "elevenlabs",
                    "voice_id": settings.ELEVENLABS_VOICE_ID,
                },
                "input": text,
            },
            "config": {
                "fluent": True,
                "pad_audio": 0.0,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code in (200, 201):
                    talk_id = res.json().get("id")
                    logger.info(f"D-ID talk created with ID: {talk_id}. Polling for render...")
                    # Poll for video completion
                    for _ in range(30):
                        import asyncio
                        await asyncio.sleep(2)
                        status_res = await client.get(f"{url}/{talk_id}", headers=headers)
                        if status_res.status_code == 200:
                            data = status_res.json()
                            if data.get("status") == "done":
                                return data.get("result_url")
                            elif data.get("status") == "error":
                                logger.error(f"D-ID render error: {data}")
                                return None
                    return None
                else:
                    logger.error(f"Failed to initiate D-ID talk: {res.status_code} - {res.text}")
                    return None
        except Exception as e:
            logger.error(f"Exception during talking video generation: {e}")
            return None


avatar_video_service = AvatarVideoService()
