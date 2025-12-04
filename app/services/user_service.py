# app/services/user_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.user import User, UserRole
from ..schemas.user import UserCreate, UserUpdate
from ..utils.security import get_password_hash

def create_user(db: Session, user_data: UserCreate) -> User:
    # Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise ValueError("Un utilisateur avec cet email existe déjà")
    
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone_number=user_data.phone_number,
        role=user_data.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()

def get_commercials(db: Session) -> List[User]:
    return db.query(User).filter(
        User.role == UserRole.COMMERCIAL,
        User.is_active == True
    ).all()

def get_inactive_users(db: Session) -> List[User]:
    return db.query(User).filter(User.is_active == False).all()

def get_user_by_id(db: Session, user_id: int, include_inactive: bool = False) -> Optional[User]:
    query = db.query(User).filter(User.id == user_id)
    if not include_inactive:
        query = query.filter(User.is_active == True)
    return query.first()

def get_user_by_email(db: Session, email: str, include_inactive: bool = False) -> Optional[User]:
    query = db.query(User).filter(User.email == email)
    if not include_inactive:
        query = query.filter(User.is_active == True)
    return query.first()

def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
    # On utilise include_inactive=True pour pouvoir réactiver un utilisateur inactif
    user = get_user_by_id(db, user_id, include_inactive=True)
    if not user:
        return None
    
    update_data = user_data.dict(exclude_unset=True)
    
    # Hasher le mot de passe si fourni
    if 'password' in update_data:
        update_data['password_hash'] = get_password_hash(update_data.pop('password'))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int) -> bool:
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    # Soft delete
    user.is_active = False
    db.commit()
    return True