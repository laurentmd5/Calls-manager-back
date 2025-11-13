# NetSysVoice - Backend

Backend de l'application NetSysVoice pour la gestion des appels commerciaux.

## 📋 Prérequis

- Python 3.8+
- MySQL/MariaDB
- pip (gestionnaire de paquets Python)

## 🚀 Installation

1. **Cloner le dépôt** :
   ```bash
   git clone https://github.com/calebMoussoungou/netsyscall-backend.git
   cd netsyscall-backend
   ```

2. **Créer un environnement virtuel** :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Linux/Mac
   # OU
   .\venv\Scripts\activate  # Sur Windows
   ```

3. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

1. **Variables d'environnement** :
   Créez un fichier `.env` à la racine du projet avec :
   ```env
   DATABASE_URL=mysql+mysqlconnector://utilisateur:motdepasse@localhost/nom_de_la_base
   SECRET_KEY=votre_clé_secrète_ici
   ```

2. **Base de données** :
   - Créez une base de données MySQL/MariaDB
   - Mettez à jour `DATABASE_URL` dans le fichier `.env`

## 🛠 Commandes utiles

### Lancer l'application
```bash
uvicorn app.main:app --reload
```

### Gestion des migrations
```bash
# Créer une nouvelle migration
alembic revision --autogenerate -m "Description des modifications"

# Appliquer les migrations
alembic upgrade head

# Revenir à une version précédente
alembic downgrade -1
```

### Tests
```bash
# Lancer les tests
pytest
```

## 🌐 API Documentation

Une fois l'application démarrée, accédez à la documentation :

- **Swagger UI** : http://127.0.0.1:8000/docs
- **ReDoc** : http://127.0.0.1:8000/redoc

## 📚 Routes de l'API

### Authentification
- `POST /api/v1/auth/login` - Connexion utilisateur
- `POST /api/v1/auth/register` - Création de compte

### Utilisateurs
- `GET /api/v1/users/` - Liste des utilisateurs
- `GET /api/v1/users/{user_id}` - Détails d'un utilisateur
- `POST /api/v1/users/` - Créer un utilisateur
- `PUT /api/v1/users/{user_id}` - Mettre à jour un utilisateur

### Clients
- `GET /api/v1/clients/` - Liste des clients
- `POST /api/v1/clients/` - Créer un client
- `GET /api/v1/clients/{client_id}` - Détails d'un client

### Appels
- `GET /api/v1/calls/` - Liste des appels
- `POST /api/v1/calls/` - Créer un appel
- `GET /api/v1/calls/{call_id}` - Détails d'un appel

### Enregistrements
- `GET /api/v1/recordings/` - Liste des enregistrements
- `POST /api/v1/recordings/upload` - Téléverser un enregistrement
- `GET /api/v1/recordings/{recording_id}` - Télécharger un enregistrement

## 🧪 Tests

Pour exécuter les tests :

```bash
pytest
```

## 🛡️ Sécurité

- Authentification JWT
- Hachage des mots de passe avec bcrypt
- Protection CSRF
- Headers de sécurité HTTP

## 🤝 Contribution

1. Forkez le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Poussez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👨‍💻 Auteur

[Caleb Moussoungou](https://github.com/calebMoussoungou) - [@calebMoussoungou](https://twitter.com/calebMoussoungou)

---

<div align="center">
  <sub>Créé avec ❤️ par [Caleb Moussoungou](https://github.com/calebMoussoungou)</sub>
</div>
