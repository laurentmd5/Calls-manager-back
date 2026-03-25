# app/utils/logging_config.py
"""
Configuration centralisée du système de logging structuré.
Logs vers fichier + console avec niveaux appropriés.
"""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logger(app_name: str = "netsyscall") -> logging.Logger:
    """
    Configure le système de logging structuré avec rotation des fichiers.
    
    Architecture:
    - logs/netsyscall.log: Tous les logs INFO+
    - logs/netsyscall_errors.log: Logs ERROR+ uniquement  
    - Console: Tous les logs DEBUG+
    
    Args:
        app_name: Nom de l'application pour le logger
        
    Returns:
        logging.Logger: Logger configuré et prêt à l'emploi
    """
    
    # Créer le dossier logs s'il n'existe pas
    os.makedirs("logs", exist_ok=True)
    
    # Logger principal
    logger = logging.getLogger(app_name)
    
    # Ne pas ajouter les handlers deux fois (check pour éviter les doublons)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Format structuré: timestamp | logger name | level | [file:line] | message
    formatter = logging.Formatter(
        '%(asctime)s | %(name)-20s | %(levelname)-8s | [%(filename)s:%(lineno)d] | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # ========== Handler Fichier Principal (INFO+) ==========
    file_handler = logging.handlers.RotatingFileHandler(
        "logs/netsyscall.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # ========== Handler Console (DEBUG+) ==========
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ========== Handler Fichier Erreurs (ERROR+) ==========
    error_handler = logging.handlers.RotatingFileHandler(
        "logs/netsyscall_errors.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


# Instance globale du logger (importée par d'autres modules)
logger = setup_logger()
