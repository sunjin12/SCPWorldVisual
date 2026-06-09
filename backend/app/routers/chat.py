"""Chat router — SSE streaming and non-streaming endpoints."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.core.personas import get_persona
from app.dependencies import (
    get_embedding_service,
    get_llm_http_client,
    get_storage_service,
)
from app.middleware.auth import verify_google_token
from app.models.schemas import AuthUser, ChatRequest, ChatResponse
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.services.prompt_service import build_prompt, extract_sources
from app.services.rag_service import RAGService
from app.services.response_filter import sanitize

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/api/chat/stream")
async def chat_stream(
    request: ChatRequest,
    user: AuthUser = Depends(verify_google_token),
):
    """
    SSE streaming chat endpoint.

    Streams tokens one-by-one via Server-Sent Events.
    After streaming completes, saves the full response to SQLite.
    """
    storage_svc = get_storage_service()
    llm_client = await get_llm_http_client()
    embedding_svc: EmbeddingService = get_embedding_service()

    memory_svc = MemoryService(
        storage_svc,
        max_turns=settings.MAX_CONVERSATION_TURNS,
    )
    rag_svc = RAGService(storage_svc, embedding_svc)
    llm_svc = LLMService(llm_client)

    async def event_generator():
        full_response = ""
        sources: list[str] = []
        stage = "init"

        def stage_event(s: str) -> str:
            return f"data: {json.dumps({'stage': s}, ensure_ascii=False)}\n\n"

        try:
            stage = "history"
            yield stage_event(stage)
            history = await memory_svc.get_history(
                user.user_id, request.persona_id, request.session_id
            )

            stage = "rag"
            yield stage_event(stage)
            rag_results = await rag_svc.hybrid_search(request.message)
            sources = extract_sources(rag_results)

            stage = "prompt"
            yield stage_event(stage)
            persona = get_persona(request.persona_id)
            messages = build_prompt(persona, rag_results, history, request.message)
            logger.info("📝 Prompt built. Message context length: %d messages", len(messages))

            stage = "llm"
            yield stage_event(stage)
            logger.info("🔮 Calling llm_svc.generate_stream...")
            async for token in llm_svc.generate_stream(
                messages,
                temperature=persona.temperature,
                top_p=persona.top_p,
                frequency_penalty=persona.frequency_penalty,
                presence_penalty=persona.presence_penalty,
            ):
                full_response += token
                event_data = json.dumps(
                    {"token": token, "done": False}, ensure_ascii=False
                )
                yield f"data: {event_data}\n\n"

            stage = "sanitize"
            cleaned_response = sanitize(full_response, request.persona_id)

            stage = "persist"
            await memory_svc.add_turn(
                user.user_id,
                request.persona_id,
                request.session_id,
                request.message,
                cleaned_response,
            )

            done_data = json.dumps(
                {
                    "token": "",
                    "done": True,
                    "sources": sources,
                    "final_text": cleaned_response,
                },
                ensure_ascii=False,
            )
            yield f"data: {done_data}\n\n"
        except Exception as e:
            logger.exception("Chat stream failed at stage=%s: %s", stage, e)
            err_msg = str(e) or type(e).__name__
            error_data = json.dumps(
                {"error": err_msg, "stage": stage, "done": True},
                ensure_ascii=False,
            )
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: AuthUser = Depends(verify_google_token),
):
    """Non-streaming chat endpoint (fallback)."""
    storage_svc = get_storage_service()
    llm_client = await get_llm_http_client()
    embedding_svc: EmbeddingService = get_embedding_service()

    memory_svc = MemoryService(
        storage_svc,
        max_turns=settings.MAX_CONVERSATION_TURNS,
    )
    rag_svc = RAGService(storage_svc, embedding_svc)
    llm_svc = LLMService(llm_client)

    stage = "init"
    try:
        stage = "history"
        history = await memory_svc.get_history(
            user.user_id, request.persona_id, request.session_id
        )

        stage = "rag"
        rag_results = await rag_svc.hybrid_search(request.message)
        sources = extract_sources(rag_results)

        stage = "prompt"
        persona = get_persona(request.persona_id)
        messages = build_prompt(persona, rag_results, history, request.message)

        stage = "llm"
        response_text = await llm_svc.generate(
            messages,
            temperature=persona.temperature,
            top_p=persona.top_p,
            frequency_penalty=persona.frequency_penalty,
            presence_penalty=persona.presence_penalty,
        )

        stage = "sanitize"
        response_text = sanitize(response_text, request.persona_id)

        stage = "persist"
        await memory_svc.add_turn(
            user.user_id,
            request.persona_id,
            request.session_id,
            request.message,
            response_text,
        )
    except Exception as e:
        logger.exception("Chat failed at stage=%s: %s", stage, e)
        raise HTTPException(
            status_code=502,
            detail={"error": str(e), "stage": stage},
        )

    return ChatResponse(
        session_id=request.session_id,
        message=response_text,
        persona_id=request.persona_id,
        sources=sources,
    )
