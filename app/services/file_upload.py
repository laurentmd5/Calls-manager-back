# app/services/file_upload.py
from sqlalchemy.orm import Session
import aiofiles
import os
import uuid
import logging
from datetime import datetime
from ..models.recording import Recording
from ..services.call_service import get_call_by_id
from config import settings

logger = logging.getLogger(__name__)


async def save_recording_file(db: Session, call_id: int, file) -> Recording:
    """
    Sauvegarde un fichier d'enregistrement audio sur le disque.
    
    Processus:
    1. Vérifier que l'appel existe
    2. Générer un UUID pour le nom du fichier (évite collisions)
    3. Sauvegarder le fichier en binaire
    4. Créer l'enregistrement en base de données
    
    Args:
        db: Session SQLAlchemy
        call_id: ID de l'appel parent
        file: Objet UploadFile de FastAPI
        
    Returns:
        Recording: Objet enregistrement créé
        
    Raises:
        ValueError: Si l'appel n'existe pas
        IOError: Si erreur d'écriture disque
    """
    
    logger.info(
        f"Début upload pour appel {call_id}: {file.filename} "
        f"(size={file.size or '?'} bytes, MIME: {file.content_type or 'non_spécifié'})"
    )
    
    # Vérifier que l'appel existe
    call = get_call_by_id(db, call_id)
    if not call:
        logger.error(f"Appel {call_id} non trouvé - upload rejeté")
        raise ValueError(f"Appel {call_id} non trouvé")
    
    # Générer un nom de fichier unique avec UUID
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.RECORDINGS_DIR, unique_filename)
    
    logger.debug(f"Nom généré: {unique_filename}, chemin: {file_path}")
    
    try:
        # Sauvegarder le fichier
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        file_size = len(content)
        logger.info(f"✅ Fichier sauvegardé: {unique_filename} ({file_size} bytes)")
        
        # Créer l'enregistrement en base
        recording = Recording(
            filename=unique_filename,
            file_path=file_path,
            file_size=file_size,
            duration=call.duration,
            call_id=call_id
        )
        
        db.add(recording)
        db.commit()
        db.refresh(recording)
        
        logger.info(f"✅ Enregistrement créé en BD: ID={recording.id}")
        return recording
        
    except IOError as e:
        logger.error(f"❌ Erreur I/O lors de la sauvegarde: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"❌ Erreur inattendue lors de l'upload: {str(e)}", exc_info=True)
        raise


def get_recording_by_id(db: Session, recording_id: int) -> Recording:
    """Récupère un enregistrement par son ID."""
    return db.query(Recording).filter(Recording.id == recording_id).first()


def get_recording_by_call_id(db: Session, call_id: int) -> Recording:
    """Récupère un enregistrement par son ID d'appel."""
    return db.query(Recording).filter(Recording.call_id == call_id).first()


def delete_recording_file(db: Session, recording_id: int) -> bool:
    """
    Supprime un enregistrement (fichier + BD).
    
    Processus:
    1. Récupérer l'enregistrement
    2. Supprimer le fichier physique (si exists)
    3. Supprimer l'enregistrement en base de données
    
    Args:
        db: Session SQLAlchemy
        recording_id: ID de l'enregistrement à supprimer
        
    Returns:
        bool: True si succès, False sinon
    """
    
    logger.info(f"Suppression enregistrement {recording_id}")
    
    recording = get_recording_by_id(db, recording_id)
    if not recording:
        logger.warning(f"Enregistrement {recording_id} non trouvé")
        return False
    
    try:
        # Supprimer le fichier physique
        if os.path.exists(recording.file_path):
            os.remove(recording.file_path)
            logger.info(f"✅ Fichier supprimé: {recording.file_path}")
        else:
            logger.warning(f"Fichier physique non trouvé: {recording.file_path}")
        
        # Supprimer l'enregistrement en base
        db.delete(recording)
        db.commit()
        
        logger.info(f"✅ Enregistrement {recording_id} supprimé en BD")
        return True
        
    except OSError as e:
        logger.error(f"❌ Erreur suppression fichier: {str(e)}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"❌ Erreur suppression BD: {str(e)}", exc_info=True)
        return False

    if not recording:
        return False
    
    # Supprimer le fichier physique
    if os.path.exists(recording.file_path):
        os.remove(recording.file_path)
    
    # Supprimer l'enregistrement en base
    db.delete(recording)
    db.commit()
    return True