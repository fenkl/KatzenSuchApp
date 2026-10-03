"""
Auth Service
Business logic for authentication and user management.
Integrates with existing FletBase auth DB.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import secrets
import bcrypt
from modules.Mhandle_log import get_logger

log = get_logger(__name__)


@dataclass
class User:
    """User domain entity."""
    id: int
    username: str
    password_hash: str
    full_name: Optional[str] = None
    group_id: Optional[int] = None
    active: bool = True
    created_at: Optional[datetime] = None


@dataclass
class AuthToken:
    """Authentication token entity."""
    token: str
    user_id: int
    username: str
    created_at: datetime
    expires_at: datetime
    active: bool = True


class AuthService:
    """Service for authentication business logic."""
    
    def __init__(self):
        self.auth_db_path = None
        self._init_auth_db()
    
    def _init_auth_db(self):
        """Initialize connection to auth DB."""
        from classes.Cconfig import Config
        config = Config()
        self.auth_db_path = config.auth_db_path
    
    def _get_auth_connection(self):
        """Get connection to auth database."""
        import sqlite3
        return sqlite3.connect(self.auth_db_path)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        conn = self._get_auth_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, username, password_hash, full_name, group_id, active, created_at '
                'FROM users WHERE username = ?',
                (username,)
            )
            row = cursor.fetchone()
            if row:
                return User(
                    id=row[0],
                    username=row[1],
                    password_hash=row[2],
                    full_name=row[3],
                    group_id=row[4],
                    active=bool(row[5]),
                    created_at=row[6]
                )
            return None
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        conn = self._get_auth_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, username, password_hash, full_name, group_id, active, created_at '
                'FROM users WHERE id = ?',
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return User(
                    id=row[0],
                    username=row[1],
                    password_hash=row[2],
                    full_name=row[3],
                    group_id=row[4],
                    active=bool(row[5]),
                    created_at=row[6]
                )
            return None
        finally:
            conn.close()
    
    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception as e:
            log.error(f"Password verification error: {e}")
            return False
    
    def hash_password(self, plain_password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = self.get_user_by_username(username)
        if not user:
            log.warning(f"Authentication failed: user {username} not found")
            return None
        
        if not user.active:
            log.warning(f"Authentication failed: user {username} is inactive")
            return None
        
        if not self.verify_password(password, user.password_hash):
            log.warning(f"Authentication failed: invalid password for {username}")
            return None
        
        log.info(f"User {username} authenticated successfully")
        return user
    
    def create_access_token(
        self,
        user_id: int,
        username: str,
        expires_minutes: int = 30
    ) -> AuthToken:
        """Create access token for user."""
        token = self._generate_token()
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(minutes=expires_minutes)
        
        auth_token = AuthToken(
            token=token,
            user_id=user_id,
            username=username,
            created_at=created_at,
            expires_at=expires_at
        )
        
        # In production, store token in DB with database backend
        # For now, return token object
        return auth_token
    
    def _generate_token(self) -> str:
        """Generate secure random token."""
        return secrets.token_urlsafe(32)
    
    def validate_token(self, token: str) -> Optional[AuthToken]:
        """Validate token and return associated user."""
        # TODO: Implement token validation with database lookup
        # For now, return None (mock implementation)
        # In production, query token store and validate expiration
        log.info(f"Validating token: {token[:10]}...")
        return None
    
    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """Validate password strength."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        if not any(c.isalpha() for c in password):
            return False, "Password must contain at least one letter"
        
        return True, ""
    
    def create_user(
        self,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        group_id: Optional[int] = None
    ) -> Optional[User]:
        """Create new user."""
        # Validate password
        valid, message = self.validate_password_strength(password)
        if not valid:
            log.error(f"Password validation failed: {message}")
            return None
        
        # Check if user exists
        if self.get_user_by_username(username):
            log.error(f"User creation failed: username {username} already exists")
            return None
        
        password_hash = self.hash_password(password)
        
        conn = self._get_auth_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, password_hash, full_name, group_id, active, created_at) '
                'VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)',
                (username, password_hash, full_name, group_id, 1)
            )
            conn.commit()
            user_id = cursor.lastrowid
            
            log.info(f"User {username} created successfully")
            return self.get_user_by_id(user_id)
        except Exception as e:
            log.error(f"User creation error: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def update_user_password(
        self,
        user_id: int,
        new_password: str
    ) -> bool:
        """Update user password."""
        # Validate password
        valid, message = self.validate_password_strength(new_password)
        if not valid:
            log.error(f"Password validation failed: {message}")
            return False
        
        password_hash = self.hash_password(new_password)
        
        conn = self._get_auth_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET password_hash = ? WHERE id = ?',
                (password_hash, user_id)
            )
            conn.commit()
            log.info(f"Password updated for user {user_id}")
            return cursor.rowcount > 0
        except Exception as e:
            log.error(f"Password update error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account."""
        conn = self._get_auth_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET active = 0 WHERE id = ?',
                (user_id,)
            )
            conn.commit()
            log.info(f"User {user_id} deactivated")
            return cursor.rowcount > 0
        except Exception as e:
            log.error(f"User deactivation error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def activate_user(self, user_id: int) -> bool:
        """Activate user account."""
        conn = self._get_auth_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET active = 1 WHERE id = ?',
                (user_id,)
            )
            conn.commit()
            log.info(f"User {user_id} activated")
            return cursor.rowcount > 0
        except Exception as e:
            log.error(f"User activation error: {e}")
            conn.rollback()
            return False
    
    def get_user_groups(self, user_id: int) -> list:
        """Get groups for user."""
        conn = self._get_auth_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT g.id, g.name, g.permissions FROM groups g '
                'JOIN users u ON u.group_id = g.id '
                'WHERE u.id = ?',
                (user_id,)
            )
            rows = cursor.fetchall()
            return [
                {"id": row[0], "name": row[1], "permissions": row[2]}
                for row in rows
            ]
        finally:
            conn.close()
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has specific permission."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        if not user.active:
            return False
        
        groups = self.get_user_groups(user_id)
        for group in groups:
            if group["name"].lower() == "admin":
                return True
        
        return False
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return self.has_permission(user_id, "admin")


# Singleton instance
auth_service = AuthService()
