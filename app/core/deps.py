"""T
    his module contains dependencies for FastAPI 
    routes, including user authentication and database 
    session management.
"""


import uuid

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session as DBSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer(auto_error=False)
# oauth2_scheme = HTTPBearer()


def get_current_user(
        token: HTTPAuthorizationCredentials = Depends(security),
        db: DBSession = Depends(get_db),
) -> User:
    credentials_exeption = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate" : "Bearer"}
    )
    try:
        payload = decode_access_token(token.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exeption
    except JWTError:
        raise credentials_exeption
    
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if user is None:
        raise credentials_exeption
    return user



def get_current_user_optional(
    token: HTTPAuthorizationCredentials | None = Depends(security),
    db: DBSession = Depends(get_db),
) -> User | None:
    if token is None:
        return None
    try:
        payload = decode_access_token(token.credentials)
        user_id = payload.get("sub")
        return db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    except (JWTError, ValueError):
        return None