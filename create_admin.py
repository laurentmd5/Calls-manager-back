#!/usr/bin/env python3
# create_admin.py
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent))

from app.database.connection import SessionLocal
from app.models.user import User, UserRole
from passlib.context import CryptContext
from datetime import datetime

def create_admin():
    """Crée un administrateur par défaut si il n'existe pas déjà."""
    # Initialisation du hachage de mot de passe
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    db = SessionLocal()
    try:
        # Vérifier si l'admin existe déjà
        admin = db.query(User).filter(User.email == "admin@netsysvoice.com").first()
        if admin:
            print("⚠️  L'administrateur existe déjà.")
            return

        # Créer le nouvel admin
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
        print("✅ Administrateur créé avec succès !")
        print("\n🔑 Informations de connexion :")
        print(f"   Email: admin@netsysvoice.com")
        print(f"   Mot de passe: passer")
        print("\n⚠️  IMPORTANT : Changez ce mot de passe après la première connexion !")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de la création de l'administrateur : {e}")
        print("Vérifiez que la base de données est bien configurée et accessible.")
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🔄 Création de l'administrateur par défaut...")
    create_admin()
