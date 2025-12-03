# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from .database.connection import SessionLocal, create_tables
from .models.user import User, UserRole
from passlib.context import CryptContext
from datetime import datetime
from .routes import auth, users, clients, calls, recordings
from config import settings

def create_default_admin():
    """Crée un administrateur par défaut s'il n'existe pas."""
    # Configuration simplifiée de CryptContext pour éviter les problèmes de version
    pwd_context = CryptContext(
        schemes=["bcrypt"], 
        deprecated="auto",
        bcrypt__rounds=12  # Nombre de tours de hachage (plus c'est élevé, plus c'est sécurisé mais plus lent)
    )
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@netsysvoice.com").first()
        if not admin:
            admin = User(
                email="admin@netsysvoice.com",
                password_hash=pwd_context.hash("passer"),
                first_name="netsysvoice",
                last_name="admin",
                phone_number="",
                role=UserRole.ADMIN,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(admin)
            db.commit()
            print("✅ Administrateur par défaut créé avec succès")
    except Exception as e:
        print(f"⚠️  Erreur lors de la création de l'administrateur par défaut: {e}")
    finally:
        db.close()

# Create upload directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.RECORDINGS_DIR, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Backend pour l'application de gestion d'appels commerciaux"
)

# CORS Middleware Configuration
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=[
        "Content-Disposition",
        "Content-Length",
        "Content-Type",
    ],
    max_age=600,
)

# Static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/recordings", StaticFiles(directory="recordings"), name="recordings")

# Include routes
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(clients.router, prefix="/api/v1", tags=["Clients"])
app.include_router(calls.router, prefix="/api/v1", tags=["Calls"])
app.include_router(recordings.router, prefix="/api/v1", tags=["Recordings"])

@app.on_event("startup")
async def startup_event():
    create_tables()
    create_default_admin()  # Créer l'admin au démarrage

@app.get("/")
async def root():
    return {
        "message": f"Bienvenue sur {settings.APP_NAME}",
        "version": settings.VERSION
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}