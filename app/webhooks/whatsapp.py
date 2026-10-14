import logging
from fastapi import APIRouter, Request, BackgroundTasks
from starlette.responses import JSONResponse

from app.services.gemini_client import gemini_service
from app.services.voice_handler import voice_handler
from app.services.evolution_client import evolution_client
from app.services.memory import memory_service
from app.services.tools import AVAILABLE_TOOLS, TOOL_MAPPING, HITL_PROTECTED_TOOLS
from app.security import verify_pin
from app.config import settings

logger = logging.getLogger("lisa.webhook")
router = APIRouter(prefix="/webhook", tags=["Webhook"])


async def execute_tool_call(tool_name: str, args: dict) -> dict:
    """Safely execute a mapped Python tool."""
    tool_func = TOOL_MAPPING.get(tool_name)
    if not tool_func:
        return {"status": "error", "message": f"Tool '{tool_name}' not found."}
    try:
        result = await tool_func(**args)
        return result
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


async def process_incoming_message(payload: dict):
    """
    Background worker to process incoming Evolution API WhatsApp webhook messages.
    Handles text, voice transcription, Gemini generation, HITL PIN flow, Qdrant memory, and replies.
    """
    try:
        event = payload.get("event")
        if event != "messages.upsert":
            logger.debug(f"Ignoring event type: {event}")
            return

        data = payload.get("data", {})
        key = data.get("key", {})

        # Ignore messages sent by Lisa herself
        if key.get("fromMe", False):
            return

        remote_jid = key.get("remoteJid", "")
        message_id = key.get("id", "")
        push_name = data.get("pushName", "Boss")
        message_content = data.get("message", {})

        is_audio = False
        user_text = ""

        # 1. Audio message extraction
        if "audioMessage" in message_content:
            is_audio = True
            logger.info(f"Incoming audio message detected from {remote_jid}")
            audio_bytes = await evolution_client.get_base64_media(message_id)
            if audio_bytes:
                mimetype = message_content["audioMessage"].get("mimetype", "audio/ogg; codecs=opus")
                user_text = await voice_handler.transcribe_audio_deepgram(audio_bytes, mimetype=mimetype)
            else:
                logger.error("Failed to retrieve audio bytes from Evolution API.")
                await evolution_client.send_text_message(
                    remote_jid, "I could not retrieve your voice note. Please try again."
                )
                return

        # 2. Text message extraction
        elif "conversation" in message_content:
            user_text = message_content["conversation"]
        elif "extendedTextMessage" in message_content:
            user_text = message_content["extendedTextMessage"].get("text", "")

        user_text = (user_text or "").strip()
        if not user_text:
            logger.info("Empty message received or unsupported message type.")
            return

        logger.info(f"Processing message from {remote_jid} ({push_name}): '{user_text}'")
        session_id = remote_jid.split("@")[0]

        # -------------------------------------------------------------
        # HITL PIN Check (If an action is waiting for authorization)
        # -------------------------------------------------------------
        pending_action = await memory_service.get_pending_action(session_id)
        if pending_action:
            clean_input = "".join(filter(str.isdigit, user_text))
            if len(clean_input) == 4 and verify_pin(clean_input, settings.MASTER_PIN_HASH):
                await memory_service.clear_pending_action(session_id)
                tool_name = pending_action.get("tool_name", "")
                tool_args = pending_action.get("args", {})
                
                # Execute the HITL-authorized tool
                tool_result = await execute_tool_call(tool_name, tool_args)
                result_msg = tool_result.get("message", "Action completed successfully.")
                
                success_msg = f"✅ PIN verified, {push_name}.\n\n{result_msg}"
                await memory_service.append_chat_message(session_id, "user", f"[PIN Provided: Authorized {tool_name}]")
                await memory_service.append_chat_message(session_id, "assistant", success_msg)
                await evolution_client.send_text_message(remote_jid, success_msg)
                return
            elif len(clean_input) == 4:
                error_msg = f"❌ Incorrect authorization PIN, {push_name}. Please provide the correct 4-digit master PIN to proceed with {pending_action.get('tool_name')}."
                await evolution_client.send_text_message(remote_jid, error_msg)
                return

        # -------------------------------------------------------------
        # Qdrant Semantic Memory Retrieval
        # -------------------------------------------------------------
        query_vector = await gemini_service.generate_embedding(user_text)
        semantic_memories = []
        if query_vector:
            semantic_memories = await memory_service.search_semantic_memories(
                user_id=session_id,
                query_vector=query_vector,
                limit=3,
            )

        # -------------------------------------------------------------
        # Gemini Tool Calling & Inference
        # -------------------------------------------------------------
        chat_history = await memory_service.get_chat_history(session_id, limit=6)

        response = await gemini_service.generate_response(
            user_message=user_text,
            user_name=push_name,
            chat_history=chat_history,
            tools=AVAILABLE_TOOLS,
            semantic_memories=semantic_memories,
        )

        reply_text = ""

        # Check if model made function / tool calls
        if response.function_calls:
            for call in response.function_calls:
                call_name = call.name
                call_args = dict(call.args) if call.args else {}
                logger.info(f"Gemini invoked tool: {call_name} with args: {call_args}")

                # Check if tool is HITL protected (e.g. boost_social_media_post)
                if call_name in HITL_PROTECTED_TOOLS:
                    # Save pending action in Redis and prompt user for PIN
                    await memory_service.set_pending_action(
                        session_id=session_id,
                        action_data={
                            "tool_name": call_name,
                            "args": call_args,
                            "user_name": push_name,
                        },
                        ttl=300,  # 5 minutes expiry
                    )
                    reply_text = (
                        f"🔒 **Authorization Required**, {push_name}.\n\n"
                        f"To execute `{call_name}` (Budget: ${call_args.get('budget_usd', 'N/A')}), "
                        f"please enter your 4-digit Master Security PIN."
                    )
                    break
                else:
                    # Execute non-sensitive tool immediately
                    tool_result = await execute_tool_call(call_name, call_args)
                    reply_text = tool_result.get("message", f"Action '{call_name}' completed.")

        # If no tool was called, or response has text
        if not reply_text:
            reply_text = response.text or "I processed your request, but received no text response."

        # Store in Redis short-term memory
        await memory_service.append_chat_message(session_id, "user", user_text)
        await memory_service.append_chat_message(session_id, "assistant", reply_text)

        # If user explicitly instructed to remember something, persist to Qdrant
        lower_text = user_text.lower()
        if any(trigger in lower_text for trigger in ["remember that", "remember this", "keep in mind that", "note that"]):
            if query_vector:
                await memory_service.save_semantic_memory(
                    user_id=session_id,
                    text=user_text,
                    vector=query_vector,
                )

        # -------------------------------------------------------------
        # Reply dispatch (Video, Voice note or Text)
        # -------------------------------------------------------------
        from app.services.avatar_video import avatar_video_service

        is_video_requested = any(w in user_text.lower() for w in ["video", "ভিডিও", "avatar video", "talking avatar"])
        sent_video = False

        if is_video_requested and avatar_video_service.did_api_key:
            video_url = await avatar_video_service.generate_talking_video(reply_text)
            if video_url:
                await evolution_client.send_video_message(remote_jid, video_url, caption=reply_text)
                sent_video = True

        if not sent_video:
            if is_audio and settings.ELEVENLABS_API_KEY:
                speech_bytes = await voice_handler.text_to_speech_elevenlabs(reply_text)
                if speech_bytes:
                    await evolution_client.send_audio_message(remote_jid, speech_bytes)
                else:
                    await evolution_client.send_text_message(remote_jid, reply_text)
            else:
                await evolution_client.send_text_message(remote_jid, reply_text)

    except Exception as e:
        logger.error(f"Error processing incoming WhatsApp webhook: {e}", exc_info=True)


@router.post("/evolution")
async def evolution_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook endpoint for Evolution API events.
    Returns HTTP 200 immediately to satisfy gateway timeout rules.
    """
    try:
        payload = await request.json()
        background_tasks.add_task(process_incoming_message, payload)
        return JSONResponse(status_code=200, content={"status": "received"})
    except Exception as e:
        logger.error(f"Error receiving webhook: {e}")
        return JSONResponse(status_code=200, content={"status": "error", "detail": str(e)})
