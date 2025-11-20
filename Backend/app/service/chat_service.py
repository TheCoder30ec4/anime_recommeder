import asyncio
from copy import deepcopy
from typing import Any, Dict

from pydantic import ValidationError

from app.model.ChatModel import Chat  # noqa: F401  (kept for typing/reference)
from config.state import session_state_store
from src.workflow import ChatState, StructuredAssistantResponse, graph
DEFAULT_SUGGESTION = (
    "User, would you like to share your favorite genres or tell me about a recent anime you enjoyed so I can tailor recommendations for you?"
)



async def ChatService(session_id: str, query: str) -> Dict[str, Any]:
    """
    Execute the chat workflow and return a structured response payload.
    """
    if not query or len(query.strip()) < 3:
        raise ValueError("Query must contain at least 3 characters.")

    def _run_graph() -> ChatState:
        stored_state = session_state_store.get_state(session_id)
        if stored_state:
            state: ChatState = deepcopy(stored_state)  # type: ignore[assignment]
        else:
            state = {
                "session_id": session_id,
                "user_messages": [],
                "assistant_message": [],
                "human_review_feedback": [],
                "memory": {},
            }

        state.setdefault("user_messages", [])
        state.setdefault("assistant_message", [])
        state.setdefault("human_review_feedback", [])
        state.setdefault("memory", {})

        config = {"configurable": {"thread_id": session_id}}
        state["user_messages"].append({"role": "user", "content": query})
        updated_state = graph.invoke(state, config=config)
        session_state_store.set_state(session_id, updated_state)
        return updated_state

    loop = asyncio.get_running_loop()
    updated_state = await loop.run_in_executor(None, _run_graph)

    assistant_entry = updated_state["assistant_message"][-1]
    structured_message = assistant_entry.get("structured")
    conversation_text = assistant_entry.get("content") or ""

    if structured_message is None:
        structured_obj = StructuredAssistantResponse(
            conversation=conversation_text,
            suggestion_for_next_question=DEFAULT_SUGGESTION,
        )
    else:
        try:
            structured_obj = StructuredAssistantResponse.model_validate(structured_message)
        except ValidationError:
            fallback_suggestion = structured_message.get(
                "suggestion_for_next_question", DEFAULT_SUGGESTION
            )
            structured_obj = StructuredAssistantResponse(
                conversation=conversation_text,
                suggestion_for_next_question=fallback_suggestion,
            )

    structured_payload = structured_obj.model_dump()

    return {
        "session_id": session_id,
        "query": query,
        "assistant_message": structured_payload
    }
