import json

import pytest

from src import workflow


def build_state(session_id: str, user_message: str):
    return {
        "session_id": session_id,
        "user_messages": [{"role": "user", "content": user_message}],
        "assistant_message": [],
        "human_review_feedback": [],
        "memory": {},
    }


def test_workflow_updates_memory_and_feedback():
    session_id = "session-1"
    state = build_state(session_id, "Hello there")
    config = {"configurable": {"thread_id": session_id}}

    updated_state = workflow.graph.invoke(state, config=config)

    assert updated_state["assistant_message"], "Assistant response should be recorded"
    assert (
        updated_state["memory"]["last_interaction"]["user"] == "Hello there"
    ), "Memory should capture the most recent user message"

    assert updated_state["human_review_feedback"], "Review feedback should be logged"
    first_feedback = json.loads(updated_state["human_review_feedback"][0])
    assert first_feedback["decision"] == "approve"

