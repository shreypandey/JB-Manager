import logging
from fastapi import APIRouter
from ..crud import get_chat_history, get_bot_chat_sessions

logger = logging.getLogger('jb-manager-api')

router = APIRouter(
    prefix="/chats",
)

# get all messages related to a session
@router.get("/{bot_id}/sessions/{session_id}")
async def get_session(bot_id: str, session_id: str):
    sessions = await get_bot_chat_sessions(bot_id, session_id)
    return sessions


# get all chats related to a bot
@router.get("/{bot_id}")
async def get_chats_from_bot_id(bot_id: str, skip: int = 0, limit: int = 100):
    chats = await get_chat_history(bot_id, skip, limit)
    return chats


@router.get("/")
async def get_chats(bot_id: str) -> list:
    chats = await get_chat_history(bot_id)
    return chats