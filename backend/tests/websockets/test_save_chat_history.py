from sqlmodel import Session, select
from core.socketio_config import (
    save_chat_history,
    Sender_Role_Enum,
    Platform_Enum,
    Chat_Session,
    Client,
    User,
    Chat,
    Chat_Status_Enum,
)
from models import Chat_Media


def test_save_chat_history_when_send_a_message_into_platform(session: Session):
    conversation = session.exec(select(Chat_Session)).first()
    client = session.exec(
        select(Client).where(Client.id == conversation.client_id)
    ).first()
    user = session.exec(
        select(User).where(User.id == conversation.user_id)
    ).first()

    conversation_envelope = {
        "user_phone_number": f"+{user.phone_number}",
        "client_phone_number": f"+{client.phone_number}",
        "sender_role": Sender_Role_Enum.USER.value,
        "platform": Platform_Enum.WHATSAPP.value,
        "message_id": "123456",
        "timestamp": "2024-11-05T03:03:00.308848+00:00",
    }

    result = save_chat_history(
        session=session,
        conversation_envelope=conversation_envelope,
        message_body="Saved message",
    )

    assert result is not None
    chat = session.exec(select(Chat).where(Chat.id == result)).first()
    assert chat.message == "Saved message"
    assert chat.sender_role == Sender_Role_Enum.USER
    assert chat.status == Chat_Status_Enum.READ


def test_save_chat_history_with_image(session: Session):
    conversation = session.exec(select(Chat_Session)).first()
    client = session.exec(
        select(Client).where(Client.id == conversation.client_id)
    ).first()
    user = session.exec(
        select(User).where(User.id == conversation.user_id)
    ).first()

    image_url = "https://akvo.org/wp-content/themes/Akvo-Theme"
    image_url += "/images/logos/akvologoblack.png"

    conversation_envelope = {
        "user_phone_number": f"+{user.phone_number}",
        "client_phone_number": f"+{client.phone_number}",
        "sender_role": Sender_Role_Enum.USER.value,
        "platform": Platform_Enum.WHATSAPP.value,
        "message_id": "123457",
        "timestamp": "2024-11-05T03:03:00.308848+00:00",
    }

    media = [
        {"url": image_url, "type": "image/png"},
        {"url": image_url, "type": "image/png"},
    ]

    result = save_chat_history(
        session=session,
        conversation_envelope=conversation_envelope,
        message_body="Saved message with image",
        media=media,
    )

    assert result is not None
    chat = session.exec(select(Chat).where(Chat.id == result)).first()
    assert chat.message == "Saved message with image"
    assert chat.sender_role == Sender_Role_Enum.USER
    assert chat.status == Chat_Status_Enum.READ

    chat_media = session.exec(
        select(Chat_Media).where(Chat_Media.chat_id == chat.id)
    ).all()
    assert len(chat_media) == 2
