from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.entities import User, Client
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user (Admin or Client) and return JWT access token with role claims.
    """
    result = await db.execute(select(User).where(User.email == payload.email.lower().strip()))
    user = result.scalars().first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact the administrator."
        )

    institution_name = None
    if user.client_id:
        client_res = await db.execute(select(Client).where(Client.id == user.client_id))
        client = client_res.scalars().first()
        if client:
            institution_name = client.name

    access_token = create_access_token(
        subject=user.email,
        role=user.role,
        client_id=user.client_id,
        institution_name=institution_name,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        client_id=user.client_id,
        institution_name=institution_name,
        email=user.email
    )

@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """Return profile of the currently authenticated user."""
    return current_user
