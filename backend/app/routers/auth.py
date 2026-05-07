# Author: Oleg Andriichuk, xandri07
# Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.user import UserCreate, UserLogin, Token, UserResponse, UserUpdate, UserUpdateResponse
from ..repositories import users_repository
from ..utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..services.deletion_service import deletion_service

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db)
):
    existing_user = await users_repository.get_user_by_email(session, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(user_data.password)
    user = await users_repository.create_user(
        session,
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password
    )
    await session.commit()
    await session.refresh(user)

    return user

@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    session: AsyncSession = Depends(get_db)
):
    user = await users_repository.get_user_by_email(session, user_data.email)
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.patch("/me", response_model=UserUpdateResponse)
async def update_current_user(
    data: UserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update name, email, and/or password of the current user."""
    if data.email and data.email != current_user.email:
        existing = await users_repository.get_user_by_email(session, data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

    await users_repository.update_user(
        session,
        current_user,
        name=data.name,
        email=data.email,
        hashed_password=get_password_hash(data.password) if data.password else None,
    )
    await session.commit()
    await session.refresh(current_user)

    # Always issue a new token so an email change doesn't invalidate the session
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=access_token_expires
    )

    return {"user": current_user, "access_token": access_token, "token_type": "bearer"}


@router.delete("/me")
async def delete_current_user(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete the current user and all their projects/photos (DB + S3)"""
    await deletion_service.delete_user(session, current_user)
    return {"ok": True, "id": current_user.id}
