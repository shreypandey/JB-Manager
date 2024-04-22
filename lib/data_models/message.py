from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, model_validator


class MessageType(Enum):
    INTERACTIVE = "interactive"
    TEXT = "text"
    AUDIO = "audio"
    DOCUMENT = "document"
    FORM = "form"
    IMAGE = "image"


class TextMessage(BaseModel):
    header: str
    body: str
    footer: str


class AudioMessage(BaseModel):
    media_url: str


class Option(BaseModel):
    option_id: str
    option_text: str


class InteractiveMessage(BaseModel):
    header: str
    body: str
    footer: str


class ButtonMessage(InteractiveMessage):
    options: List[Option]


class ListMessage(InteractiveMessage):
    button_text: str
    options: List[Option]


class FormMessage(BaseModel):
    header: str
    body: str
    footer: str
    form_id: str


class ImageMessage(BaseModel):
    url: str
    caption: str


class DocumentMessage(BaseModel):
    url: str
    name: str
    caption: str


class Message(BaseModel):
    message_type: MessageType
    text: Optional[TextMessage] = None
    audio: Optional[AudioMessage] = None
    interactive: Optional[InteractiveMessage] = None
    form: Optional[FormMessage] = None
    image: Optional[ImageMessage] = None
    document: Optional[DocumentMessage] = None

    @model_validator(mode="before")
    @classmethod
    def validate_data(cls, values: Dict):
        """Validates data field"""
        message_type = values.get("message_type")
        text = values.get("text")
        audio = values.get("audio")
        interactive = values.get("interactive")
        form = values.get("form")
        image = values.get("image")
        document = values.get("document")

        if message_type == MessageType.TEXT and text is None:
            raise ValueError(f"Text cannot be None for message type: {message_type.name}")
        elif message_type == MessageType.AUDIO and audio is None:
            raise ValueError(f"Audio cannot be None for message type: {message_type.name}")
        elif message_type == MessageType.INTERACTIVE and interactive is None:
            raise ValueError(f"Interactive cannot be None for message type: {message_type.name}")
        elif message_type == MessageType.FORM and form is None:
            raise ValueError(f"Form cannot be None for message type: {message_type.name}")
        elif message_type == MessageType.IMAGE and image is None:
            raise ValueError(f"Image cannot be None for message type: {message_type.name}")
        elif message_type == MessageType.DOCUMENT and document is None:
            raise ValueError(f"Document cannot be None for message type: {message_type.name}")
        
        return values