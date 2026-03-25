# app/utils/file_validator.py
"""
Validateur pour les fichiers audio uploaidés par les appareils Samsung A06.
Accepte MIME types multiples + fallback sur extension du fichier.
"""

import os
from typing import Tuple

# MIME types acceptés pour les fichiers audio
ACCEPTED_AUDIO_MIMES = {
    'audio/mp4',                # Samsung A06 envoie .m4a avec ce type
    'audio/m4a',                # Standard pour M4A
    'audio/mpeg',               # MP3
    'audio/wav',                # WAV
    'audio/ogg',                # OGG Vorbis
    'audio/webm',               # WebM
    'audio/x-m4a',              # Variante M4A
    'application/octet-stream', # Fallback quand le client ne connaît pas le type
}

# Extensions acceptées (fallback quand MIME type est incorrect/manquant)
ACCEPTED_AUDIO_EXTENSIONS = {
    '.m4a', '.mp4', '.mp3', '.wav', '.ogg', '.webm'
}


def validate_audio_file(file) -> Tuple[bool, str]:
    """
    Valide un fichier audio avec vérification MIME type + extension.
    
    Stratégie de validation:
    1. Vérifier le MIME type (permissif)
    2. Si MIME type absent/incorrect, vérifier l'extension du fichier
    3. Accepter si au moins l'une des deux conditions est remplie
    
    Args:
        file: Objet UploadFile de FastAPI
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
        
    Examples:
        >>> validate_audio_file(file)  # .m4a de Samsung avec audio/mp4
        (True, "")
        
        >>> validate_audio_file(file)  # application/octet-stream
        (True, "")
        
        >>> validate_audio_file(file)  # .txt
        (False, "Format de fichier non supporté...")
    """
    
    # Vérification 1: MIME type
    mime_type = file.content_type.lower() if file.content_type else ""
    if mime_type in ACCEPTED_AUDIO_MIMES:
        return True, ""
    
    # Vérification 2: Extension du fichier (fallback)
    if file.filename:
        _, ext = os.path.splitext(file.filename.lower())
        if ext in ACCEPTED_AUDIO_EXTENSIONS:
            return True, ""
    
    # Rejet: ni MIME type ni extension valide
    return False, (
        f"Format de fichier audio non supporté. "
        f"Fichier reçu: {file.filename or 'sans_nom'} "
        f"(MIME: {mime_type or 'non_spécifié'}). "
        f"Formats acceptés: .m4a, .mp4, .mp3, .wav, .ogg, .webm"
    )


def get_audio_mime_type(filename: str, fallback: str = "audio/mpeg") -> str:
    """
    Détermine le MIME type approprié basé sur l'extension du fichier.
    Utilisé pour servir le fichier avec le bon Content-Type.
    
    Args:
        filename: Nom du fichier
        fallback: MIME type par défaut si extension non reconnue
        
    Returns:
        str: MIME type approprié
        
    Examples:
        >>> get_audio_mime_type("recording.m4a")
        'audio/mp4'
        
        >>> get_audio_mime_type("song.mp3")
        'audio/mpeg'
    """
    mime_map = {
        '.m4a': 'audio/mp4',
        '.mp4': 'audio/mp4',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.webm': 'audio/webm',
    }
    
    _, ext = os.path.splitext(filename.lower())
    return mime_map.get(ext, fallback)
