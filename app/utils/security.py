# app/utils/security.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from config import settings

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
        print("Aucun token fourni")
        return None
        
    try:
        # Nettoyer le token au cas où il contiendrait le préfixe 'Bearer '
        if isinstance(token, str) and token.startswith('Bearer '):
            token = token[7:].strip()
            
        if not token:
            print("Token vide après nettoyage")
            return None
            
        print(f"Tentative de décodage du token: {token[:20]}...")
        print(f"Algorithme: {settings.ALGORITHM}")
        
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
        
        print(f"Token décodé avec succès pour l'utilisateur: {payload.get('sub')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        print("Erreur: Le token a expiré")
        return None
    except jwt.JWTClaimsError as e:
        print(f"Erreur de revendications du token: {str(e)}")
        return None
    except Exception as e:
        print(f"Erreur inattendue lors du décodage du token: {str(e)}")
        return None

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