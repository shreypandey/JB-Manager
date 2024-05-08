import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import (
    bots_router,
    chats_router,
    channels_router,
    callback_router,
    webhook_router,
)

logging.basicConfig(level=logging.ERROR, format="%(asctime)s %(levelname)s [%(name)s] - %(message)s")


app = FastAPI()
app.include_router(bots_router)
app.include_router(chats_router)
app.include_router(channels_router)
app.include_router(callback_router)
app.include_router(webhook_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.get("/")


def hello_world():
    return {"message": "This is JB Manager"}
