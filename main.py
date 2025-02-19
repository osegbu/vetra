from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from db.db import create_db_and_tables
from db.db import SessionDep
from api.route import User
import os
import json
from datetime import datetime
import base64
from websocket.ConnectionManager import ConnectionManager
from api.controller.ChatController import insert_chat
import aiofiles
import asyncio

if not os.path.exists('static/profile'):
    os.makedirs('static/profile')

if not os.path.exists('static/chat'):
    os.makedirs('static/chat')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the database and tables if they do not exist
    if not os.path.exists('database.db'):
        create_db_and_tables()
    yield

# Initialize the FastAPI app with metadata
app = FastAPI(
    title="Chat API",
    description="""
    This API serves as the backend for a chat platform where users can:
    - Register and manage user accounts
    - Send and receive messages (real-time)
    - View chat histories with other users
    """,
    version="1.0.0",
    contact={
        "name": "Obinna Osegbu",
        "url": "https://valentineosegbu.com/contact",
        "email": "valentineosegbu@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Define allowed origins for CORS
origins = [
    "http://localhost:3000"
]

# Add CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include user routes from the User router
app.include_router(User.user_routes)

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, session: SessionDep):
    connect = await manager.connect(websocket, user_id, session)
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=15)
                await handle_received_data(websocket, data, session)
            except asyncio.TimeoutError:
                await websocket.close(code=1001, reason="Ping timeout")
                await manager.disconnect(user_id, session)
                break
    except WebSocketDisconnect:
        await manager.disconnect(user_id, session)
        

async def handle_received_data(websocket: WebSocket, data: str, session: SessionDep):
    try:
        json_data = json.loads(data)
        message_type = json_data.get('type')

        if message_type == 'chat':
            await handle_chat(json_data, session)

        if message_type in ['typing', 'blur']:
            await manager.typing_indicator(message_type, json_data['receiver_id'], json_data['sender_id'])

        if message_type == 'ping':
            await websocket.send_text(json.dumps({'type': 'pong'}))
        
        if message_type == 'ack':
            await manager.acknowledge_message(json_data['message_id'])

    except json.JSONDecodeError:
        print("Received invalid JSON data")
    except KeyError as e:
        print(f"Missing key in received data: {e}")
    except Exception as e:
        print(f"Unexpected error while handling data: {e}")

async def handle_chat(json_data: dict, session: SessionDep):
    try:
        sender_id = int(json_data['sender_id'])
        receiver_id = int(json_data['receiver_id'])
        message = json_data['message']
        uuid = json_data['uuid']
        created_at = json_data['created_at']
        file_data = json_data.get('file')

        image_url = None
        if file_data:
            image_url = await handle_file_upload(file_data)

        post_data = {
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'message': message,
            'uuid': uuid,
            'image': image_url,
            'status': 'sent',
            'created_at': created_at
        }

        try:
            chat_message = insert_chat(post_data, session)
            if chat_message:
                if sender_id != receiver_id:
                    await manager.send_chat(json.loads(chat_message))
                    await manager.update_msg_status(sender_id, receiver_id, uuid)
                    print(f"Message sent from user {sender_id} to {receiver_id}")

        except Exception as e:
            print(e)
            return
        
    except Exception as e:
        print(f"Error handling chat message: {e}")

async def handle_file_upload(file_data: dict):
    try:
        file_name = file_data['name']
        base64_data = file_data['data']
        file_content = base64.b64decode(base64_data)

        unique_file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}{os.path.splitext(file_name)[1]}"
        file_path = os.path.join("static/chat", unique_file_name)
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)
        return unique_file_name
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise