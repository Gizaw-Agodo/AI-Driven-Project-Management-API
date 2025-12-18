from datetime import datetime, timedelta
import string
from typing import Any, Dict, Optional
from passlib.context import CryptContext
from app.core.config import settings
from jose import JWTError, jwt
import secrets

pwd_context = CryptContext( schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12 )

def hash_password(password:str)-> str : 
    print(password,'hash passwd')
    return pwd_context.hash('password')

def verify_password(plain_password: str, hashed_password : str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except:
        return False

def create_access_token(
    data : dict[str, Any], 
    expires_delta : Optional[timedelta] = None
) -> str : 

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data : dict[str, Any])-> str : 
    to_encode = data.copy()
    expire = datetime.utcnow()+ timedelta(days = 7)
    to_encode.update({
        "exp": expire, 
        "iat": datetime.utcnow(),
        "type" : "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )

    return encoded_jwt

def decode_token(token : str) -> Optional[dict[str, Any]]: 
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
            )
        return payload
        
    except JWTError:
        return None


def verify_token_type(payload: dict[str, Any], expected_type: str) -> bool:
    return payload.get("type") == expected_type


def create_token_pair(user_id: int, username: str, email: str) -> Dict[str, str]:
    # Prepare token data
    token_data = {
        "sub": str(user_id),  
        "username": username,
        "email": email
    }
    
    # Create both tokens
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

def generate_random_token(length: int = 32) -> str : 
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def generate_verification_code(length: int = 6) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(length))

