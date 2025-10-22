from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import models, schemas
from .database import get_db
import os
from dotenv import load_dotenv
import hashlib
import hmac

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    salt = os.urandom(32)  # Generate a random 32 byte salt
    key = hashlib.pbkdf2_hmac(
        'sha256',  # Hash algorithm
        password.encode('utf-8'),  # Convert the password to bytes
        salt,  # Provide the salt
        100000,  # Number of iterations
    )
    # Store salt and key together
    return salt.hex() + ':' + key.hex()

def verify_password(plain_password: str, stored_password: str) -> bool:
    """Verify a stored password against one provided by user"""
    try:
        salt_str, key_str = stored_password.split(':')
        salt = bytes.fromhex(salt_str)
        stored_key = bytes.fromhex(key_str)
        
        # Use the same parameters as used for hashing
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt,
            100000,
        )
        
        return hmac.compare_digest(new_key, stored_key)
    except Exception:
        return False

def authenticate_shop(db: Session, email: str, password: str):
    shop = db.query(models.Shop).filter(models.Shop.email == email).first()
    if not shop:
        return False
    if not verify_password(password, shop.hashed_password):
        return False
    return shop

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_shop(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    shop = db.query(models.Shop).filter(models.Shop.email == token_data.email).first()
    if shop is None:
        raise credentials_exception
    return shop