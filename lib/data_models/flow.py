from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, model_validator
from lib.data_models.message import Message, MessageType


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

        if intent == BotIntent.INSTALL and bot is None:
            raise ValueError("Bot cannot be None for intent: INSTALL")
        return values


class UserInput(BaseModel):
    turn_id: str
    message: Message


class Callback(BaseModel):
    turn_id: str
    callback_input: str


class Dialog(BaseModel):
    turn_id: str
    message: Message

    @model_validator(mode="before")
    @classmethod
    def validate_data(cls, values: Dict):
        """Validates data field"""
        message = values.get("message")

        if message.message_type != MessageType.DIALOG:
            raise ValueError("Only dialog message type is allowed for dialog intent")
        return values


class Flow(BaseModel):
    source: str
    intent: FlowIntent
    bot_config: Optional[BotConfig] = None
    dialog: Optional[Dialog] = None
    callback: Optional[Callback] = None
    user_input: Optional[UserInput] = None

    @model_validator(mode="before")
    @classmethod
    def validate_data(cls, values: Dict):
        """Validates data field"""
        intent = values.get("intent")
        bot_config = values.get("bot_config")
        dialog = values.get("dialog")
        callback = values.get("callback")
        user_input = values.get("user_input")

        if intent == FlowIntent.BOT and bot_config is None:
            raise ValueError(f"bot_config cannot be None for intent: {intent.name}")
        elif intent == FlowIntent.DIALOG and dialog is None:
            raise ValueError(f"dialog cannot be None for intent: {intent.name}")
        elif intent == FlowIntent.CALLBACK and callback is None:
            raise ValueError(f"callback cannot be None for intent: {intent.name}")
        elif intent == FlowIntent.USER_INPUT and user_input is None:
            raise ValueError(f"user_input cannot be None for intent: {intent.name}")
        return values


class FSMIntent(Enum):
    CONVERSATION_RESET = "CONVERSATION_RESET"
    LANGUAGE_CHANGE = "LANGUAGE_CHANGE"
    SEND_MESSAGE = "SEND_MESSAGE"
    RAG_CALL = "RAG_CALL"


class FSMOutput(BaseModel):
    intent: FSMIntent
    message: Optional[Message] = None
    rag_query: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_data(cls, values: Dict):
        """Validates data field"""
        intent = values.get("intent")
        message = values.get("message")
        rag_query = values.get("rag_query")

        if intent == FSMIntent.SEND_MESSAGE and message is None:
            raise ValueError(f"message cannot be None for intent: {intent.name}")
        elif intent == FSMIntent.RAG_CALL and rag_query is None:
            raise ValueError(f"rag_query cannot be None for intent: {intent.name}")
        return values


class FSMInput(BaseModel):
    user_input: Optional[str] = None
    callback_input: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_data(cls, values: Dict):
        """Validates data field"""
        if values.get("user_input") is None and values.get("callback_input") is None:
            raise ValueError("user_input or callback_input is required")
        elif (
            values.get("user_input") is not None
            and values.get("callback_input") is not None
        ):
            raise ValueError(
                "user_input and callback_input cannot be provided together"
            )
