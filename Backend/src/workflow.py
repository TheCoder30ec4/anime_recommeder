import json
import os
import re
import sys
import uuid
from typing import Any, Dict, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph

from pydantic import BaseModel, Field, ValidationError

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv()

from config.llm import Llm  # noqa: E402  pylint: disable=wrong-import-position
from config.prompts import PromptLibrary  # noqa: E402  pylint: disable=wrong-import-position
from utils.logger import get_logger  # noqa: E402  pylint: disable=wrong-import-position
from pipeline import run_anime_recommendations_tool  # noqa: E402  pylint: disable=wrong-import-position

logger = get_logger(__name__)

llm = Llm(model_name="openai/gpt-oss-120b", api_key=os.getenv("GROQ_API_KEY", ""))
prompt_library = PromptLibrary()

DEFAULT_SUGGESTION = (
    "Would you like to share your favorite genres or tell me about a recent anime you enjoyed so I can tailor recommendations for you?"
)


class ChatState(TypedDict):
    session_id: str
    user_messages: list[Dict[str, Any]]
    assistant_message: list[Dict[str, Any]]
    human_review_feedback: list[str]
    memory: dict[str, Any]


class AnimeRecommendation(BaseModel):
    anime_name: str = Field(
        ...,
        description="Title of the recommended anime.",
    )
    about_anime: str = Field(
        ...,
        description="Short synopsis or description for the anime.",
    )


class StructuredAssistantResponse(BaseModel):
    conversation: str = Field(
        ...,
        description="Natural-language reply to the user capturing the tool output.",
    )
    anime: list[AnimeRecommendation] = Field(
        default_factory=list,
        description="Ordered list of anime recommendations with descriptions.",
    )
    suggestion_for_next_question: str = Field(
        ...,
        description="Follow-up prompt that nudges the user to continue the chat.",
    )

def _parse_review_decision(content: str) -> Dict[str, Any]:
    text = content.strip()

    if text.startswith("```"):
        text = text.strip("`")
        lines = text.splitlines()
        if lines and lines[0].strip().lower() in {"json", "javascript"}:
            lines = lines[1:]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {}

def assist_node(state: ChatState) -> ChatState:

    user_latest = state["user_messages"][-1]["content"]
    try:
        memory_snapshot = json.dumps(state["memory"])
    except TypeError:
        memory_snapshot = str(state["memory"])

    structured_prompt = prompt_library.get_structured_response_prompt()
    history = [
        SystemMessage(content=structured_prompt),
        HumanMessage(content=f"Previous memory: {memory_snapshot}"),
        HumanMessage(content=f"User said: {user_latest}")
    ]
    response_text = _invoke_llm_with_tools(history)
    structured = _build_structured_response(response_text, user_latest)
    state["assistant_message"].append(
        {
            "role": "assistant",
            "content": structured.conversation,
            "structured": structured.model_dump(),
        }
    )
    
    return state

def review_node(state: ChatState) -> ChatState:

    assistant_message = state["assistant_message"][-1]["content"]
    user_message = state["user_messages"][-1]["content"]
    context_memory = state["memory"]

    review_instructions = prompt_library.get_review_instructions()

    review_prompt = [
        HumanMessage(
            content=(
                f"{review_instructions}\n\n"
                f"Latest user message:\n{user_message}\n\n"
                f"Assistant response:\n{assistant_message}\n\n"
                f"Context memory:\n{context_memory}"
            )
        )
    ]

    review_content = _invoke_llm_with_tools(review_prompt)
    review_data = _parse_review_decision(review_content)

    decision = review_data.get("decision", "approve").lower()
    if decision not in {"approve", "edit", "reject"}:
        decision = "approve"
    if decision == "edit":
        edited = review_data.get("edited")
        if edited:
            state["assistant_message"][-1]["content"] = edited
            _update_structured_conversation(state, edited)
    elif decision == "reject":
        rejection_message = review_data.get(
            "edited",
            "I'm sorry, but I can't help with that request."
        )
        state["assistant_message"][-1]["content"] = rejection_message
        _update_structured_conversation(state, rejection_message)

    state["human_review_feedback"].append(json.dumps(review_data))

    return state

def memory_update_node(state: ChatState) -> ChatState:

    last_user = state["user_messages"][-1]["content"]
    last_bot = state["assistant_message"][-1]["content"]
    state["memory"]["last_interaction"] = {"user": last_user, "assistant": last_bot}

    return state

def end_node(state: ChatState) -> ChatState:
    return state    

graph_builder = StateGraph(ChatState)
graph_builder.add_node("assistant_node", assist_node)
graph_builder.add_node("review_node", review_node)
graph_builder.add_node("memory_update_node", memory_update_node)
graph_builder.add_node("end_node", end_node)
graph_builder.set_entry_point("assistant_node")

graph_builder.add_edge("assistant_node", "review_node")
graph_builder.add_edge("review_node", "memory_update_node")
graph_builder.add_edge("memory_update_node", "end_node")
graph_builder.add_edge("end_node", END)

graph = graph_builder.compile(checkpointer=InMemorySaver())


def _invoke_llm_with_tools(messages: list[HumanMessage]) -> str:
    model = llm.tool_instance()
    response = model.invoke(messages)

    if isinstance(response, AIMessage) and response.tool_calls:
        outputs = []
        for call in response.tool_calls:
            name = call.get("name")
            args = call.get("args") or {}
            if name == run_anime_recommendations_tool.name:
                outputs.append(run_anime_recommendations_tool.invoke(args))
            elif name.lower() in {"json", "commentary"}:
                # Handle case-insensitive tool names (Groq sometimes uses lowercase)
                outputs.append(json.dumps(args))
        if outputs:
            return "\n".join(str(o) for o in outputs if o).strip()
    if hasattr(response, "content"):
        return response.content
    
    return str(response)


def _update_structured_conversation(state: ChatState, new_conversation: str) -> None:
    if not state.get("assistant_message"):
        return
    entry = state["assistant_message"][-1]
    structured = entry.get("structured")
    if not structured:
        entry["structured"] = StructuredAssistantResponse(
            conversation=new_conversation,
            anime=[],
            suggestion_for_next_question=DEFAULT_SUGGESTION,
        ).model_dump()
        return

    try:
        structured_obj = StructuredAssistantResponse.model_validate(structured)
    except ValidationError:
        structured_obj = StructuredAssistantResponse(
            conversation=new_conversation,
            anime=[],
            suggestion_for_next_question=structured.get(
                "suggestion_for_next_question", DEFAULT_SUGGESTION
            ),
        )
    else:
        structured_obj = structured_obj.model_copy(update={"conversation": new_conversation})

    entry["structured"] = structured_obj.model_dump()


def _build_structured_response(
    content: str, user_message: str | None = None
) -> StructuredAssistantResponse:
    raw_text = content.strip() if content else ""

    if raw_text:
        try:
            parsed_json = json.loads(raw_text)
        except json.JSONDecodeError:
            parsed_json = None
        if isinstance(parsed_json, dict):
            try:
                return StructuredAssistantResponse.model_validate(parsed_json)
            except ValidationError:
                logger.debug("LLM JSON output failed validation; falling back to parsing heuristics.")

    conversation = raw_text

    anime_items: list[AnimeRecommendation] = []

    if conversation:
        blocks = re.split(r"\n\s*\n", conversation)
        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue

            title_line = lines[0]
            title_match = re.match(r"^\d+\.\s*(.+)", title_line)
            title = title_match.group(1).strip() if title_match else title_line

            synopsis = ""
            for line in lines[1:]:
                if line.lower().startswith("synopsis:"):
                    synopsis = line.split(":", 1)[1].strip()
                    break

            if title_match or synopsis:
                anime_items.append(
                    AnimeRecommendation(
                        anime_name=title,
                        about_anime=synopsis or "",
                    )
                )

    if not conversation:
        conversation = "I'm sorry, I don't have a response for that."

    if not conversation.lower().startswith(("hi", "hello")):
        conversation = f"Hello! {conversation}"

    suggestion = DEFAULT_SUGGESTION

    data = {
        "conversation": conversation,
        "anime": [item.model_dump() for item in anime_items],
        "suggestion_for_next_question": suggestion,
    }

    try:
        return StructuredAssistantResponse.model_validate(data)
    except ValidationError as exc:
        logger.warning(
            "Structured response validation failed; returning fallback. Error: %s",
            exc,
        )
    fallback = StructuredAssistantResponse(
        conversation=conversation or "I'm sorry, I don't have a response for that.",
        anime=[],
        suggestion_for_next_question=suggestion or DEFAULT_SUGGESTION,
    )
    return fallback


def start_session() -> str:
    return str(uuid.uuid4())


# def main() -> None:
#     logger.info("Starting workflow CLI.")
#     session_id = start_session()
#     state: ChatState = {
#         "session_id": session_id,
#         "user_messages": [],
#         "assistant_message": [],
#         "human_review_feedback": [],
#         "memory": {}
#     }
#     config = {"configurable": {"thread_id": session_id}}

#     print("Interactive chat started. Type 'exit' or 'quit' to stop.\n")

#     while True:
#         user_input = input("You: ").strip()
#         if not user_input:
#             continue
#         if user_input.lower() in {"exit", "quit"}:
#             print("Ending chat session.")
#             break

#         state["user_messages"].append({"role": "user", "content": user_input})
#         state = graph.invoke(state, config=config)

#         assistant_message = state["assistant_message"][-1]["content"]
#         print(f"Assistant: {assistant_message}\n")

#     logger.info("Workflow CLI session ended.")

# if __name__ == "__main__":
#     main()