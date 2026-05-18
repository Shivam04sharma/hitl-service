"""Integrated chat endpoint with Vertex AI and HITL triggers."""

from __future__ import annotations

import structlog
from deps import get_db, verify_token
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from services import review_store
from services.sensitive_detector import detect_sensitive_data
from services.complexity_analyzer import analyze_query_complexity, suggest_model
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(dependencies=[Depends(verify_token)])


class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    pair_count: int
    current_model: str = "gemini-2.0-flash-lite"


class ChatResponse(BaseModel):
    message: str | None = None
    hitl_popup: dict | None = None


class ConversationStore:
    """In-memory conversation storage."""
    _conversations: dict[str, list[dict]] = {}
    
    @classmethod
    def add_message(cls, conversation_id: str, role: str, content: str):
        if conversation_id not in cls._conversations:
            cls._conversations[conversation_id] = []
        cls._conversations[conversation_id].append({"role": role, "content": content})
    
    @classmethod
    def get_messages(cls, conversation_id: str) -> list[dict]:
        return cls._conversations.get(conversation_id, [])
    
    @classmethod
    def get_pair_count(cls, conversation_id: str) -> int:
        messages = cls.get_messages(conversation_id)
        return len([m for m in messages if m["role"] == "user"])


async def generate_vertex_ai_response(conversation_id: str, message: str, model_name: str = "gemini-2.0-flash-lite") -> str:
    """Generate response using Vertex AI."""
    try:
        import os
        import vertexai
        from vertexai.preview.generative_models import GenerativeModel
        from config import settings
        
        # Set credentials
        if settings.google_application_credentials:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
        
        # Initialize Vertex AI
        vertexai.init(
            project=settings.vertex_ai_project_id,
            location=settings.vertex_ai_location
        )
        
        # Get conversation history
        history = ConversationStore.get_messages(conversation_id)
        
        # Build context from last 5 messages
        context = "\n".join([f"{m['role']}: {m['content']}" for m in history[-5:]])
        
        # Generate response
        model = GenerativeModel(model_name)
        
        system_instruction = "You are a helpful AI assistant. Provide direct, conversational answers. Do not use bullet points, lists, or ask clarifying questions unless absolutely necessary. Give complete, natural responses."
        
        if context:
            full_prompt = f"{system_instruction}\n\nPrevious conversation:\n{context}\n\nUser: {message}\nAssistant:"
        else:
            full_prompt = f"{system_instruction}\n\nUser: {message}\nAssistant:"
        
        response = model.generate_content(full_prompt)
        return response.text
        
    except Exception as e:
        logger.error("vertex_ai_error", error=str(e))
        return f"I'm having trouble processing your request. Error: {str(e)}"


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Main chat endpoint with integrated HITL triggers.
    
    Flow:
    1. Check sensitive data
    2. Check model switch recommendation
    3. Check chat compression (at pair 10, 20)
    4. Generate Vertex AI response
    5. Store message
    """
    
    # Store user message
    ConversationStore.add_message(body.conversation_id, "user", body.message)
    current_pair_count = ConversationStore.get_pair_count(body.conversation_id)
    
    logger.info("chat_request", conversation_id=body.conversation_id, pair_count=current_pair_count)
    
    # ═══════════════════════════════════════════════════════════
    # HITL CHECK 1: Sensitive Data Detection
    # ═══════════════════════════════════════════════════════════
    feature = await review_store.get_feature(db, "sensitive_data_detection")
    if feature and feature.enabled:
        detected = detect_sensitive_data(body.message)
        if detected:
            event = await review_store.create_event(
                db,
                body.conversation_id,
                current_pair_count,
                feature_key="sensitive_data_detection",
                event_metadata={"detected_types": list(detected.keys())},
            )
            logger.info("hitl_sensitive_data_triggered", conversation_id=body.conversation_id)
            return ChatResponse(
                hitl_popup={
                    "event_id": event.id,
                    "feature_key": "sensitive_data_detection",
                    "message": f"⚠️ Detected sensitive data: {', '.join(detected.keys())}. Mask and continue?",
                    "detected_types": list(detected.keys()),
                }
            )
    
    # ═══════════════════════════════════════════════════════════
    # HITL CHECK 2: Model Switch Recommendation
    # ═══════════════════════════════════════════════════════════
    feature = await review_store.get_feature(db, "model_switch_recommendation")
    if feature and feature.enabled:
        analysis = analyze_query_complexity(body.message)
        if analysis["is_complex"]:
            suggested = suggest_model(analysis["complexity_score"], body.current_model)
            if suggested != body.current_model:
                event = await review_store.create_event(
                    db,
                    body.conversation_id,
                    current_pair_count,
                    feature_key="model_switch_recommendation",
                    event_metadata={
                        "complexity_score": analysis["complexity_score"],
                        "current_model": body.current_model,
                        "suggested_model": suggested,
                    },
                )
                logger.info("hitl_model_switch_triggered", conversation_id=body.conversation_id)
                return ChatResponse(
                    hitl_popup={
                        "event_id": event.id,
                        "feature_key": "model_switch_recommendation",
                        "message": f"🚀 Complex query detected. Switch to {suggested} for better results?",
                        "suggested_model": suggested,
                    }
                )
    
    # ═══════════════════════════════════════════════════════════
    # HITL CHECK 3: Chat Compression (at pair 10, 20)
    # ═══════════════════════════════════════════════════════════
    if current_pair_count in [10, 20]:
        feature = await review_store.get_feature(db, "chat_compression")
        if feature and feature.enabled:
            already = await review_store.already_shown(db, body.conversation_id, current_pair_count)
            if not already:
                event = await review_store.create_event(
                    db,
                    body.conversation_id,
                    current_pair_count,
                    feature_key="chat_compression",
                )
                logger.info("hitl_compression_triggered", conversation_id=body.conversation_id, pair_count=current_pair_count)
                return ChatResponse(
                    hitl_popup={
                        "event_id": event.id,
                        "feature_key": "chat_compression",
                        "message": "Your conversation is getting long. Compress old messages to keep responses fast?",
                        "pair_count": current_pair_count,
                    }
                )
    
    # ═══════════════════════════════════════════════════════════
    # NO HITL NEEDED - Generate Vertex AI Response
    # ═══════════════════════════════════════════════════════════
    ai_response = await generate_vertex_ai_response(
        body.conversation_id,
        body.message,
        body.current_model,
    )
    
    # Store assistant message
    ConversationStore.add_message(body.conversation_id, "assistant", ai_response)
    
    logger.info("chat_response_generated", conversation_id=body.conversation_id)
    
    return ChatResponse(message=ai_response)
