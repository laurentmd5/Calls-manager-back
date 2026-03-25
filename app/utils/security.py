# app/utils/security.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from config import settings
import os
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

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
    """
    Vérifie et décode un token JWT.
    
    Args:
        token: Le token JWT à vérifier (peut inclure le préfixe 'Bearer ')
        
    Returns:
        dict: Le payload décodé si le token est valide, None sinon
    """
    if not token:
        logger.debug("Aucun token fourni")
        return None
        
    try:
        # Nettoyer le token au cas où il contiendrait le préfixe 'Bearer '
        if isinstance(token, str) and token.startswith('Bearer '):
            token = token[7:].strip()
            
        if not token:
            logger.debug("Token vide après nettoyage")
            return None
        
        # Décoder le token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={
                "verify_exp": True,  # Vérifier l'expiration
                "require": ["exp", "sub", "user_id", "role"]  # Champs obligatoires
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
    """
    Vérifie qu'un chemin de fichier est sécurisé.
    Prévient les attaques par traversal de répertoire (path traversal).
    
    Sécurité:
    - Le chemin doit être dans le répertoire recordings/
    - Pas de traversal de répertoire (..)
    - Chemin absolu doit commencer par recordings_dir
    
    Args:
        file_path: Chemin du fichier à valider
        
    Returns:
        bool: True si le chemin est sûr
        
    Raises:
        ValueError: Si le chemin est en dehors de recordings/ ou n'existe pas
    """
    
    # Résoudre les chemins en absolu (élimine .., symlinks, etc)
    abs_path = os.path.abspath(file_path)
    recordings_dir = os.path.abspath(settings.RECORDINGS_DIR)
    
    # Vérifier que le chemin est bien dans recordings/
    # Important: vérifier que abs_path commence par recordings_dir + le séparateur
    if not abs_path.startswith(recordings_dir + os.sep) and abs_path != recordings_dir:
        logger.error(f"Tentative accès en dehors recordings: {abs_path}")
        raise ValueError(f"Accès refusé: chemin en dehors de {recordings_dir}")
    
    # Vérifier l'existence
    if not os.path.exists(abs_path):
        logger.warning(f"Fichier non trouvé: {abs_path}")
        raise ValueError(f"Fichier non trouvé: {abs_path}")
    
    return True


def safe_file_path(file_path: str) -> str:
    """
    Retourne le chemin sécurisé d'un fichier ou lève une exception.
    À utiliser avant chaque accès de fichier pour éviter les traversals.
    
    Args:
        file_path: Chemin à valider
        
    Returns:
        str: Chemin absolu sécurisé
        
    Raises:
        ValueError: Si le chemin est invalide ou en dehors de recordings/
        
    Examples:
        >>> safe_path = safe_file_path("recordings/550e8400.m4a")
        >>> with open(safe_path, "rb") as f:
        ...     content = f.read()
    """
    validate_file_path(file_path)
    return os.path.abspath(file_path)

def has_permission(user, required_permissions):
    """
    Vérifie si un utilisateur a les permissions requises.
    
    Args:
        user: L'utilisateur (doit avoir un attribut 'role')
        required_permissions: Liste des permissions requises (ex: ['read:performance'])
        
    Returns:
        bool: True si l'utilisateur a toutes les permissions requises, False sinon
    """
    if not user or not hasattr(user, 'role'):
        return False
        
    # Les permissions par rôle
    role_permissions = {
        'admin': [
            'read:performance',
            'write:performance',
            'read:users',
            'write:users',
            'read:clients',
            'write:clients',
            'read:calls',
            'write:calls',
            'read:recordings',
            'write:recordings'
        ],
        'manager': [
            'read:performance',
            'read:users',
            'read:clients',
            'write:clients',
            'read:calls',
            'write:calls',
            'read:recordings'
        ],
        'commercial': [
            'read:performance:own',
            'read:clients:own',
            'read:calls:own',
            'read:recordings:own'
        ]
    }
    
    # Vérifier si l'utilisateur a un rôle valide
    if user.role not in role_permissions:
        return False
        
    # Vérifier si l'utilisateur a toutes les permissions requises
    user_permissions = role_permissions.get(user.role, [])
    
    # Pour les commerciaux, vérifier les permissions spécifiques
    if user.role == 'commercial':
        # Si l'utilisateur demande une permission spécifique, vérifier s'il a accès
        for perm in required_permissions:
            if perm not in user_permissions and not perm.startswith('read:performance:own'):
                return False
        return True
    
    # Pour les autres rôles, vérifier les permissions normales
    return all(perm in user_permissions for perm in required_permissions)