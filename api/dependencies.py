"""Dependencies for FastAPI API."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from classes.Cconfig import Config
from api.core_security import decode_access_token, get_current_user_from_token
from core.services.auth_service import auth_service


security = HTTPBearer(auto_error=False)


def get_db_connection():
    """Database connection dependency."""
    from modules.db_utils import get_connection
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def get_config():
    """Config dependency."""
    return Config()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Check if user still exists and is active
    user = auth_service.get_user_by_username(username)
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return UserInfo(username=username, user_id=user.id, active=user.active)


def require_admin(current_user = Depends(get_current_user)):
    """Require admin permissions."""
    if not auth_service.is_admin(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    return current_user


class UserInfo:
    """User info from token."""
    def __init__(self, username: str, user_id: int, active: bool):
        self.username = username
        self.user_id = user_id
        self.active = active
