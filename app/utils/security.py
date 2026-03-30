# app/utils/security.py
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from config import settings
import os
import logging

logger = logging.getLogger(__name__)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du mot de passe: {e}")
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str = None) -> Optional[dict]:
    if not token:
        logger.debug("Aucun token fourni")
        return None
        
    try:
        if isinstance(token, str) and token.startswith('Bearer '):
            token = token[7:].strip()
            
        if not token:
            logger.debug("Token vide après nettoyage")
            return None
        
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={
                "verify_exp": True,
                "require": ["exp", "sub", "user_id", "role"]
            }
        )
        
        logger.debug(f"Token décodé avec succès pour l'utilisateur: {payload.get('sub')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Le token a expiré")
        return None
    except jwt.JWTClaimsError as e:
        logger.warning(f"Erreur de revendications du token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors du décodage du token: {str(e)}", exc_info=True)
        return None


def validate_file_path(file_path: str) -> bool:
    abs_path = os.path.abspath(file_path)
    recordings_dir = os.path.abspath(settings.RECORDINGS_DIR)
    
    if not abs_path.startswith(recordings_dir + os.sep) and abs_path != recordings_dir:
        logger.error(f"Tentative accès en dehors recordings: {abs_path}")
        raise ValueError(f"Accès refusé: chemin en dehors de {recordings_dir}")
    
    if not os.path.exists(abs_path):
        logger.warning(f"Fichier non trouvé: {abs_path}")
        raise ValueError(f"Fichier non trouvé: {abs_path}")
    
    return True


def safe_file_path(file_path: str) -> str:
    validate_file_path(file_path)
    return os.path.abspath(file_path)

def has_permission(user, required_permissions):
    if not user or not hasattr(user, 'role'):
        return False
        
    role_permissions = {
        'admin': [
            'read:performance', 'write:performance',
            'read:users', 'write:users',
            'read:clients', 'write:clients',
            'read:calls', 'write:calls',
            'read:recordings', 'write:recordings'
        ],
        'manager': [
            'read:performance', 'read:users',
            'read:clients', 'write:clients',
            'read:calls', 'write:calls',
            'read:recordings'
        ],
        'commercial': [
            'read:performance:own',
            'read:clients:own',
            'read:calls:own',
            'read:recordings:own'
        ]
    }
    
    if user.role not in role_permissions:
        return False
        
    user_permissions = role_permissions.get(user.role, [])
    
    if user.role == 'commercial':
        for perm in required_permissions:
            if perm not in user_permissions and not perm.startswith('read:performance:own'):
                return False
        return True
    
    return all(perm in user_permissions for perm in required_permissions)
