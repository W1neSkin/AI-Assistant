from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy import select

from app.core.jwt import decode_token
from app.services.db_service import DatabaseService
from app.core.service_container import ServiceContainer
from app.models.user import User
from app.dependencies import get_db_service


security = HTTPBearer()

async def get_current_user(
        token=Depends(security), 
        db_service: DatabaseService = Depends(get_db_service)
) -> User:
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    async with db_service.async_session() as db:
        user = await db.scalar(select(User).where(User.username == payload.get("sub")))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user 