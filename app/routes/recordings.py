# app/routes/recordings.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from sqlalchemy.orm import Session
from typing import List
import os
import logging

from ..database.connection import get_db
from ..schemas.recording import RecordingResponse, RecordingCreate
from ..services.call_service import get_call_by_id
from ..services.file_upload import save_recording_file, get_recording_by_call_id, get_recording_by_id
from ..utils.security import verify_token, safe_file_path
from ..utils.file_validator import validate_audio_file, get_audio_mime_type
from ..utils.exceptions import ResourceNotFound, UnauthorizedAccess, InvalidFileFormat, UploadError
from ..models.user import UserRole
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def get_current_user(token: str = Depends(verify_token)):
    """Extrait l'utilisateur courant du token JWT."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )
    return token


def check_recording_access(db: Session, recording, current_user: dict) -> bool:
    """
    Vérifie si l'utilisateur a accès à cet enregistrement.
    
    Règles:
    - COMMERCIAL: accès à ses appels uniquement
    - MANAGER: accès à tous (comme admin)
    - ADMIN: accès à tous
    
    Args:
        db: Session base de données
        recording: Objet Recording
        current_user: Dict utilisateur du token
        
    Returns:
        bool: True si accès autorisé
    """
    if current_user["role"] in [UserRole.ADMIN, UserRole.MANAGER]:
        return True
    
    if current_user["role"] == UserRole.COMMERCIAL:
        return recording.call.commercial_id == current_user["user_id"]
    
    return False


@router.post(
    "/recordings",
    response_model=RecordingResponse,
    summary="Upload un enregistrement d'appel",
    tags=["Recordings"]
)
async def upload_recording(
    call_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload un fichier audio (m4a, mp3, wav...) pour un appel donné.
    
    **Formats acceptés:**
    - audio/mp4 (.m4a, .mp4) - Samsung A06
    - audio/mpeg (.mp3)
    - audio/wav (.wav)
    - audio/ogg (.ogg)
    - application/octet-stream (fallback)
    
    **Processus:**
    1. Validation du format (MIME type + extension)
    2. Génération UUID unique pour le nom de stockage
    3. Sauvegarde dans `/recordings/[UUID].m4a`
    4. Création de l'enregistrement en base de données
    """
    logger.info(f"Upload fichier pour appel {call_id}: {file.filename} (MIME: {file.content_type})")
    
    # Vérifier que l'appel existe
    call = get_call_by_id(db, call_id)
    if not call:
        logger.warning(f"Appel {call_id} non trouvé - upload rejeté")
        raise ResourceNotFound(f"Appel {call_id} non trouvé")
    
    # Vérifier le format du fichier (avec validation améliorée)
    is_valid, error_msg = validate_audio_file(file)
    if not is_valid:
        logger.warning(f"Fichier rejeté: {error_msg}")
        raise InvalidFileFormat(error_msg)
    
    try:
        logger.debug(f"Sauvegarde du fichier {file.filename} pour appel {call_id}")
        recording = await save_recording_file(db, call_id, file)
        logger.info(f"✅ Enregistrement créé: ID={recording.id}, chemin={recording.file_path}")
        return recording
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'upload: {str(e)}", exc_info=True)
        raise UploadError(f"Erreur lors de l'upload: {str(e)}")


@router.get(
    "/recordings/{recording_id}",
    response_model=RecordingResponse,
    summary="Récupérer les infos d'un enregistrement",
    tags=["Recordings"]
)
def get_recording_info(
    recording_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupère les infos d'un enregistrement spécifique."""
    recording = get_recording_by_id(db, recording_id)
    if not recording:
        logger.warning(f"Enregistrement {recording_id} non trouvé")
        raise ResourceNotFound(f"Enregistrement {recording_id} non trouvé")
    
    # Vérifier les permissions
    if not check_recording_access(db, recording, current_user):
        logger.warning(
            f"Accès refusé: {current_user['role']} {current_user['user_id']} "
            f"tente d'accéder enregistrement {recording_id}"
        )
        raise UnauthorizedAccess("Vous n'avez pas accès à cet enregistrement")
    
    return recording


@router.get(
    "/recordings/by-call/{call_id}",
    response_model=RecordingResponse,
    summary="Récupérer l'enregistrement d'un appel",
    tags=["Recordings"]
)
def get_recording_by_call_id_route(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupère l'enregistrement lié à un appel spécifique."""
    recording = get_recording_by_call_id(db, call_id)
    if not recording:
        logger.warning(f"Aucun enregistrement trouvé pour appel {call_id}")
        raise ResourceNotFound(f"Aucun enregistrement trouvé pour appel {call_id}")
    
    # Vérifier les permissions
    if not check_recording_access(db, recording, current_user):
        logger.warning(
            f"Accès refusé: {current_user['role']} {current_user['user_id']} "
            f"tente d'accéder appel {call_id}"
        )
        raise UnauthorizedAccess("Vous n'avez pas accès à cet enregistrement")
    
    return recording


@router.get(
    "/recordings/by-call/{call_id}/play",
    summary="Lire un enregistrement en streaming",
    tags=["Recordings"]
)
async def play_recording(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Récupère et lit l'enregistrement audio d'un appel en streaming.
    
    **Permissions:**
    - COMMERCIAL: peut lire ses propres appels
    - MANAGER: peut lire tous les appels
    - ADMIN: accès à tous
    """
    logger.info(
        f"Lecture appel {call_id} par {current_user['sub']} "
        f"(ID: {current_user['user_id']}, Rôle: {current_user['role']})"
    )
    
    # Récupérer l'enregistrement lié à l'appel
    recording = get_recording_by_call_id(db, call_id)
    
    if not recording:
        logger.warning(f"Aucun enregistrement trouvé pour appel {call_id}")
        raise ResourceNotFound(f"Aucun enregistrement trouvé pour appel {call_id}")
    
    # Vérifier les permissions
    if not check_recording_access(db, recording, current_user):
        logger.warning(
            f"Accès refusé: {current_user['role']} {current_user['user_id']} "
            f"tente de lire appel {call_id}"
        )
        raise UnauthorizedAccess("Vous n'avez pas accès à cet enregistrement")
    
    # Valider et récupérer le chemin du fichier (prévient path traversal)
    try:
        file_path = safe_file_path(recording.file_path)
    except ValueError as e:
        logger.error(f"❌ Tentative accès fichier invalide: {str(e)}")
        raise ResourceNotFound("Fichier d'enregistrement introuvable")
    
    # Déterminer le MIME type basé sur l'extension
    media_type = get_audio_mime_type(recording.filename)
    
    logger.info(f"Envoi du fichier {recording.filename} (MIME: {media_type})")
    
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        
        return Response(content=content, media_type=media_type)
    except IOError as e:
        logger.error(f"❌ Erreur lecture fichier: {str(e)}", exc_info=True)
        raise UploadError("Erreur lors de la lecture du fichier")


@router.get(
    "/recordings/by-call/{call_id}/download",
    summary="Télécharger un enregistrement",
    tags=["Recordings"]
)
async def download_recording(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Télécharge un enregistrement audio en tant que pièce jointe.
    
    **Permissions:**
    - COMMERCIAL: peut télécharger ses propres appels
    - MANAGER: peut télécharger tous les appels
    - ADMIN: accès à tous
    """
    recording = get_recording_by_call_id(db, call_id)
    if not recording:
        logger.warning(f"Enregistrement non trouvé pour appel {call_id}")
        raise ResourceNotFound(f"Enregistrement non trouvé pour appel {call_id}")
    
    # Vérifier les permissions
    if not check_recording_access(db, recording, current_user):
        logger.warning(
            f"Accès refusé: {current_user['role']} {current_user['user_id']} "
            f"tente de télécharger appel {call_id}"
        )
        raise UnauthorizedAccess("Vous n'avez pas accès à cet enregistrement")
    
    # Valider et récupérer le chemin du fichier
    try:
        file_path = safe_file_path(recording.file_path)
    except ValueError as e:
        logger.error(f"❌ Tentative accès fichier invalide: {str(e)}")
        raise ResourceNotFound("Fichier d'enregistrement introuvable")
    
    media_type = get_audio_mime_type(recording.filename)
    
    logger.info(f"Téléchargement fichier {recording.filename}")
    
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={recording.filename}",
                "Content-Type": "application/octet-stream"
            }
        )
    except IOError as e:
        logger.error(f"❌ Erreur téléchargement fichier: {str(e)}", exc_info=True)
        raise UploadError("Erreur lors du téléchargement du fichier")


@router.delete(
    "/recordings/{recording_id}",
    summary="Supprimer un enregistrement",
    tags=["Recordings"]
)
def delete_recording(
    recording_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Supprime un enregistrement (admin uniquement).
    
    **Permissions:**
    - ADMIN: autorisé
    - Autres: accès refusé
    """
    from ..services.file_upload import delete_recording_file
    
    recording = get_recording_by_id(db, recording_id)
    if not recording:
        logger.warning(f"Enregistrement {recording_id} non trouvé")
        raise ResourceNotFound(f"Enregistrement {recording_id} non trouvé")
    
    # Vérifier les permissions (admin seulement)
    if current_user["role"] != UserRole.ADMIN:
        logger.warning(
            f"Tentative suppression par non-admin: "
            f"{current_user['role']} {current_user['user_id']}"
        )
        raise UnauthorizedAccess("Seul un administrateur peut supprimer des enregistrements")
    
    try:
        delete_recording_file(db, recording_id)
        logger.info(f"✅ Enregistrement {recording_id} supprimé")
        return {"message": "Enregistrement supprimé avec succès"}
    except Exception as e:
        logger.error(f"❌ Erreur suppression enregistrement: {str(e)}", exc_info=True)
        raise UploadError(f"Erreur lors de la suppression: {str(e)}")
