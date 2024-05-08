import os
import logging
from lib.azure_storage_sync import AzureStorageSync
from lib.kafka_utils import KafkaConsumer, KafkaProducer

logging.basicConfig()
logger = logging.getLogger("flow")
logger.setLevel(logging.INFO)

consumer = KafkaConsumer.from_env_vars(
    group_id="cooler_group_id", auto_offset_reset="latest"
)
producer = KafkaProducer.from_env_vars()

account_url = os.getenv("STORAGE_ACCOUNT_URL")
account_key = os.getenv("STORAGE_ACCOUNT_KEY")
container_name = os.getenv("STORAGE_AUDIOFILES_CONTAINER")
storage = AzureStorageSync(
    account_url=account_url,
    account_key=account_key,
    container_name=container_name,
    base_path="output_files/",
)
def save_file(filename: str, file_content: bytes, mime_type: str):
    storage.write_file(filename, file_content, mime_type)
    media_output_url = storage.make_public(filename)
    return media_output_url