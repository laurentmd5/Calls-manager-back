# app/routes/recordings.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
from ..database.connection import get_db
from ..schemas.recording import RecordingResponse, RecordingCreate
from ..services.call_service import get_call_by_id
from ..services.file_upload import save_recording_file
from ..utils.security import verify_token
from ..models.user import UserRole
from config import settings

router = APIRouter()

def get_current_user(token: str = Depends(verify_token)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )
    return token

@router.post("/recordings", response_model=RecordingResponse)
async def upload_recording(
    call_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Vérifier que l'appel existe
    call = get_call_by_id(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Appel non trouvé")
    
    # Vérifier les permissions
    if (current_user["role"] == UserRole.COMMERCIAL and 
        call.commercial_id != current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Vérifier le format du fichier
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Format de fichier audio non supporté")
    
    try:
        recording = await save_recording_file(db, call_id, file)
        return recording
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

@router.get("/recordings/{recording_id}")
def get_recording_info(
    recording_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from ..services.file_upload import get_recording_by_id
    recording = get_recording_by_id(db, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Enregistrement non trouvé")
    
    # Vérifier les permissions
    call = recording.call
    if (current_user["role"] == UserRole.COMMERCIAL and 
        call.commercial_id != current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    return recording

@router.delete("/recordings/{recording_id}")
def delete_recording(
    recording_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from ..services.file_upload import delete_recording_file
    recording = delete_recording_file(db, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Enregistrement non trouvé")
    
    # Vérifier les permissions (admin seulement)
    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    return {"message": "Enregistrement supprimé avec succès"}