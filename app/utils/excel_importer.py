# app/utils/excel_importer.py
import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models.client import Client
from ..models.user import User, UserRole

def validate_excel_columns(df: pd.DataFrame) -> List[str]:
    """Valide les colonnes requises dans le fichier Excel"""
    required_columns = ['first_name', 'last_name', 'phone_number']
    missing_columns = [col for col in required_columns if col not in df.columns]
    return missing_columns

def parse_excel_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Parse les données Excel en liste de dictionnaires"""
    clients_data = []
    
    for _, row in df.iterrows():
        client_data = {
            'first_name': str(row['first_name']).strip(),
            'last_name': str(row['last_name']).strip(),
            'phone_number': str(row['phone_number']).strip(),
            'company': str(row['company']).strip() if 'company' in df.columns and pd.notna(row['company']) else None,
            'email': str(row['email']).strip() if 'email' in df.columns and pd.notna(row['email']) else None,
            'address': str(row['address']).strip() if 'address' in df.columns and pd.notna(row['address']) else None,
            'notes': str(row['notes']).strip() if 'notes' in df.columns and pd.notna(row['notes']) else None,
        }
        clients_data.append(client_data)
    
    return clients_data

def assign_clients_to_commercials(db: Session, clients_data: List[Dict[str, Any]]) -> List[Client]:
    """Répartit les clients entre les commerciaux de manière équitable"""
    commercials = db.query(User).filter(
        User.role == UserRole.COMMERCIAL,
        User.is_active == True
    ).all()
    
    if not commercials:
        raise ValueError("Aucun commercial actif trouvé")
    
    clients = []
    commercial_index = 0
    
    for client_data in clients_data:
        # Assigner au commercial suivant
        commercial_id = commercials[commercial_index].id
        client_data['commercial_id'] = commercial_id
        
        client = Client(**client_data)
        clients.append(client)
        
        # Passer au commercial suivant
        commercial_index = (commercial_index + 1) % len(commercials)
    
    return clients