from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.core.jwt import create_access_token, create_refresh_token
from app.utils.security import verify_password, get_password_hash
from sqlalchemy import select

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(
        select(User).where(User.username == request.username)
    )
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Set token expiration based on remember_me
    access_expires = timedelta(days=7) if request.remember_me else timedelta(minutes=15)
    refresh_expires = timedelta(days=7) if request.remember_me else timedelta(days=1)
    
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_expires)
    refresh_token = create_refresh_token(data={"sub": user.username}, expires_delta=refresh_expires)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Passwords do not match"
        )
    
    # Check if user exists
    existing_user = await db.scalar(
        select(User).where(User.username == request.username)
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    user = User(
        username=request.username,
        hashed_password=get_password_hash(request.password),
        use_cloud=request.use_cloud,
        enable_document_search=request.enable_document_search,
        handle_urls=request.handle_urls,
        check_db=request.check_db
    )
    db.add(user)
    await db.commit()
    return {"message": "User created successfully"} 