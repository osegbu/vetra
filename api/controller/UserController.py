from fastapi import HTTPException, Depends
from sqlmodel import select, and_, or_
from sqlalchemy.exc import SQLAlchemyError
from db.db import SessionDep
from models.User import CreateUser, Auth, UserResponse, Model as User
from models.Chat import Model as Chat, ChatResponse
from utils.password_utils import hash_password, verify_password
from utils.jwt_utils import create_access_token
from utils.avatar import avatar
from datetime import datetime
import os

def create_user(user_data: CreateUser, session: SessionDep):
    try:
        user_data.user_name = user_data.user_name.lower()
        hashed_password = hash_password(user_data.hashed_password)
        user_data.hashed_password = hashed_password
        user = User.model_validate(user_data)
        
        existing_user = session.exec(select(User).where(User.user_name == user_data.user_name)).first()

        if existing_user:
            raise HTTPException(status_code=400, detail="Username is already taken")
        
        image_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        avatar_path = os.path.join("static/profile", image_name)
        avatar(user_data.user_name[0].upper(), output_path=avatar_path)

        user.profile_image = image_name

        session.add(user)
        session.commit()
        session.refresh(user)

        user_dict = {"id": user.id, "user_name": user.user_name}
        token = create_access_token(user_dict)

        return {"access_token": token}
    
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Error while creating user") from e
    
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


def login_user(user_data: CreateUser, session: SessionDep):
    try:
        user_data.user_name = user_data.user_name.lower()
        user = session.exec(select(User).where(User.user_name == user_data.user_name)).first()

        if not user:
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        
        if not verify_password(user_data.hashed_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        
        user_dict = {"id": user.id, "user_name": user.user_name}
        token = create_access_token(user_dict)
        return {"access_token": token}
    
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Database error during login") from e
    except Exception as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail)) from e

def fetch_users(current_user: int, session: SessionDep):
    try:
        auth = session.get(User, current_user)

        if not auth:
            raise HTTPException(status_code=400, detail="User not found")

        fetched_users = session.exec(select(User).where(User.id != current_user)).all()

        def build_response(user):
            chats = session.exec(
                select(Chat).where(
                    or_(
                        and_(Chat.sender_id == user.id, Chat.receiver_id == current_user),
                        and_(Chat.receiver_id == user.id, Chat.sender_id == current_user)
                    )
                )
            ).all()

            chat_responses = [
                ChatResponse(
                    id=chat.id,
                    sender_id=chat.sender_id,
                    receiver_id=chat.receiver_id,
                    message=chat.message,
                    image=chat.image,
                    uuid=chat.uuid,
                    created_at=chat.created_at
                ) for chat in chats
            ] if chats else []

            return UserResponse(
                id=user.id,
                user_name=user.user_name,
                profile_image=user.profile_image,
                status=user.status,
                created_at=user.created_at.isoformat(),
                chats=chat_responses
            )

        return [build_response(user) for user in fetched_users] if fetched_users else []

    except SQLAlchemyError as e:
        print(str(e))
        raise HTTPException(status_code=500, detail="Database error while fetching users") from e
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail="An error occurred while fetching users") from e
    
def auth(current_user:int, session: SessionDep):
    try:
        user = session.get(User, current_user)

        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        return Auth(
            id=user.id,
            user_name=user.user_name,
            profile_image=user.profile_image,
        )
    
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Database error while fetching user") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

def update_status(current_user: int, status: str, session: SessionDep):
    try:
        user = session.get(User, current_user)

        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        user.status = status
        user_data = user

        user_data = user_data.model_dump(exclude_unset=True)
        user.sqlmodel_update(user_data)
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return {'Response': 'Success'}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Database error while updating user status") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e