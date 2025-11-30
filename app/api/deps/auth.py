
from fastapi import Depends, HTTPException, status
from fastapi.security import  HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.api.deps.database import get_db

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",  
    scheme_name="JWT"
)

async def get_current_user(
    credentials:HTTPAuthorizationCredentials = Depends(oauth2_scheme),
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
        user_id : int = payload.get("sub")

        if not user_id: 
            raise credential_exception
        
        user_repo  = UserRepository(db)
        user = await user_repo.get_by_id(user_id)

        if not user : 
            raise credential_exception
        
        if not user.is_active:
            raise HTTPException( status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    except JWTError:
        raise credential_exception



