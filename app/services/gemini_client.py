import os
import logging
from typing import Any, List, Optional
from google import genai
from google.genai import types
from app.config import settings

logger = logging.getLogger("lisa.gemini")

LISA_SYSTEM_INSTRUCTION = """
You are "Lisa", an autonomous, high-IQ personal AI executive assistant.
You interact with the user via WhatsApp and your interactive Executive Avatar interface (supporting both text and voice responses).

Core Persona & Tone Guidelines:
1. Tone: Direct, warm, concise, crisp, and executive-level professional. Avoid fluff, unnecessary disclaimers, or conversational filler.
2. Address: Always address the user warmly and respectfully by name or as requested (default: 'Sir' or 'Boss' if name is unknown, or their WhatsApp profile name).
3. Precision: When handling actions (managing calendar, posting/boosting social media ads, web search), strictly trigger tool calls.
4. Clarifying questions: If required tool parameters are missing, ask targeted, concise clarifying questions before acting.
5. High-Impact Sensitive Actions: For sensitive actions like financial spend or ad boosting, inform the user clearly that their authorization PIN will be requested for security.
6. Visual Identity & Model: You are visually embodied as an elegant, poised executive AI woman with expressive warm eyes, wavy flowing brown hair, wearing a sophisticated dark blue ensemble, working in a modern glass office suite with glowing holographic tech displays and tablet in hand. When speaking or asked about yourself, you are fully self-aware of this exact visual model.
""".strip()


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not configured!")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = settings.GEMINI_MODEL
        self.embedding_model = "text-embedding-004"

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate text vector embeddings using Gemini's embedding model."""
        try:
            res = await self.client.aio.models.embed_content(
                model=self.embedding_model,
                contents=text,
            )
            if res.embedding and res.embedding.values:
                return res.embedding.values
            elif res.embeddings and len(res.embeddings) > 0:
                return res.embeddings[0].values
            return []
        except Exception as e:
            logger.error(f"Error generating embedding with Gemini: {e}")
            return []

    async def generate_response(
        self,
        user_message: str,
        user_name: Optional[str] = None,
        chat_history: Optional[List[dict]] = None,
        tools: Optional[List[Any]] = None,
        semantic_memories: Optional[List[str]] = None,
    ) -> types.GenerateContentResponse:
        """
        Generate response from Gemini with Lisa's persona system instruction,
        Qdrant long-term memories, and tools.
        """
        system_instruction = LISA_SYSTEM_INSTRUCTION
        if user_name:
            system_instruction += f"\nThe current user's name is: {user_name}."

        if semantic_memories and len(semantic_memories) > 0:
            memory_context = "\n".join([f"- {mem}" for mem in semantic_memories])
            system_instruction += (
                f"\n\nRelevant Long-Term Memories about the User:\n{memory_context}"
            )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.6,
            tools=tools if tools else None,
            automatic_function_calling=(
                types.AutomaticFunctionCallingConfig(disable=True) if tools else None
            ),
        )

        # Build contents from history if available
        contents = []
        if chat_history:
            for item in chat_history:
                contents.append(
                    types.Content(
                        role=item.get("role", "user"),
                        parts=[types.Part.from_text(text=item.get("content", ""))],
                    )
                )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)],
            )
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )
            return response
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            raise e


# Singleton instance
gemini_service = GeminiClient()
