# app/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database.connection import get_db
from ..schemas.user import UserCreate, UserResponse, UserUpdate
from ..services.user_service import (
    create_user, get_users, get_user_by_id, 
    update_user, delete_user, get_commercials, get_inactive_users
)
from ..services.auth import get_current_user
from ..models.user import UserRole, User
from ..utils.exceptions import UnauthorizedAccess

router = APIRouter()

def require_admin_or_manager(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise UnauthorizedAccess("Accès réservé aux administrateurs et managers")
    return current_user

@router.post("/users", response_model=UserResponse)
def create_new_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    return create_user(db, user_data)

@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    return get_users(db, skip, limit)

@router.get("/users/commercials", response_model=List[UserResponse])
def list_commercials(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    return get_commercials(db)

@router.get("/users/inactive", response_model=List[UserResponse])
def list_inactive_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Récupère la liste des utilisateurs inactifs.
    Seuls les administrateurs et les managers peuvent accéder à cette fonctionnalité.
    """
    return get_inactive_users(db)

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user_info(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    user = update_user(db, user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user

@router.delete("/users/{user_id}")
def delete_user_account(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return {"message": "Utilisateur supprimé avec succès"}