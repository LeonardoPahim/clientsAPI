from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.schemas.user import MasterUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

http_bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    description="Enter your JWT in the format: Bearer <token>"
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password.

    Args:
        plain_password: The password in plain text.
        hashed_password: The hashed version of the password to compare against.

    Returns:
        True if the plain password matches the hashed password, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hashes a plain password using the configured hashing algorithm (bcrypt).

    This is mainly intended for initial setup, e.g., creating the
    MASTER_PASSWORD_HASH for the .env file.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password string.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT access token.

    The token will contain the provided data as its payload and will be signed
    using the SECRET_KEY and ALGORITHM specified in the application settings.
    It includes "exp" (expiration time) and "iat" (issued at) claims.

    Args:
        data: A dictionary containing the data to include in the token's payload
              (e.g., {"sub": username, "role": role}).
        expires_delta: An optional timedelta object or an integer representing minutes
                       for the token's lifespan. If None, it defaults to
                       `settings.MASTER_TOKEN_EXPIRE_MINUTES` for master tokens.
                       If an int is provided, it's treated as minutes.

    Returns:
        The encoded JWT string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.MASTER_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer_scheme)
) -> MasterUser:
    """
    Dependency function to get the current authenticated admin user from a JWT token.

    It decodes the provided JWT token, validates its signature and expiration,
    and checks if the user details ("sub" and "role") within the token correspond
    to the configured master admin user.

    This function is typically used as a dependency in FastAPI path operations
    to protect routes that require admin authentication.

    Args:
        token: The JWT token string, automatically extracted from the request
               by FastAPI using the `oauth2_scheme` (OAuth2PasswordBearer).

    Returns:
        A MasterUser Pydantic model instance if the token is valid and represents
        the master admin user.

    Raises:
        HTTPException (status_code 401):
            - If the token cannot be decoded (e.g., invalid format, signature, expired).
            - If the token payload is missing "sub" or "role" claims.
            - If the "sub" or "role" claims do not match the master admin credentials
              (settings.MASTER_USERNAME and role "master").
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Admin access required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role")

        if username is None or role is None:
            raise credentials_exception

        if role == "master" and username == settings.MASTER_USERNAME:
            return MasterUser(username=username, role="master")
        else:
            raise credentials_exception
    except JWTError:
        raise credentials_exception