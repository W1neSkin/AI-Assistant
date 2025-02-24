from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.core.jwt import create_access_token, create_refresh_token
from app.utils.security import verify_password, get_password_hash
from app.services.db_service import DatabaseService
from app.utils.logger import setup_logger
from app.dependencies import get_db_service


logger = setup_logger(__name__)
router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    login_request: LoginRequest,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Endpoint to authenticate a user and return JWT tokens."""
    logger.info(f"Logging in user: {login_request.username}")
    async with db_service.async_session() as db:       
        user = await db.scalar(
            select(User).where(User.username == login_request.username)
        )
        
        if not user or not verify_password(login_request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Set token expiration based on remember_me
        access_expires = timedelta(days=7) if login_request.remember_me else timedelta(minutes=15)
        refresh_expires = timedelta(days=7) if login_request.remember_me else timedelta(days=1)
        
        access_token = create_access_token(data={"sub": user.username}, expires_delta=access_expires)
        refresh_token = create_refresh_token(data={"sub": user.username}, expires_delta=refresh_expires)
        
        logger.info(f"User {user.username} logged in successfully")
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    register_request: RegisterRequest,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Endpoint to register a new user."""
    if register_request.password != register_request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Passwords do not match"
        )
    
    # Check if user exists
    async with db_service.async_session() as db:
        existing_user = await db.scalar(
            select(User).where(User.username == register_request.username)
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Create new user
        user = User(
            username=register_request.username,
            hashed_password=get_password_hash(register_request.password),
            use_cloud=register_request.use_cloud,
            enable_document_search=register_request.enable_document_search,
            handle_urls=register_request.handle_urls,
            check_db=register_request.check_db
        )
        db.add(user)
        await db.commit()
        return {"message": "User created successfully"} 