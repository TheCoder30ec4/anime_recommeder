from fastapi.testclient import TestClient

from config.state import session_state_store
from main import app


client = TestClient(app)


def test_chat_endpoint_returns_structured_response_and_remembers():
    session_state_store.reset()
    session_id = "test-session"

    response = client.post(
        "/chat/recommender",
        json={"session_id": session_id, "query": "Suggest a horror anime"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["query"] == "Suggest a horror anime"
    assistant_payload = body["assistant_message"]
    assert assistant_payload["conversation"] == "Hello! Assistant reply to: Suggest a horror anime"
    assert assistant_payload["anime"] == []
    assert assistant_payload["suggestion_for_next_question"] == (
        "Would you like to share your favorite genres or tell me about a recent anime you enjoyed so I can tailor recommendations for you?"
    )
    assert isinstance(body["memory"], dict)

    response = client.post(
        "/chat/recommender",
        json={"session_id": session_id, "query": "What is the previous question I asked?"},
    )
    assert response.status_code == 200
    body = response.json()
    assistant_payload = body["assistant_message"]
    assert assistant_payload["conversation"] == "Hello! Your previous question was: Suggest a horror anime"
    assert assistant_payload["anime"] == []
    assert assistant_payload["suggestion_for_next_question"] == (
        "Would you like to share your favorite genres or tell me about a recent anime you enjoyed so I can tailor recommendations for you?"
    )

    stored = session_state_store.get_state(session_id)
    assert stored["memory"]["last_interaction"]["user"] == "What is the previous question I asked?"


def test_chat_endpoint_rejects_short_query():
    response = client.post(
        "/chat/recommender", json={"session_id": "s1", "query": "hi"}
    )

    assert response.status_code == 422
    detail = response.json()["detail"][0]["msg"].lower()
    assert "at least 3 characters" in detail


def test_chat_endpoint_returns_400_when_service_raises(monkeypatch):
    session_state_store.reset()

    async def fake_service(session_id: str, query: str):
        raise ValueError("Something went wrong")

    from app.controller import ChatController

    monkeypatch.setattr(ChatController, "ChatService", fake_service)

    response = client.post(
        "/chat/recommender", json={"session_id": "s1", "query": "valid question"}
    )

    assert response.status_code == 400
    assert "something went wrong" in response.json()["detail"].lower()

