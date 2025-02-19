import uuid
import time
import json
import asyncio
from fastapi import WebSocket
from dotenv import load_dotenv
from api.controller.UserController import update_status
from db.db import SessionDep

load_dotenv()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
        self.pending_messages: dict = {}

    async def connect(self, websocket: WebSocket, user_id: int, session: SessionDep):
        if user_id in self.active_connections:
            return
        self.active_connections[user_id] = websocket
        try:
            user = update_status(user_id, "Online", session)
            await self.notify_status_change(user_id, "Online")
            return user
        except Exception as e:
            print(f"Failed to connect user {user_id}: {e}")

    async def disconnect(self, user_id: int, session: SessionDep):
        self.active_connections.pop(user_id)
        try:
            update_status(user_id, "Offline", session)
            print(f"User {user_id} disconnected")
            await self.notify_status_change(user_id, "Offline")
        except Exception as e:
            print(f"Failed to disconnect user {user_id}: {e}")

    async def send_chat(self, chat):
        websocket = self.active_connections.get(chat['receiver_id'])
        message_id = self.generate_message_id()
        message = json.dumps({'type': 'chat', 'message_id': message_id, **chat})

        if websocket:
            await self.queue_message(chat['receiver_id'], message, message_id)

    async def update_msg_status(self, user_id: int, receiver_id:int, uuid: str):
        websocket = self.active_connections.get(user_id)
        if websocket:
            message_id = self.generate_message_id()
            message = json.dumps({'type': 'msg_update',  'receiver_id': receiver_id, 'uuid': uuid, 'message_id': message_id})
            await self.queue_message(user_id, message, message_id)

    async def typing_indicator(self, type: str, receiver_id: int, sender_id: int):
        websocket = self.active_connections.get(receiver_id)
        if websocket:
            try:
                message_id = self.generate_message_id()
                message = json.dumps({'type': type, 'sender_id': sender_id, 'message_id': message_id})
                await self.queue_message(receiver_id, message, message_id)
            except Exception as e:
                print(f"Failed to send typing indicator to {receiver_id}: {e}")

    async def acknowledge_message(self, message_id: str):
        if message_id in self.pending_messages:
            del self.pending_messages[message_id]

    async def queue_message(self, receiver_id: int, message: str, message_id: str, retries: int = 5, retry_interval: int = 2):
        self.pending_messages[message_id] = message
        websocket = self.active_connections.get(receiver_id)
        if websocket:
            asyncio.create_task(self._retry_send_message(receiver_id, message, message_id, retries, retry_interval))

    async def _retry_send_message(self, receiver_id: int, message: str, message_id: str, retries: int, retry_interval: int):
        retry_count = 0
        while retry_count < retries:
            try:
                websocket = self.active_connections.get(receiver_id)
                if websocket:
                    await websocket.send_text(message)
                    await asyncio.sleep(retry_interval * (2 ** retry_count))

                    if message_id not in self.pending_messages:
                        return

                    retry_count += 1
            except Exception as e:
                print(f"Failed to send message {message_id} to {receiver_id}: {e}")
                break

    def generate_message_id(self) -> str:
        return f"{uuid.uuid4()}-{int(time.time())}"

    async def notify_status_change(self, user_id: int, status: str):
        message_id = self.generate_message_id()
        message = json.dumps({'type': 'status', 'user_id': user_id, 'status': status, 'message_id': message_id})

        for connection_id in self.active_connections.keys():
            await self.queue_message(connection_id, message, message_id)