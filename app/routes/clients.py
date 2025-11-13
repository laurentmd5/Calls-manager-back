# app/routes/clients.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from ..database.connection import get_db
from ..schemas.client import ClientCreate, ClientResponse, ClientUpdate
from ..services.client_service import (
    create_client, get_clients, get_client_by_id,
    update_client, delete_client, get_commercial_clients,
    import_clients_from_excel, redistribute_clients
)
from ..utils.security import verify_token
from ..models.user import UserRole

router = APIRouter()

def get_current_user(token: str = Depends(verify_token)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )
    return token

@router.post("/clients", response_model=ClientResponse)
def create_new_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Les commerciaux ne peuvent créer que leurs propres clients
    if current_user["role"] == UserRole.COMMERCIAL:
        client_data.commercial_id = current_user["user_id"]
    
    return create_client(db, client_data)

@router.get("/clients", response_model=List[ClientResponse])
def list_clients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] == UserRole.COMMERCIAL:
        return get_commercial_clients(db, current_user["user_id"], skip, limit)
    else:
        return get_clients(db, skip, limit)

@router.get("/clients/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    client = get_client_by_id(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    # Vérifier que le commercial peut accéder à ce client
    if (current_user["role"] == UserRole.COMMERCIAL and 
        client.commercial_id != current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    return client

@router.put("/clients/{client_id}", response_model=ClientResponse)
def update_client_info(
    client_id: int,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    client = get_client_by_id(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    # Vérifier les permissions
    if (current_user["role"] == UserRole.COMMERCIAL and 
        client.commercial_id != current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    return update_client(db, client_id, client_data)

@router.delete("/clients/{client_id}")
def delete_client_record(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    client = get_client_by_id(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    # Seuls les admins peuvent supprimer des clients
    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    success = delete_client(db, client_id)
    if not success:
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression")
    
    return {"message": "Client supprimé avec succès"}

@router.post("/clients/import")
async def import_clients(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Format de fichier non supporté")
    
    try:
        result = await import_clients_from_excel(db, file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import: {str(e)}")

@router.post("/clients/redistribute")
def redistribute_clients_to_commercials(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    try:
        result = redistribute_clients(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la redistribution: {str(e)}")