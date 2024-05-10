from typing import Dict
import uuid

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from lib.db_connection import async_session
from lib.models import JBChannel, JBMessage, JBUser, JBTurn


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
