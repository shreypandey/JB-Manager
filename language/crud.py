from sqlalchemy import select

from lib.db_connection import async_session
from lib.models import JBMessage, JBTurn, JBUser, JBSession

async def get_user_preferred_language(turn_id: str):
    query = select(JBUser.language_preference).join(JBTurn, JBTurn.user_id==JBUser.id).where(JBTurn.id == turn_id)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            preferred_language = result.scalars().first()
            return preferred_language


async def get_user_preferred_language_by_pid(pid: str):        
    query = select(JBUser.language_preference).where(JBUser.id == pid)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            preferred_language = result.scalars().first()
            return preferred_language


async def get_message_media_information(msg_id: str):
    query = select(JBMessage).where(JBMessage.id == msg_id)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            message = result.scalars().first()
            return message

async def get_turn_information(turn_id: str):
    query = select(JBTurn).where(JBTurn.id == turn_id)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            turn = result.scalars().first()
            return turn
