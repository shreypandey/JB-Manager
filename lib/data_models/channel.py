from abc import ABC
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, model_validator
from lib.data_models.message import Message


class BotInflow(BaseModel, ABC):
    channel_name: str


class RestBotInflow(BotInflow):
    headers: Dict[str, str]
    data: Dict[str, Any]
    query_params: Dict[str, str]


class ChannelIntent(Enum):
    BOT_IN = "bot_inflow"
    BOT_OUT = "bot_outflow"


class ChannelInput(BaseModel):
    turn_id: str
    intent: ChannelIntent
    bot_inflow: Optional[BotInflow] = None
    bot_outflow: Optional[Message] = None

    @model_validator(mode="before")
    @classmethod
    def validate_data(cls, values: Dict):
        """Validates data field"""
        intent = values.get("intent")
        bot_inflow = values.get("bot_inflow")
        bot_outflow = values.get("bot_outflow")
        if isinstance(intent, str):
            intent = ChannelIntent(intent)
        if intent == ChannelIntent.BOT_IN and bot_inflow and bot_outflow is None:
            return values
        elif intent == ChannelIntent.BOT_OUT and bot_inflow is None and bot_outflow:
            return values
        else:
            raise ValueError("Intent mismatch with provided data")
