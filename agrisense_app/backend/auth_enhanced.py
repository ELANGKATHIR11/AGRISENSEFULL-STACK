"""
JWT Authentication and User Management for AgriSense
Enhanced security with role-based access control
"""
# type: ignore  # Suppress type checking for optional auth dependencies

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request

# FastAPI imports with fallback
try:
    from fastapi import Depends, HTTPException, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    Depends = HTTPException = status = HTTPBearer = HTTPAuthorizationCredentials = None

try:
    from fastapi_users import BaseUserManager, FastAPIUsers  # type: ignore
    from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTAuthentication, CookieTransport  # type: ignore
    from fastapi_users.db import SQLAlchemyUserDatabase  # type: ignore
    FASTAPI_USERS_AVAILABLE = True
except ImportError:
    FASTAPI_USERS_AVAILABLE = False
    BaseUserManager = FastAPIUsers = None  # type: ignore
    AuthenticationBackend = BearerTransport = JWTAuthentication = CookieTransport = None
    SQLAlchemyUserDatabase = None  # type: ignore

try:
    import jwt  # PyJWT library
    from jwt.exceptions import InvalidTokenError as JWTError
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False
    JWTError = jwt = None  # type: ignore

try:
    from passlib.context import CryptContext  # type: ignore
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False
    
    class CryptContext:
        def __init__(self, *args, **kwargs):
            pass
        def hash(self, password):
            return f"hashed_{password}"
        def verify(self, password, hashed):
            return f"hashed_{password}" == hashed

from pydantic import BaseModel, EmailStr

try:
    from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore
    from sqlalchemy import select, update  # type: ignore
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    AsyncSession = None  # type: ignore
    
    def select(*args, **kwargs):  # type: ignore
        return None
    
    def update(*args, **kwargs):  # type: ignore
        return None

import logging

try:
    from .database_enhanced import User, get_async_session  # type: ignore
except ImportError:
    User = None
    
    async def get_async_session():
        return None

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("AGRISENSE_JWT_SECRET", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
if PASSLIB_AVAILABLE and CryptContext:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
else:
    pwd_context = None

# Security schemes
if FASTAPI_AVAILABLE and HTTPBearer:
    bearer_scheme = HTTPBearer()
else:
    bearer_scheme = None


# User roles and permissions
class UserRole:
    ADMIN = "admin"
    FARM_MANAGER = "farm_manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        "read:all",
        "write:all",
        "delete:all",
        "manage:users",
        "manage:system",
        "manage:irrigation",
        "view:analytics",
        "export:data",
    ],
    UserRole.FARM_MANAGER: [
        "read:farm",
        "write:farm",
        "manage:irrigation",
        "view:analytics",
        "export:data",
        "manage:zones",
    ],
    UserRole.OPERATOR: ["read:farm", "write:sensors", "manage:irrigation", "view:basic_analytics"],
    UserRole.VIEWER: ["read:basic", "view:dashboard"],
}


# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: str = UserRole.VIEWER
    farm_id: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    farm_id: Optional[str] = None
    is_active: Optional[bool] = None


class UserRead(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    farm_id: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[List[str]] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# User Manager
if FASTAPI_USERS_AVAILABLE and User is not None:
    class UserManager(BaseUserManager[User, str]):  # type: ignore
        reset_password_token_secret = SECRET_KEY
        verification_token_secret = SECRET_KEY

        async def on_after_register(self, user, request: Optional[Request] = None):  # type: ignore
            logger.info(f"User {user.id} has registered.")

        async def on_after_login(self, user, request: Optional[Request] = None):  # type: ignore
            # Update last login timestamp
            if SQLALCHEMY_AVAILABLE:
                async with get_async_session() as session:  # type: ignore
                    await session.execute(update(User).where(User.id == user.id).values(last_login=datetime.utcnow()))  # type: ignore
                    await session.commit()
            logger.info(f"User {user.id} logged in.")

        async def on_after_forgot_password(self, user, token: str, request: Optional[Request] = None):  # type: ignore
            logger.info(f"User {user.id} has forgot their password. Reset token: {token}")

        async def on_after_request_verify(self, user, token: str, request: Optional[Request] = None):  # type: ignore
            logger.info(f"Verification requested for user {user.id}. Verification token: {token}")
else:
    class UserManager:  # type: ignore
        """Mock UserManager when FastAPI-Users not available"""
        pass


# User database adapter
if FASTAPI_USERS_AVAILABLE and SQLALCHEMY_AVAILABLE:
    async def get_user_db(session=Depends(get_async_session)):  # type: ignore
        yield SQLAlchemyUserDatabase(session, User)  # type: ignore

    # User manager dependency for FastAPIUsers (must return instance, not generator)
    async def get_user_manager_instance_real():
        async for user_db in get_user_db():
            return UserManager()
else:
    async def get_user_db():  # type: ignore
        """Mock user database when dependencies not available"""
        yield None
        
    async def get_user_manager_instance_mock():  # type: ignore
        """Mock user manager when dependencies not available"""
        return UserManager()  # type: ignore


# Authentication backends
if FASTAPI_USERS_AVAILABLE:
    bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")  # type: ignore
    cookie_transport = CookieTransport(cookie_max_age=3600, cookie_secure=False)  # type: ignore

    jwt_authentication = JWTAuthentication(  # type: ignore
        secret=SECRET_KEY,
        lifetime_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        tokenUrl="auth/jwt/login",
    )

    cookie_authentication = JWTAuthentication(  # type: ignore
        secret=SECRET_KEY,
        lifetime_seconds=3600,
        tokenUrl="auth/cookie/login",
    )

    def get_jwt_strategy():
        if jwt_authentication is None:
            raise RuntimeError("JWTAuthentication is not initialized")
        return jwt_authentication

    def get_cookie_strategy():
        if cookie_authentication is None:
            raise RuntimeError("CookieAuthentication is not initialized")
        return cookie_authentication

    auth_backend_jwt = AuthenticationBackend(  # type: ignore
        name="jwt",
        transport=bearer_transport,
        get_strategy=get_jwt_strategy,
    )

    auth_backend_cookie = AuthenticationBackend(  # type: ignore
        name="cookie",
        transport=cookie_transport,
        get_strategy=get_cookie_strategy,
    )
else:
    bearer_transport = cookie_transport = None  # type: ignore
    jwt_authentication = cookie_authentication = None  # type: ignore
    auth_backend_jwt = auth_backend_cookie = None  # type: ignore

# FastAPI Users instance
if FASTAPI_USERS_AVAILABLE and FastAPIUsers and User:
    backends = [b for b in [auth_backend_jwt, auth_backend_cookie] if b is not None]

    # Create FastAPIUsers at runtime. Use type: ignore because static analysis
    # may not understand the project's dynamic User model and FastAPI-Users generics.
    try:
        fastapi_users = FastAPIUsers(get_user_manager_instance_real, backends)  # type: ignore
        current_active_user = fastapi_users.current_user(active=True)  # type: ignore
        current_verified_user = fastapi_users.current_user(verified=True)  # type: ignore
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning(f"Failed to initialize FastAPIUsers: {exc}")
        fastapi_users = None
        current_active_user = current_verified_user = None
else:
    fastapi_users = None
    current_active_user = current_verified_user = None


# Token utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # type: ignore
    return encoded_jwt


def create_refresh_token(data: dict) -> str:  # type: ignore
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # type: ignore
    return encoded_jwt


async def verify_token(credentials=Depends(bearer_scheme)):  # type: ignore
    """Verify JWT token and extract user information"""
    credentials_exception = HTTPException(  # type: ignore
        status_code=status.HTTP_401_UNAUTHORIZED,  # type: ignore
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Get user from database to fetch role and permissions
        async with get_async_session() as session:  # type: ignore
            result = await session.execute(select(User).where(User.id == user_id))  # type: ignore
            user = result.scalar_one_or_none()

            if user is None:
                raise credentials_exception

            permissions = ROLE_PERMISSIONS.get(user.role, [])

            token_data = TokenData(username=user.email, user_id=user.id, role=user.role, permissions=permissions)
    except JWTError:  # type: ignore
        raise credentials_exception

    return token_data


# Permission checking utilities  
def require_permission(permission: str):  # type: ignore
    """Decorator to require specific permission"""

    async def permission_checker(token_data=Depends(verify_token)):  # type: ignore
        if permission not in (token_data.permissions or []):
            raise HTTPException(  # type: ignore
                status_code=status.HTTP_403_FORBIDDEN,  # type: ignore
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return token_data

    return permission_checker


def require_role(required_role: str):  # type: ignore
    """Decorator to require specific role"""

    async def role_checker(token_data=Depends(verify_token)):  # type: ignore
        if token_data.role != required_role:
            raise HTTPException(  # type: ignore
                status_code=status.HTTP_403_FORBIDDEN,  # type: ignore
                detail=f"Insufficient role. Required: {required_role}"
            )
        return token_data

    return role_checker


def require_any_role(required_roles: List[str]):  # type: ignore
    """Decorator to require any of the specified roles"""

    async def role_checker(token_data=Depends(verify_token)):  # type: ignore
        if token_data.role not in required_roles:
            raise HTTPException(  # type: ignore
                status_code=status.HTTP_403_FORBIDDEN,  # type: ignore
                detail=f"Insufficient role. Required one of: {required_roles}"
            )
        return token_data

    return role_checker


# Admin utilities
async def get_admin_user(token_data=Depends(require_role(UserRole.ADMIN))):  # type: ignore
    """Get current admin user"""
    return token_data


async def get_farm_manager_or_admin(
    token_data=Depends(require_any_role([UserRole.ADMIN, UserRole.FARM_MANAGER]))  # type: ignore
):
    """Get current farm manager or admin user"""
    return token_data


# Farm access utilities
async def verify_farm_access(farm_id: str, token_data=Depends(verify_token)):  # type: ignore
    """Verify user has access to specific farm"""
    if token_data.role == UserRole.ADMIN:  # type: ignore
        return True  # Admins have access to all farms

    if token_data.role in [UserRole.FARM_MANAGER, UserRole.OPERATOR, UserRole.VIEWER]:  # type: ignore
        # Get user's farm_id from database
        async with get_async_session() as session:  # type: ignore
            result = await session.execute(select(User).where(User.id == token_data.user_id))  # type: ignore
            user = result.scalar_one_or_none()  # type: ignore

            if user and user.farm_id == farm_id:  # type: ignore
                return True

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this farm")  # type: ignore


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:  # type: ignore
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)  # type: ignore


def get_password_hash(password: str) -> str:  # type: ignore
    """Hash password"""
    return pwd_context.hash(password)  # type: ignore


# User creation utilities
async def create_user(user_data, session) -> User:  # type: ignore
    """Create new user with hashed password"""
    hashed_password = get_password_hash(user_data.password)  # type: ignore

    user = User(  # type: ignore
        email=user_data.email,  # type: ignore
        hashed_password=hashed_password,  # type: ignore
        first_name=user_data.first_name,  # type: ignore
        last_name=user_data.last_name,  # type: ignore
        role=user_data.role,  # type: ignore
        farm_id=user_data.farm_id,  # type: ignore
        is_active=True,  # type: ignore
        is_verified=False,  # type: ignore
        created_at=datetime.utcnow(),  # type: ignore
    )

    session.add(user)  # type: ignore
    await session.commit()  # type: ignore
    await session.refresh(user)  # type: ignore

    return user  # type: ignore


# Authentication endpoints utilities
async def authenticate_user(email: str, password: str):  # type: ignore
    """Authenticate user with email and password"""
    async with get_async_session() as session:  # type: ignore
        result = await session.execute(select(User).where(User.email == email))  # type: ignore
        user = result.scalar_one_or_none()  # type: ignore

        if user and verify_password(password, user.hashed_password):  # type: ignore
            # Update last login
            await session.execute(update(User).where(User.id == user.id).values(last_login=datetime.utcnow()))  # type: ignore
            await session.commit()  # type: ignore
            return user

    return None


async def login_user(login_data):  # type: ignore
    """Login user and return tokens"""
    user = await authenticate_user(login_data.email, login_data.password)  # type: ignore

    if not user:
        raise HTTPException(  # type: ignore
            status_code=status.HTTP_401_UNAUTHORIZED,  # type: ignore
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:  # type: ignore
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")  # type: ignore

    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # type: ignore

    token_data = {"sub": user.id, "email": user.email, "role": user.role}  # type: ignore

    access_token = create_access_token(data=token_data, expires_delta=access_token_expires)  # type: ignore

    refresh_token = create_refresh_token(data={"sub": user.id})  # type: ignore

    return Token(  # type: ignore
        access_token=access_token,  # type: ignore
        refresh_token=refresh_token,  # type: ignore
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # type: ignore
    )


# Security middleware utilities
async def get_current_user_optional(
    credentials=Depends(HTTPBearer(auto_error=False)),  # type: ignore
):  # type: ignore
    """Get current user without requiring authentication"""
    if not credentials:
        return None

    try:
        token_data = await verify_token(credentials)  # type: ignore
        return token_data
    except HTTPException:  # type: ignore
        return None


# Rate limiting per user
user_request_counts: Dict[str, Dict[str, int]] = {}  # type: ignore


async def check_user_rate_limit(
    token_data=Depends(verify_token), max_requests: int = 100, window_minutes: int = 60  # type: ignore
):
    """Check rate limit for authenticated user"""
    current_minute = datetime.utcnow().replace(second=0, microsecond=0)  # type: ignore
    window_key = current_minute.strftime("%Y-%m-%d_%H:%M")

    if token_data.user_id is None:  # type: ignore
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")  # type: ignore

    if token_data.user_id not in user_request_counts:  # type: ignore
        user_request_counts[token_data.user_id] = {}  # type: ignore

    user_counts = user_request_counts[token_data.user_id]  # type: ignore

    # Clean old entries
    cutoff_time = current_minute - timedelta(minutes=window_minutes)  # type: ignore
    keys_to_remove = [key for key in user_counts.keys() if datetime.strptime(key, "%Y-%m-%d_%H:%M") < cutoff_time]  # type: ignore

    for key in keys_to_remove:
        del user_counts[key]

    # Check current count
    current_count = user_counts.get(window_key, 0)

    if current_count >= max_requests:
        raise HTTPException(  # type: ignore
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,  # type: ignore
            detail=f"Rate limit exceeded. Max {max_requests} requests per {window_minutes} minutes.",
        )

    # Increment count
    user_counts[window_key] = current_count + 1

    return token_data  # type: ignore


# Admin Guard for API protection
class AdminGuard:  # type: ignore
    """Guard for admin-only endpoints"""
    
    def __init__(self, required_token=None):  # type: ignore
        self.required_token = required_token or os.getenv("AGRISENSE_ADMIN_TOKEN", "admin123")  # type: ignore
    
    def __call__(self, func):  # type: ignore
        """Decorator to protect admin endpoints"""
        if not FASTAPI_AVAILABLE:
            return func
            
        async def wrapper(*args, **kwargs):  # type: ignore
            # Extract request from args/kwargs
            request = None  # type: ignore
            for arg in args:
                if hasattr(arg, 'headers'):  # type: ignore
                    request = arg  # type: ignore
                    break
            
            if request and hasattr(request, 'headers'):  # type: ignore
                admin_token = request.headers.get("X-Admin-Token")  # type: ignore
                if admin_token != self.required_token:  # type: ignore
                    if HTTPException and status:  # type: ignore
                        raise HTTPException(  # type: ignore
                            status_code=status.HTTP_403_FORBIDDEN,  # type: ignore
                            detail="Admin access required"
                        )
                    else:
                        raise Exception("Admin access required")  # type: ignore
            
            return await func(*args, **kwargs)  # type: ignore
        
        return wrapper  # type: ignore
