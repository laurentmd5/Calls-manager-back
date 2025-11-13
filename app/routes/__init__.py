# app/routes/__init__.py
from .auth import router as auth_router
from .users import router as users_router
from .clients import router as clients_router
from .calls import router as calls_router
from .recordings import router as recordings_router

__all__ = ["auth_router", "users_router", "clients_router", "calls_router", "recordings_router"]