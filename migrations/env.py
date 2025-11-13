from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
from dotenv import load_dotenv

# Charge les variables d'environnement
load_dotenv()

# Import des modèles
from app.models.user import Base
from app.models.call import Call
from app.models.client import Client
from app.models.recording import Recording

# Configuration de la base de données
config = context.config
config.set_main_option('sqlalchemy.url', os.getenv('DATABASE_URL'))
target_metadata = Base.metadata

# Configuration du logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_online() -> None:
    # Récupère l'URL depuis les variables d'environnement
    database_url = os.getenv('DATABASE_URL')
    
    # Configure la connexion directement avec l'URL
    connectable = engine_from_config(
        {'sqlalchemy.url': database_url},
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()