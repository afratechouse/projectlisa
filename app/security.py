import json
import logging
import bcrypt
from starlette.responses import JSONResponse
from app.config import settings

logger = logging.getLogger("lisa.security")


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verify if the 4-digit plain PIN matches the bcrypt hash."""
    if not hashed_pin:
        logger.warning("MASTER_PIN_HASH is not set. PIN verification failing safely.")
        return False
    try:
        return bcrypt.checkpw(plain_pin.strip().encode("utf-8"), hashed_pin.strip().encode("utf-8"))
    except Exception as e:
        logger.error(f"Error checking PIN hash: {e}")
        return False


def hash_pin(plain_pin: str) -> str:
    """Generate a bcrypt hash for a PIN."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_pin.strip().encode("utf-8"), salt).decode("utf-8")


def is_authorized_phone(sender_jid_or_phone: str) -> bool:
    """
    Check if incoming sender matches AUTHORIZED_PHONE_NUMBER.
    remoteJid example: '8801700000000@s.whatsapp.net' or '8801700000000'
    """
    if not sender_jid_or_phone:
        return False

    clean_sender = sender_jid_or_phone.split("@")[0].strip().replace("+", "")
    authorized = settings.AUTHORIZED_PHONE_NUMBER.strip().replace("+", "")

    if authorized in ("8801XXXXXXXXX", ""):
        logger.warning("AUTHORIZED_PHONE_NUMBER is not set or using default placeholder.")

    return clean_sender == authorized


class WhatsAppSecurityMiddleware:
    """
    Pure ASGI Middleware that intercepts incoming webhook events (from Evolution API).
    Validates sender remoteJid against AUTHORIZED_PHONE_NUMBER.
    If unauthorized, immediately returns HTTP 200 to prevent WhatsApp gateway timeout loops.
    Safely buffers and replays the request body for downstream route handlers.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] == "http"
            and scope["path"].startswith("/webhook/evolution")
            and scope.get("method") == "POST"
        ):
            # Buffer the incoming request body
            body_chunks = []
            more_body = True
            while more_body:
                message = await receive()
                if message["type"] == "http.request":
                    body_chunks.append(message.get("body", b""))
                    more_body = message.get("more_body", False)
                else:
                    break

            body_bytes = b"".join(body_chunks)

            # Security inspection
            try:
                if body_bytes:
                    payload = json.loads(body_bytes.decode("utf-8"))
                    sender = None
                    if "data" in payload and isinstance(payload["data"], dict):
                        key = payload["data"].get("key", {})
                        sender = key.get("remoteJid") or payload["data"].get("sender")
                    elif "sender" in payload:
                        sender = payload.get("sender")

                    if sender:
                        # Skip WhatsApp status broadcasts
                        if "status@broadcast" in sender:
                            response = JSONResponse(
                                status_code=200,
                                content={"status": "ignored", "reason": "status_broadcast"},
                            )
                            await response(scope, receive, send)
                            return

                        # Check whitelist authorization
                        if not is_authorized_phone(sender):
                            logger.warning(
                                f"SECURITY ALERT: Dropped unauthorized request from sender: {sender}"
                            )
                            response = JSONResponse(
                                status_code=200,
                                content={"status": "dropped", "reason": "unauthorized_sender"},
                            )
                            await response(scope, receive, send)
                            return

            except Exception as e:
                logger.error(f"Error parsing webhook payload in security middleware: {e}")
                response = JSONResponse(
                    status_code=200,
                    content={"status": "error", "message": "Failed to parse webhook payload"},
                )
                await response(scope, receive, send)
                return

            # Re-supply the buffered body to downstream handlers
            sent_body = False

            async def buffered_receive():
                nonlocal sent_body
                if not sent_body:
                    sent_body = True
                    return {"type": "http.request", "body": body_bytes, "more_body": False}
                return {"type": "http.request", "body": b"", "more_body": False}

            await self.app(scope, buffered_receive, send)
            return

        await self.app(scope, receive, send)
