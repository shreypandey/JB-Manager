import uuid
from typing import Dict
from sqlalchemy import desc, func, join, select, update, Integer
from sqlalchemy.orm import joinedload
from lib.db_connection import async_session, sync_session
from lib.models import JBSession, JBPluginUUID, JBBot, JBChannel, JBTurn, JBMessage, JBUser


async def update_user_language(turn_id: str, selected_language: str):
    async with async_session() as session:
        async with session.begin():
            stmt = (
                update(JBUser)
                .values(language_preference=selected_language)
                .filter(JBTurn.user_id == JBUser.id)
                .where(JBTurn.id == turn_id)
            )
            await session.execute(stmt)
            await session.commit()
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


async def get_session_with_bot(session_id: str):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(JBSession)
                .options(joinedload(JBSession.bot))
                .join(JBBot, JBSession.bot_id == JBBot.id)
                .where(JBSession.id == session_id)
            )
            s = result.scalars().first()
            return s


async def get_bot_by_id(bot_id: str) -> JBBot:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(JBBot).where(JBBot.id == bot_id))
            s = result.scalars().first()
            return s


async def get_all_bots():
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(JBBot).where(JBBot.status != "deleted")
            )
            s = result.scalars().all()
            return s


async def get_pid_by_session_id(session_id: str):
    # Create a query to select JBSession based on the provided session_id
    query = select(JBSession.pid).where(JBSession.id == session_id)

    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            s = result.scalars().first()
            return s


def insert_jb_plugin_uuid(session_id: str, turn_id: str):
    # Create a query to insert a new row into JBPluginMapping
    JB_IDENTIFIER = "jbkey"
    reference_id = f"{JB_IDENTIFIER}{str(uuid.uuid4())[:25]}{JB_IDENTIFIER}"
    plugin_uid = JBPluginUUID(id=reference_id, session_id=session_id, turn_id=turn_id)

    with sync_session() as session:
        with session.begin():
            session.add(plugin_uid)
            session.commit()
            return reference_id
    return False


async def insert_session(bot_id: str, channel_id: str) -> JBSession:
    """Function to insert a new session into the database"""
    session_id = str(uuid.uuid4())
    jb_session = JBSession(
        id=session_id, bot_id=bot_id, channel_id=channel_id, variables={}
    )
    async with async_session() as session:
        async with session.begin():
            session.add(jb_session)
            await session.commit()
            return jb_session


async def create_session(turn_id: str):
    """Function to create a new session using turn_id"""
    query = select(JBTurn.bot_id, JBTurn.channel_id).where(JBTurn.id == turn_id)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            result = result.first()
            bot_id, channel_id = result
            return await insert_session(bot_id, channel_id)


async def get_session(turn_id: str):
    """Function to get a session using turn_id if the session is not expired from timeout, else it will create a new session and return"""
    async with async_session() as session:
        async with session.begin():
            query = (
                select(JBSession)
                .join(JBSession.channel)
                .join(JBChannel.turns)
                .filter(JBTurn.id == turn_id)
                .options(joinedload(JBSession.bot))
                .options(joinedload(JBSession.channel))
                .where(
                    JBSession.updated_at
                    > (
                        func.now()
                        - func.make_interval(0, 0, 0, 0, 0, 0, JBBot.timeout * 1000)
                    )
                )
            )
            result = await session.execute(query)
            jb_session = result.scalars().first()
            if jb_session is not None:
                return jb_session
            else:
                return await create_session(turn_id)


async def update_session(session_id: str, variables: dict):
    async with async_session() as session:
        async with session.begin():
            stmt = (
                update(JBSession)
                .where(JBSession.id == session_id)
                .values(variables=variables)
            )
            await session.execute(stmt)
            await session.commit()
    return None
