from typing import Dict
import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from lib.db_connection import async_session
from lib.models import JBBot, JBChannel, JBMessage, JBSession, JBUser, JBTurn


async def get_user_by_session_id(session_id: str):
    # TODO: have to make it as single query
    query = select(JBSession).where(JBSession.id == session_id)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            s = result.scalars().first()
            if s is not None:
                query = select(JBUser).where(JBUser.id == s.pid)
                result = await session.execute(query)
                user = result.scalars().first()
                return user
    return None


async def get_user_by_turn_id(turn_id: str):
    query = (
        select(JBUser)
        .join(JBTurn, JBTurn.user_id == JBUser.id)
        .options(joinedload(JBUser.turns))
        .where(JBTurn.id == turn_id)
    )
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            s = result.scalars().first()
            return s


async def get_bot_by_session_id(session_id: str):
    # TODO: have to make it as single query
    query = select(JBSession).where(JBSession.id == session_id)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            s = result.scalars().first()
            if s is not None:
                query = select(JBBot).where(JBBot.id == s.bot_id)
                result = await session.execute(query)
                bot = result.scalars().first()
                return bot.phone_number, bot.channels
    return None


async def get_channel_by_session_id(session_id: str):
    # TODO: have to make it as single query
    query = select(JBSession).where(JBSession.id == session_id)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            s = result.scalars().first()
            if s is not None:
                query = select(JBChannel).where(JBChannel.id == s.channel_id)
                result = await session.execute(query)
                channel = result.scalars().first()
                return channel
    return None


async def get_channel_by_turn_id(turn_id: str):
    query = (
        select(JBChannel)
        .join(JBTurn)
        .options(joinedload(JBChannel.turns))
        .where(JBTurn.id == turn_id)
    )
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            s = result.scalars().first()
            return s


async def set_user_language(session_id: str, language: str):
    async with async_session() as session:
        async with session.begin():
            query = select(JBSession).where(JBSession.id == session_id)
            result = await session.execute(query)
            s = result.scalars().first()
            if s is not None:
                query = (
                    update(JBUser)
                    .where(JBUser.id == s.pid)
                    .values(language_preference=language)
                )
                await session.execute(query)
                await session.commit()
                return True
    return None


async def update_message(msg_id: str, **kwargs):
    async with async_session() as session:
        async with session.begin():
            query = update(JBMessage).where(JBMessage.id == msg_id).values(**kwargs)
            await session.execute(query)
            await session.commit()
            return True
    return None


async def create_message(
    turn_id: str,
    message_type: str,
    message: Dict,
    is_user_sent: bool = False,
):
    message_id = str(uuid.uuid4())
    async with async_session() as session:
        async with session.begin():
            session.add(
                JBMessage(
                    id=message_id,
                    turn_id=turn_id,
                    message_type=message_type,
                    is_user_sent=is_user_sent,
                    message=message,
                )
            )
            await session.commit()
            return message_id
