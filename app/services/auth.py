# app/services/auth.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ..models.user import User
from ..database.connection import get_db
from ..utils.security import verify_password, verify_token

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

security = HTTPBearer()

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Récupère l'utilisateur actuellement connecté à partir du token.
    Le token doit être fourni dans l'en-tête Authorization: Bearer <token>
    """
    credentials: HTTPAuthorizationCredentials = await security(request)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier et décoder le token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier que le payload contient bien un email
    user_email = payload.get("sub")
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide: informations manquantes",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Récupérer l'utilisateur depuis la base de données
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce compte utilisateur est désactivé"
        )
    
    return user