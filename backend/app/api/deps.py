from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.entities import User, UserRole, Client
from app.schemas.auth import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Validate bearer token and return authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    email: Optional[str] = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return user

async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Strictly enforce Admin role. Clients are forbidden."""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required. Client accounts cannot access coordinator endpoints."
        )
    return current_user

async def require_client(
    current_user: User = Depends(get_current_user)
) -> User:
    """Strictly enforce Client role. Admins cannot impersonate training clients directly."""
    if current_user.role != UserRole.CLIENT.value or not current_user.client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client role required. Only registered healthcare clients can perform local FL training operations."
        )
    return current_user

def require_client_isolation(requested_client_id: str):
    """
    Factory dependency ensuring client isolation.
    Client A can NEVER inspect or submit on behalf of Client B or C.
    """
    async def _verifier(current_user: User = Depends(require_client)) -> User:
        if current_user.client_id != requested_client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Private boundary violation. You are authenticated as '{current_user.client_id}' and cannot access data or endpoints for '{requested_client_id}'."
            )
        return current_user
    return _verifier
