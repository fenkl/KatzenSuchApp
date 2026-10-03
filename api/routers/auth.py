"""Auth router for FastAPI API with JWT support."""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from datetime import timedelta
from api.models.schemas import LoginRequest, TokenResponse, UserResponse, RefreshTokenRequest, CreateUserRequest
from api.core_security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from core.services.auth_service import auth_service
from api.dependencies import get_current_user, require_admin


router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Login endpoint with JWT token generation."""
    user = auth_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest, current_user = Depends(get_current_user)):
    """Refresh access token."""
    # For now, just create a new token with same user
    # In production, validate refresh token from DB
    access_token = create_access_token(
        data={"sub": current_user.username, "user_id": current_user.user_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """Logout endpoint - client should discard token."""
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user info."""
    user = auth_service.get_user_by_id(current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        active=user.active
    )


@router.post("/users", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def create_user(user_data: CreateUserRequest):
    """Create new user - admin only."""
    user = auth_service.create_user(
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name,
        group_id=user_data.group_id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User creation failed - username may already exist or password too weak"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        active=user.active
    )


@router.get("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def get_user(user_id: int):
    """Get user by ID - admin only."""
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        active=user.active
    )


@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def deactivate_user(user_id: int):
    """Deactivate user - admin only."""
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = auth_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )
    
    return {"message": f"User {user.username} deactivated"}


@router.put("/users/{user_id}/password")
async def change_password(user_id: int, password_data: dict, current_user = Depends(get_current_user)):
    """Change user password."""
    # Users can only change their own password unless admin
    if current_user.user_id != user_id and not auth_service.is_admin(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change password for another user"
        )
    
    new_password = password_data.get("password")
    if not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required"
        )
    
    success = auth_service.update_user_password(user_id, new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password update failed"
        )
    
    return {"message": "Password updated successfully"}


@router.get("/admin/users")
async def list_users(current_user = Depends(require_admin)):
    """List all users - admin only."""
    conn = auth_service._get_auth_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, full_name, active, group_id, created_at '
            'FROM users ORDER BY created_at DESC'
        )
        rows = cursor.fetchall()
        
        users = []
        for row in rows:
            users.append({
                "id": row[0],
                "username": row[1],
                "full_name": row[2],
                "active": bool(row[3]),
                "group_id": row[4],
                "created_at": row[5]
            })
        
        return {"users": users, "total": len(users)}
    finally:
        conn.close()
