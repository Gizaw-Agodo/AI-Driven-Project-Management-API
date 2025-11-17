
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.api.deps.database import get_db
security = HTTPBearer()

async def get_user(
    credentials:HTTPAuthorizationCredentials = Depends(security),
    db:AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials

    credential_exception = HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail = "Could not validate credentials",
        headers={"WWW-Authenticate" : "Brearere"}
    )

    try: 
        payload = decode_token(token)
        if payload is None: 
            raise credential_exception
            #to be continued 
    except JWTError:
        raise credential_exception



