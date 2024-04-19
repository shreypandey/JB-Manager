from enum import Enum
from pydantic import BaseModel
from lib.data_models.message import Message


class LanguageIntent(Enum):
    LANGUAGE_IN = "language_in"
    LANGUAGE_OUT = "language_out"


class LanguageInput(BaseModel):
    turn_id: str
    intent: LanguageIntent
    message: Message
