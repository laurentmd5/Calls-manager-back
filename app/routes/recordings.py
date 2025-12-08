# app/routes/recordings.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from sqlalchemy.orm import Session
from typing import List
import os
from ..database.connection import get_db
from ..schemas.recording import RecordingResponse, RecordingCreate
from ..services.call_service import get_call_by_id
from ..services.file_upload import save_recording_file, get_recording_by_call_id, get_recording_by_id
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
    db: Session = Depends(get_db)
):
    # Vérifier que l'appel existe
    call = get_call_by_id(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Appel non trouvé")
    
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
    recording = get_recording_by_id(db, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Enregistrement non trouvé")
    
    # Vérifier les permissions
    call = recording.call
    if (current_user["role"] == UserRole.COMMERCIAL and 
        call.commercial_id != current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    return recording

@router.get("/recordings/by-call/{call_id}")
def get_recording_by_call_id_route(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Récupérer l'enregistrement lié à l'appel
    recording = get_recording_by_call_id(db, call_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Aucun enregistrement trouvé pour cet appel")
    
    # Vérifier les permissions
    if (current_user["role"] == UserRole.COMMERCIAL and 
        recording.call.commercial_id != current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    return recording

@router.get("/recordings/by-call/{call_id}/play")
async def play_recording(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    print(f"Tentative de lecture de l'enregistrement pour l'appel {call_id} par l'utilisateur {current_user['sub']} (ID: {current_user['user_id']}, Rôle: {current_user['role']})")
    
    # Récupérer l'enregistrement lié à l'appel
    recording = get_recording_by_call_id(db, call_id)
    print(f"Enregistrement trouvé: {recording}")
    
    if not recording:
        print(f"Aucun enregistrement trouvé pour l'appel {call_id}")
        raise HTTPException(status_code=404, detail="Aucun enregistrement trouvé pour cet appel")
    
    # Vérifier si le fichier existe
    file_path = os.path.abspath(recording.file_path)
    print(f"Chemin du fichier: {file_path}")
    print(f"Le fichier existe-t-il ? {os.path.exists(file_path)}")
    
    if not os.path.exists(file_path):
        print(f"Le fichier {file_path} n'existe pas sur le disque")
        raise HTTPException(status_code=404, detail="Fichier d'enregistrement introuvable")
    
    # Vérifier les permissions
    print(f"Vérification des permissions: Rôle={current_user['role']}, Commercial ID={recording.call.commercial_id}, User ID={current_user['user_id']}")
    
    if current_user["role"] == UserRole.COMMERCIAL and recording.call.commercial_id != current_user["user_id"]:
        print("Accès refusé: L'utilisateur n'a pas les droits pour accéder à cet enregistrement")
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Lire le fichier audio et le renvoyer
    file_extension = os.path.splitext(recording.filename)[1].lower()
    media_type = f"audio/{file_extension[1:] if file_extension else 'mpeg'}"
    
    print(f"Envoi du fichier avec le type MIME: {media_type}")
    
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        
        return Response(content=content, media_type=media_type)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la lecture du fichier")

@router.get("/recordings/by-call/{call_id}/download")
async def download_recording(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Récupérer l'enregistrement lié à l'appel
    recording = get_recording_by_call_id(db, call_id)
    if not recording or not os.path.exists(recording.file_path):
        raise HTTPException(status_code=404, detail="Aucun enregistrement trouvé pour cet appel")
    
    # Vérifier les permissions
    if (current_user["role"] == UserRole.COMMERCIAL and 
        recording.call.commercial_id != current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Lire le fichier audio et le renvoyer en tant que pièce jointe
    file_extension = os.path.splitext(recording.filename)[1].lower()
    media_type = f"audio/{file_extension[1:] if file_extension else 'mpeg'}"
    
    with open(recording.file_path, "rb") as f:
        content = f.read()
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={recording.filename}",
            "Content-Type": "application/octet-stream"
        }
    )

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