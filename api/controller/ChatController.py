from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from db.db import SessionDep
from models.Chat import Model as Chat, ChatResponse, InsertChat
import json

def insert_chat(chat_data: InsertChat, session: SessionDep):
    try:
        chat = Chat.model_validate(chat_data)
    
        session.add(chat)
        session.commit()
        session.refresh(chat)

        chat_response = ChatResponse(
            id=chat.id,
            sender_id=chat.sender_id,
            receiver_id=chat.receiver_id,
            message=chat.message,
            image=chat.image,
            uuid=chat.uuid,
            created_at=chat.created_at
        )

        return chat_response.model_dump_json()
    
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Error Inserting chat") from e
    
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e