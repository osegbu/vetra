from fastapi import APIRouter, Depends
from models.User import CreateUser, UserResponse, Auth
from db.db import SessionDep
from api.controller.UserController import create_user, login_user, fetch_users, auth
from utils.jwt_utils import decode_access_token

user_routes = APIRouter()

@user_routes.post(
    "/users/signup", 
    summary="Register a new user", 
    description="Creates a new user account using the provided registration details."
)
def create_user_endpoint(user_data: CreateUser, session: SessionDep):
    """
    Endpoint to register a new user.
    
    Args:
        user_data (CreateUser): The user registration details.
        session (SessionDep): The database session dependency.
    
    Returns:
        JSON response with the created user details.
    """
    return create_user(user_data, session)

@user_routes.post(
    "/users/login", 
    summary="Login user", 
    description="Authenticates a user with their credentials and provides an access token."
)
def login_user_endpoint(user_data: CreateUser, session: SessionDep):
    """
    Endpoint to login a user.
    
    Args:
        user_data (CreateUser): The user login credentials.
        session (SessionDep): The database session dependency.
    
    Returns:
        JSON response with the access token.
    """
    return login_user(user_data, session)

@user_routes.get(
    "/users/me", 
    response_model=Auth, 
    summary="Fetch the logged in user", 
    description="Retrieves the details of the currently logged in user."
)
def auth_endpoint(session: SessionDep, token: dict = Depends(decode_access_token)):
    """
    Endpoint to fetch the currently logged in user.
    
    Args:
        session (SessionDep): The database session dependency.
        token (dict): The decoded access token.
    
    Returns:
        JSON response with the authenticated user details.
    """
    return auth(token['id'], session)

@user_routes.get(
    "/users", 
    response_model=list[UserResponse], 
    summary="Fetch all users", 
    description="Retrieves a list of all registered users."
)
def fetch_all_users_endpoint(session: SessionDep, token: dict = Depends(decode_access_token)):
    """
    Endpoint to fetch all registered users.
    
    Args:
        session (SessionDep): The database session dependency.
    
    Returns:
        JSON response with the list of all users.
    """
    return fetch_users(token['id'], session)
