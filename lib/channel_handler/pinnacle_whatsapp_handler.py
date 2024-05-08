import base64
import json
import os
from typing import Any, Dict, Generator
import requests

from sqlalchemy import select

from lib.db_connection import sync_session
from lib.azure_storage_sync import AzureStorageSync
from lib.channel_handler.channel_handler import ChannelData, RestChannelHandler, User
from lib.data_models import (
    MessageType,
    Message,
    TextMessage,
    AudioMessage,
    InteractiveMessage,
    Option,
    FormMessage,
    ImageMessage,
    DocumentMessage,
    InteractiveReplyMessage,
    RestBotInput,
    ListMessage,
    ButtonMessage,
    DialogMessage,
    DialogOption
)
from lib.models import JBChannel, JBUser, JBForm
from lib.utils import EncryptionHandler

azure_creds = {
    "account_url": os.getenv("STORAGE_ACCOUNT_URL"),
    "account_key": os.getenv("STORAGE_ACCOUNT_KEY"),
    "container_name": os.getenv("STORAGE_AUDIOFILES_CONTAINER"),
    "base_path": "input/",
}
storage = AzureStorageSync(**azure_creds)


class PinnacleWhatsappHandler(RestChannelHandler):

    @classmethod
    def is_valid_data(cls, data: Dict) -> str:
        return "object" in data and data["object"] == "whatsapp_business_account"

    @classmethod
    def process_message(cls, data: Dict) -> Generator[ChannelData, None, None]:
        if cls.is_valid_data(data):
            for entry in data["entry"]:
                for change in entry["changes"]:
                    if "value" in change:
                        if "metadata" in change["value"]:
                            metadata = change["value"]["metadata"]
                            whatsapp_number = metadata.get("display_phone_number")
                        if "messages" in change["value"]:
                            for message in change["value"]["messages"]:
                                user_identifier = message.pop("from")
                                yield ChannelData(
                                    bot_identifier=whatsapp_number,
                                    user=User(
                                        user_identifier=user_identifier,
                                        user_name="Dummy",
                                        user_phone=user_identifier,
                                    ),
                                    message_data=message,
                                )

    @classmethod
    def get_channel_name(cls) -> str:
        return "pinnacle_whatsapp"

    @classmethod
    def to_message(
        cls, turn_id: str, channel: JBChannel, bot_input: RestBotInput
    ) -> Message:
        data = bot_input.data
        message_type = data["type"]
        timestamp = data["timestamp"]
        message_data = data[message_type]
        if message_type == "text":
            text = message_data["body"]
            return Message(
                message_type=MessageType.TEXT,
                text=TextMessage(body=text),
                timestamp=timestamp,
            )
        elif message_type == "audio":
            audio_id = message_data["id"]
            audio_content = cls.wa_download_audio(channel=channel, file_id=audio_id)
            audio_bytes = base64.b64decode(audio_content)
            audio_file_name = f"{turn_id}.ogg"
            storage.write_file(audio_file_name, audio_bytes, "audio/ogg")
            storage_url = storage.make_public(audio_file_name)

            return Message(
                message_type=MessageType.AUDIO,
                audio=AudioMessage(media_url=storage_url),
                timestamp=timestamp,
            )
        elif message_type == "interactive":
            interactive_type = message_data["type"]
            interactive_message_data = message_data[interactive_type]
            if interactive_type == "button_reply ":
                options = [
                    Option(
                        id=interactive_message_data["id"],
                        title=interactive_message_data["title"],
                    )
                ]
                return Message(
                    message_type=MessageType.INTERACTIVE,
                    interactive_reply=InteractiveReplyMessage(options=options),
                    timestamp=timestamp,
                )
            elif interactive_type == "list_reply":
                if (selected_language:=interactive_message_data["id"].startswith("lang_")):
                    return Message(
                        message_type=MessageType.DIALOG,
                        dialog=DialogMessage(
                            dialog_id=DialogOption.LANGUAGE_SELECTED,
                            dialog_input=selected_language
                        ),
                    )
                options = [
                    Option(
                        id=interactive_message_data["id"],
                        title=interactive_message_data["title"],
                    )
                ]
                return Message(
                    message_type=MessageType.INTERACTIVE,
                    interactive_reply=InteractiveReplyMessage(options=options),
                    timestamp=timestamp,
                )
            elif interactive_type == "nfm_reply":
                return Message(
                    message_type=MessageType.FORM,
                    form=FormMessage(body=interactive_message_data["response_json"]),
                    timestamp=timestamp,
                )
        return NotImplemented

    @classmethod
    def parse_bot_output(
        cls, message: Message, user: JBUser, channel: JBChannel
    ) -> Dict:
        message_type = message.message_type
        if message_type == MessageType.TEXT:
            data = cls.parse_text_message(
                channel=channel, user=user, message=message.text
            )
        elif message_type == MessageType.AUDIO:
            data = cls.parse_audio_message(
                channel=channel, user=user, message=message.audio
            )
        elif message_type == MessageType.INTERACTIVE:
            data = cls.parse_interactive_message(
                channel=channel,
                user=user,
                message=message.interactive,
            )
        elif message_type == MessageType.IMAGE:
            data = cls.parse_image_message(
                channel=channel,
                user=user,
                message=message.image,
            )
        elif message_type == MessageType.DOCUMENT:
            data = cls.parse_document_message(
                channel=channel,
                user=user,
                message=message.document,
            )
        elif message_type == MessageType.FORM:
            data = cls.parse_form_message(
                channel=channel,
                user=user,
                message=message.form,
            )
        elif message_type == MessageType.DIALOG:
            data = cls.parse_dialog_message(
                channel=channel,
                user=user,
                message=message.dialog,
            )
        else:
            return NotImplemented
        return data

    @classmethod
    def parse_text_message(
        cls, channel: JBChannel, user: JBUser, message: TextMessage
    ) -> Dict[str, Any]:
        data = {
            "messaging_product": "whatsapp",
            "preview_url": False,
            "recipient_type": "individual",
            "to": str(user.identifier),
            "type": "text",
            "text": {"body": str(message.body)},
        }
        return data

    @classmethod
    def parse_audio_message(
        cls, channel: JBChannel, user: JBUser, message: AudioMessage
    ) -> Dict[str, Any]:
        data = {
            "messaging_product": "whatsapp",
            "preview_url": False,
            "recipient_type": "individual",
            "to": str(user.phone_number),
            "type": "audio",
            "audio": {"link": message.media_url},
        }
        return data

    @classmethod
    def parse_list_message(
        cls,
        channel: JBChannel,
        user: JBUser,
        data: ListMessage,
    ) -> Dict[str, Any]:
        data = {
            "messaging_product": "whatsapp",
            "preview_url": False,
            "recipient_type": "individual",
            "to": str(user.identifier),
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": data.header[:59] if data.header else None,
                },
                "body": {"text": data.body},
                "footer": {"text": data.footer},
                "action": {
                    "button": data.button_text,
                    "sections": [
                        {
                            "title": data.list_title,
                            "rows": [
                                {
                                    "id": option.option_id,
                                    "title": option.option_text[:20],
                                }
                                for option in data.options
                            ],
                        }
                    ],
                },
            },
        }
        return data

    @classmethod
    def parse_button_message(
        cls,
        channel: JBChannel,
        user: JBUser,
        data: ButtonMessage,
    ) -> Dict[str, Any]:
        data = {
            "messaging_product": "whatsapp",
            "preview_url": False,
            "recipient_type": "individual",
            "to": str(user.phone_number),
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "text",
                    "text": data.header[:59] if data.header else None,
                },
                "body": {"text": data.body},
                "footer": {"text": data.footer},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": x["id"], "title": x["title"][:20]},
                        }
                        for x in data.options
                    ],
                },
            },
        }
        return data

    @classmethod
    def parse_interactive_message(
        cls,
        channel: JBChannel,
        user: JBUser,
        message: InteractiveMessage,
    ) -> str:
        if isinstance(message, ListMessage):
            data = cls.parse_list_message(channel, user, message)
        else:
            data = cls.parse_button_message(channel, user, message)
        return data

    @classmethod
    def parse_image_message(
        cls,
        channel: JBChannel,
        user: JBUser,
        message: ImageMessage,
    ) -> str:
        data = {
            "messaging_product": "whatsapp",
            "preview_url": False,
            "recipient_type": "individual",
            "to": str(user.phone_number),
            "type": "image",
            "image": {"link": message.url, "caption": message.caption},
        }
        return data

    @classmethod
    def parse_document_message(
        cls,
        channel: JBChannel,
        user: JBUser,
        message: DocumentMessage,
    ) -> str:
        data = {
            "messaging_product": "whatsapp",
            "preview_url": False,
            "recipient_type": "individual",
            "to": str(user.phone_number),
            "type": "document",
            "document": {
                "link": message.url,
                "filename": message.name,
                "caption": message.caption,
            },
        }
        return data

    @classmethod
    def get_form_parameters(cls, form_id: str):
        # Create a query to insert a new row into JBPluginMapping
        with sync_session() as session:
            with session.begin():
                result = session.execute(select(JBForm).where(JBForm.id == form_id))
                s = result.scalars().first()
                return s

    @classmethod
    def parse_form_message(
        cls,
        channel: JBChannel,
        user: JBUser,
        message: FormMessage,
    ) -> str:
        form_id = message.form_id

        form_parameters = cls.get_form_parameters(form_id)
        data = {
            "messaging_product": "whatsapp",
            "preview_url": False,
            "recipient_type": "individual",
            "to": str(user.phone_number),
            "type": "interactive",
            "interactive": {
                "type": "flow",
                "body": {"text": message.body},
                "footer": {"text": message.footer},
                "action": {
                    "name": "flow",
                    "parameters": form_parameters,
                },
            },
        }
        return data

    @classmethod
    def parse_dialog_message(
        cls,
        channel: JBChannel,
        user: JBUser,
        message: DialogMessage,
    ) -> str:
        if message.dialog_id == DialogOption.LANGUAGE_CHANGE:
            message = ListMessage(
                header="Language",
                body="Please select your preferred language",
                footer="भाषा चुनें",
                options=[
                    Option(option_id="lang_hindi", option_text="हिन्दी"),
                    Option(option_id="lang_english", option_text="English"),
                    Option(option_id="lang_bengali", option_text="বাংলা"),
                    Option(option_id="lang_telugu", option_text="తెలుగు"),
                    Option(option_id="lang_marathi", option_text="मराठी"),
                    Option(option_id="lang_tamil", option_text="தமிழ்"),
                    Option(option_id="lang_gujarati", option_text="ગુજરાતી"),
                    Option(option_id="lang_urdu", option_text="اردو"),
                    Option(option_id="lang_kannada", option_text="ಕನ್ನಡ"),
                    Option(option_id="lang_odia", option_text="ଓଡ଼ିଆ"),
                ],
                button_text="चुनें / Select",
                list_title="भाषाएँ / Languages",
            )
            return cls.parse_list_message(channel, user, message)
        return NotImplemented

    @classmethod
    def generate_header(cls, channel: JBChannel):
        decrypted_key = EncryptionHandler.decrypt_text(channel.key)
        headers = {
            "Content-type": "application/json",
            "wanumber": channel.app_id,
            "apikey": decrypted_key,
        }
        return headers

    @classmethod
    def send_message(cls, channel: JBChannel, user: JBUser, message: Message):
        url = channel.url + "/v1/messages"
        headers = cls.generate_header(channel=channel)
        data = cls.parse_bot_output(message=message, channel=channel, user=user)
        import logging
        r = requests.post(url, data=json.dumps(data), headers=headers)
        json_output = r.json()
        logging.error(json_output)
        if json_output and json_output["messages"]:
            return json_output["messages"][0]["id"]
        return None

    @classmethod
    def wa_download_audio(cls, channel: JBChannel, file_id: str):
        url = f"{channel.url}/v1/downloadmedia/{file_id}"
        headers = cls.generate_header(channel=channel)
        r = requests.get(url, headers=headers)
        file_content = base64.b64encode(r.content)
        return file_content
