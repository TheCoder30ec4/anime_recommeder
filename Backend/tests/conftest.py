import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from langchain_core.messages import HumanMessage

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

for path in (ROOT_DIR, SRC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from config.state import session_state_store
from src import workflow

LOG_FILE = Path("logs/test_failures.log")
DEFAULT_SUGGESTION = (
    "Would you like to share your favorite genres or tell me about a recent anime you enjoyed so I can tailor recommendations for you?"
)


def pytest_configure(config):
    """Clean up log file before test run."""
    if LOG_FILE.exists():
        LOG_FILE.unlink()


def _extract_memory_from_messages(messages) -> Dict[str, Any]:
    """Extract memory dictionary from message history."""
    for message in messages:
        if isinstance(message, HumanMessage) and "Previous memory:" in message.content:
            memory_text = message.content.replace("Previous memory:", "").strip()
            if memory_text:
                try:
                    return ast.literal_eval(memory_text)
                except (ValueError, SyntaxError):
                    return {}
    return {}


def _extract_user_message(content: str) -> str:
    """Extract user message from prompt content."""
    if "User said:" in content:
        return content.split("User said:", 1)[1].strip()
    return content.strip()


def _build_review_response() -> str:
    """Build response for review node."""
    return json.dumps({"decision": "approve"})


def _build_assistant_response(user_message: str, memory: Dict[str, Any]) -> str:
    """Build structured assistant response payload."""
    user_lower = user_message.lower()
    
    if "previous question" in user_lower:
        previous = memory.get("last_interaction", {}).get("user", "unknown")
        conversation = f"Hello! Your previous question was: {previous}"
    else:
        conversation = f"Hello! Assistant reply to: {user_message}"
    
    return json.dumps({
        "conversation": conversation,
        "anime": [],
        "suggestion_for_next_question": DEFAULT_SUGGESTION,
    })


def _stubbed_invoke(messages) -> str:
    """Stub implementation of LLM invocation for testing."""
    if not messages:
        return json.dumps({"conversation": "", "anime": [], "suggestion_for_next_question": DEFAULT_SUGGESTION})
    
    last_message_content = messages[-1].content
    
    # Handle review node requests
    if "Latest user message" in last_message_content:
        return _build_review_response()
    
    # Handle assistant node requests
    memory = _extract_memory_from_messages(messages)
    user_message = _extract_user_message(last_message_content)
    
    return _build_assistant_response(user_message, memory)


@pytest.fixture(autouse=True)
def patch_llm(monkeypatch):
    monkeypatch.setattr(workflow, "_invoke_llm_with_tools", _stubbed_invoke)
    yield


@pytest.fixture(autouse=True)
def reset_session_state():
    session_state_store.reset()
    yield
    session_state_store.reset()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as file:
            file.write(f"{item.nodeid} FAILED\n")
            file.write(f"{rep.longreprtext}\n\n")

