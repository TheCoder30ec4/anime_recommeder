from fastapi import APIRouter, HTTPException, status

from app.model.ChatModel import Chat
from app.service.chat_service import ChatService


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.post("/recommender", status_code=status.HTTP_200_OK)
async def chat(chat: Chat):
    try:
        payload = await ChatService(chat.session_id, chat.query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return payload
