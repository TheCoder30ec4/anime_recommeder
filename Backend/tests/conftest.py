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


def pytest_configure(config):
    if LOG_FILE.exists():
        LOG_FILE.unlink()


def _stubbed_invoke(messages) -> str:
    last_prompt = messages[-1].content
    if "Latest user message" in last_prompt:
        return json.dumps({"decision": "approve"})

    memory_text = ""
    for message in messages:
        if isinstance(message, HumanMessage) and "Previous memory:" in message.content:
            memory_text = message.content.replace("Previous memory:", "").strip()
            break
    memory: Dict[str, Any] = {}
    if memory_text:
        try:
            memory = ast.literal_eval(memory_text)
        except (ValueError, SyntaxError):
            memory = {}

    user_line = last_prompt.replace("User said:", "").strip()
    base_payload = {
        "conversation": f"Hello! Assistant reply to: {user_line}",
        "anime": [],
        "suggestion_for_next_question": "Would you like to share your favorite genres or tell me about a recent anime you enjoyed so I can tailor recommendations for you?",
    }

    if "previous question" in user_line.lower():
        previous = memory.get("last_interaction", {}).get("user", "unknown")
        base_payload["conversation"] = f"Hello! Your previous question was: {previous}"

    return json.dumps(base_payload)


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

