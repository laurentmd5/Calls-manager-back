# app/services/client_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import aiofiles
import os
from ..models.client import Client
from ..models.user import User, UserRole
from ..schemas.client import ClientCreate, ClientUpdate

def create_client(db: Session, client_data: ClientCreate) -> Client:
    db_client = Client(**client_data.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def get_clients(db: Session, skip: int = 0, limit: int = 100) -> List[Client]:
    return db.query(Client).offset(skip).limit(limit).all()

def get_commercial_clients(db: Session, commercial_id: int, skip: int = 0, limit: int = 100) -> List[Client]:
    return db.query(Client).filter(
        Client.commercial_id == commercial_id
    ).offset(skip).limit(limit).all()

def get_client_by_id(db: Session, client_id: int) -> Optional[Client]:
    return db.query(Client).filter(Client.id == client_id).first()

def update_client(db: Session, client_id: int, client_data: ClientUpdate) -> Optional[Client]:
    client = get_client_by_id(db, client_id)
    if not client:
        return None
    
    update_data = client_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    return client

def delete_client(db: Session, client_id: int) -> bool:
    client = get_client_by_id(db, client_id)
    if not client:
        return False
    
    db.delete(client)
    db.commit()
    return True

async def import_clients_from_excel(db: Session, file) -> dict:
    # Lire le fichier Excel
    contents = await file.read()
    df = pd.read_excel(contents)
    
    # Valider les colonnes requises
    required_columns = ['first_name', 'last_name', 'phone_number']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Colonnes manquantes: {', '.join(missing_columns)}")
    
    # Récupérer les commerciaux actifs
    commercials = db.query(User).filter(
        User.role == UserRole.COMMERCIAL,
        User.is_active == True
    ).all()
    
    if not commercials:
        raise ValueError("Aucun commercial actif trouvé")
    
    clients_created = 0
    errors = []
    
    # Répartir équitablement entre les commerciaux
    commercial_index = 0
    
    for index, row in df.iterrows():
        try:
            client_data = {
                'first_name': str(row['first_name']),
                'last_name': str(row['last_name']),
                'phone_number': str(row['phone_number']),
                'company': str(row['company']) if 'company' in df.columns else None,
                'email': str(row['email']) if 'email' in df.columns else None,
                'address': str(row['address']) if 'address' in df.columns else None,
                'notes': str(row['notes']) if 'notes' in df.columns else None,
                'commercial_id': commercials[commercial_index].id
            }
            
            # Passer au commercial suivant
            commercial_index = (commercial_index + 1) % len(commercials)
            
            db_client = Client(**client_data)
            db.add(db_client)
            clients_created += 1
            
        except Exception as e:
            errors.append(f"Ligne {index + 2}: {str(e)}")
    
    db.commit()
    
    return {
        "message": f"Import terminé - {clients_created} clients créés",
        "clients_created": clients_created,
        "errors": errors
    }

def redistribute_clients(db: Session) -> dict:
    # Récupérer tous les clients sans commercial
    unassigned_clients = db.query(Client).filter(Client.commercial_id == None).all()
    
    # Récupérer les commerciaux actifs
    commercials = db.query(User).filter(
        User.role == UserRole.COMMERCIAL,
        User.is_active == True
    ).all()
    
    if not commercials:
        raise ValueError("Aucun commercial actif trouvé")
    
    # Répartir équitablement
    commercial_index = 0
    clients_assigned = 0
    
    for client in unassigned_clients:
        client.commercial_id = commercials[commercial_index].id
        commercial_index = (commercial_index + 1) % len(commercials)
        clients_assigned += 1
    
    db.commit()
    
    return {
        "message": f"Redistribution terminée - {clients_assigned} clients assignés",
        "clients_assigned": clients_assigned,
        "commercials_count": len(commercials)
    }