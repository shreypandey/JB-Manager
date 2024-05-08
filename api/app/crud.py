import uuid
from typing import Tuple
from sqlalchemy import desc, select, update, and_, join
from sqlalchemy.orm import joinedload
from lib.models import (
    JBBot,
    JBChannel,
    JBPluginUUID,
    JBTurn,
    JBUser,
    JBSession
)
from lib.db_connection import async_session
from .schema import JBChannelContent

async def get_bot_and_channel_by_bot_identifier(
    bot_identifier: str, channel: str
) -> Tuple[JBBot, JBChannel]:
    query = (
        select(JBBot, JBChannel)
        .select_from(join(JBBot, JBChannel, JBBot.id == JBChannel.bot_id))
        .where(
            JBChannel.name == channel,
            JBChannel.app_id == bot_identifier,
            JBChannel.status == "active",
        )
    )
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            result = result.first()
            if result:
                bot, channel = result
                return bot, channel
            else:
                return None, None


async def update_channel_by_bot_id(bot_id: str, data):
    stmt = update(JBChannel).where(JBChannel.bot_id == bot_id).values(**data)
    async with async_session() as session:
        async with session.begin():
            await session.execute(stmt)
            await session.commit()
            return bot_id


async def create_channel(bot_id: str, data: JBChannelContent):
    channel_id = str(uuid.uuid4())
    channel = JBChannel(
        id=channel_id,
        bot_id=bot_id,
        status=data.status,
        name=data.name,
        type=data.name,
        key=data.key,
        app_id=data.app_id,
        url=data.url,
    )
    async with async_session() as session:
        async with session.begin():
            session.add(channel)
            await session.commit()
            return channel


async def update_bot(bot_id: str, data):
    async with async_session() as session:
        async with session.begin():
            stmt = update(JBBot).where(JBBot.id == bot_id).values(**data)
            await session.execute(stmt)
            await session.commit()
            return bot_id


async def get_bot_by_id(bot_id: str):
    query = select(JBBot).where(JBBot.id == bot_id)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            bot = result.scalars().first()
            return bot


async def create_bot(data):
    bot_id = str(uuid.uuid4())
    bot = JBBot(id=bot_id, **data)
    async with async_session() as session:
        async with session.begin():
            session.add(bot)
            await session.commit()
            return bot


async def get_bot_list():
    async with async_session() as session:
        async with session.begin():
            query = select(JBBot).where(JBBot.status != "deleted")
            result = await session.execute(query)
            bot_list = result.scalars().all()
            return bot_list


async def get_plugin_reference(plugin_uuid: str) -> JBPluginUUID:
    # Create a query to select JBPluginMapping based on the provided plugin_uuid
    query = select(JBPluginUUID).where(JBPluginUUID.id == plugin_uuid)

    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            s = result.scalars().first()
            return s


async def create_user(
    bot_id: str, identifier: str, first_name: str, last_name: str
) -> JBUser:
    user_id = str(uuid.uuid4())
    user = JBUser(
        id=user_id,
        bot_id=bot_id,
        identifier=identifier,
        first_name=first_name,
        last_name=last_name,
    )
    async with async_session() as session:
        async with session.begin():
            session.add(user)
            await session.commit()
            return user


async def get_user_by_identifier(identifier: str, bot_id: str) -> JBUser:
    query = select(JBUser).where(
        JBUser.identifier == identifier, JBUser.bot_id == bot_id
    )
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            user = result.scalars().first()
            return user


async def create_turn(bot_id: str, channel_id: str, user_id: str):
    turn_id: str = str(uuid.uuid4())
    async with async_session() as session:
        async with session.begin():
            session.add(
                JBTurn(
                    id=turn_id,
                    bot_id=bot_id,
                    channel_id=channel_id,
                    user_id=user_id,
                )
            )
            await session.commit()
            return turn_id

async def get_bot_and_channel_by_channel_id(channel_id: str) -> Tuple[JBBot, JBChannel]:
    query = (
        select(JBBot, JBChannel)
        .select_from(join(JBBot, JBChannel, JBBot.id == JBChannel.bot_id))
        .where(JBChannel.id == channel_id)
    )
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            result = result.first()
            if result:
                bot, channel = result
                return bot, channel
            else:
                return None, None

async def update_channel(channel_id: str, data):
    stmt = update(JBChannel).where(JBChannel.id == channel_id).values(**data)
    async with async_session() as session:
        async with session.begin():
            await session.execute(stmt)
            await session.commit()
            return channel_id

async def get_chat_history(bot_id: str, skip=0, limit=1000):
    # TODO: introduce pagination
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(JBSession)
                .options(joinedload(JBSession.user))
                .join(JBUser, JBSession.pid == JBUser.id)
                .where(JBSession.bot_id == bot_id)
                .offset(skip)
                .limit(limit)
            )
            chat_history = result.scalars().all()
            return chat_history
        
async def get_bot_chat_sessions(bot_id: str, session_id: str):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(JBSession)
                .filter(JBSession.bot_id == bot_id)
                .options(
                    joinedload(JBSession.user),
                    joinedload(JBSession.turns).joinedload(JBTurn.messages),
                )
                .where(JBSession.id == session_id)
            )
            chat_sessions = result.unique().scalars().all()
            return chat_sessions