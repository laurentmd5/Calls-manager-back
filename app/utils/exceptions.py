# app/utils/exceptions.py
"""
Exceptions personnalisées pour l'API NetSysCall.
Utilisées pour uniformiser les réponses d'erreur HTTP.
"""

from fastapi import HTTPException, status


class ResourceNotFound(HTTPException):
    """Ressource non trouvée (404)"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class UnauthorizedAccess(HTTPException):
    """Accès non autorisé (403)"""
    def __init__(self, detail: str = "Accès non autorisé"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class InvalidFileFormat(HTTPException):
    """Format de fichier invalide (400)"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class UploadError(HTTPException):
    """Erreur lors de l'upload (500)"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class InternalServerError(HTTPException):
    """Erreur serveur interne (500)"""
    def __init__(self, detail: str = "Erreur serveur interne"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
