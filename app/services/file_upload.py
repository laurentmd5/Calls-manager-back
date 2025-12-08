# app/services/file_upload.py
from sqlalchemy.orm import Session
import aiofiles
import os
import uuid
from datetime import datetime
from ..models.recording import Recording
from ..services.call_service import get_call_by_id
from config import settings

async def save_recording_file(db: Session, call_id: int, file) -> Recording:
    # Vérifier que l'appel existe
    call = get_call_by_id(db, call_id)
    if not call:
        raise ValueError("Appel non trouvé")
    
    # Générer un nom de fichier unique
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.RECORDINGS_DIR, unique_filename)
    
    # Sauvegarder le fichier
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # Créer l'enregistrement en base
    recording = Recording(
        filename=unique_filename,
        file_path=file_path,
        file_size=len(content),
        duration=call.duration,
        call_id=call_id
    )
    
    db.add(recording)
    db.commit()
    db.refresh(recording)
    
    return recording

def get_recording_by_id(db: Session, recording_id: int) -> Recording:
    return db.query(Recording).filter(Recording.id == recording_id).first()

def get_recording_by_call_id(db: Session, call_id: int) -> Recording:
    """Récupère un enregistrement par son ID d'appel"""
    return db.query(Recording).filter(Recording.call_id == call_id).first()

def delete_recording_file(db: Session, recording_id: int) -> bool:
    recording = get_recording_by_id(db, recording_id)
    if not recording:
        return False
    
    # Supprimer le fichier physique
    if os.path.exists(recording.file_path):
        os.remove(recording.file_path)
    
    # Supprimer l'enregistrement en base
    db.delete(recording)
    db.commit()
    return True