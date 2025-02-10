from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.jwt import decode_token
from app.db.base import get_db
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    token = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    result = await db.execute(
        select(User).where(User.username == payload.get("sub"))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user 