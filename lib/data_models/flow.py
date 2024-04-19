from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, model_validator
from lib.data_models.message import Message


class FlowIntent(Enum):
    BOT = "bot"
    CALLBACK = "callback"
    USER_INPUT = "user_input"
    DIALOG = "dialog"


class BotIntent(Enum):
    INSTALL = "install"
    DELETE = "delete"


class Bot(BaseModel):
    name: str
    fsm_code: str
    requirements_txt: str
    index_urls: Optional[List[str]] = None


class BotConfig(BaseModel):
    bot_id: str
    intent: BotIntent
    bot: Optional[Bot] = None

    @model_validator(mode="before")
    @classmethod
    def validate_data(cls, values: Dict):
        """Validates data field"""
        intent = values.get("intent")
        bot = values.get("bot")
        if isinstance(intent, str):
            intent = BotIntent(intent)
        if intent == BotIntent.INSTALL and bot is None:
            raise ValueError("Intent mismatch with provided data")
        else:
            return values


class UserInput(BaseModel):
    turn_id: str
    message: Message


class Callback(BaseModel):
    turn_id: str
    callback_input: str


class Dialog(BaseModel):
    turn_id: str
    dialog_input: str


class FlowInput(BaseModel):
    intent: FlowIntent
    bot: Optional[BotConfig] = None
    dialog: Optional[Dialog] = None
    callback: Optional[Callback] = None
    user_input: Optional[Message] = None

    @model_validator(mode="before")
    @classmethod
    def validate_data(cls, values: Dict):
        """Validates data field"""
        intent = values.get("intent")
        bot = values.get("bot")
        dialog = values.get("dialog")
        callback = values.get("callback")
        user_input = values.get("user_input")
        if isinstance(intent, str):
            intent = FlowIntent(intent)
        if (
            (intent == FlowIntent.BOT and bot is None)
            or (intent == FlowIntent.DIALOG and dialog is None)
            or (intent == FlowIntent.CALLBACK and callback is None)
            or (intent == FlowIntent.USER_INPUT and user_input is None)
        ):
            raise ValueError("Intent mismatch with provided data")
        else:
            return values
