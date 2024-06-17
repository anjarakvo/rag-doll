import json
from os import environ
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from uuid import uuid4
from datetime import timedelta

from models import User
from core.database import get_session
from utils.jwt_handler import create_jwt_token
from utils.rabbitmq_client import (
    rabbitmq_client,
    RABBITMQ_QUEUE_USER_CHATS,
    RABBITMQ_QUEUE_TWILIOBOT_REPLIES
)

router = APIRouter()
webdomain = environ.get("WEBDOMAIN")
MAGIC_LINK_CHAT_TEMPLATE = environ.get("MAGIC_LINK_CHAT_TEMPLATE")


@router.post("/login")
async def send_login_link(
    phone_number: str, session: Session = Depends(get_session)
):
    if phone_number[0] != "+":
        raise HTTPException(
            status_code=400, detail="Phone number must start with +"
        )
    user = session.exec(
        select(User).where(User.phone_number == phone_number)
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    login_code_uuid = uuid4()
    user.login_code = str(login_code_uuid)
    session.commit()
    # TODO: Implement this function to send WhatsApp messages
    send_whatsapp_message(phone_number, user.login_code)
    # return {"message": "Login link sent via WhatsApp"}
    return f"{webdomain}/verify/{user.login_code}"


@router.get("/verify/{login_code:path}")
async def verify_login_code(
    login_code: str, session: Session = Depends(get_session)
):
    user = session.exec(
        select(User).where(User.login_code == login_code)
    ).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification UUID")
    login_token = create_jwt_token(
        {"sub": str(user.login_code), "uid": user.id},
        expires_delta=timedelta(hours=2),
    )
    user.login_code = None
    session.commit()
    return {"token": login_token}


async def send_whatsapp_message(phone_number: int, login_token: str):
    # Implement your WhatsApp API integration here
    link = f"{webdomain}/verify/{login_token}"
    message_body = {
        "to": {
            # need phone number with country code
            "phone": f"+{phone_number}",
        },
        "text": str(MAGIC_LINK_CHAT_TEMPLATE).format(magic_link=link),
    }
    await rabbitmq_client.producer(
            body=json.dumps(message_body),
            routing_key=RABBITMQ_QUEUE_USER_CHATS,
            reply_to=RABBITMQ_QUEUE_TWILIOBOT_REPLIES
        )