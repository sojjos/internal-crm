# SME Management - Application de Gestion PME

Application web complète de gestion pour PME, incluant :
- Gestion des factures et articles/services
- Gestion de la TVA et comptabilité (exports pour le comptable)
- Gestion des notes de frais
- Gestion simplifiée des collaborateurs et de la paie
- Intégration PayPal et e-facturation belge (Peppol)
- Module d'installation automatisée sur serveur Linux

## Fonctionnalités principales

### Facturation
- Création et gestion de factures
- Génération automatique de PDF
- Envoi par email
- Support e-facturation Peppol/UBL
- Suivi des paiements
- Intégration PayPal

### Catalogue Articles/Services
- Types : Service, Produit, Frais
- Modes de facturation : Heure, Jour, Unité, Km, Forfait
- Gestion des taux TVA

### Notes de frais
- Encodage des dépenses par collaborateur
- Association aux périodes de paie
- Justificatifs (upload)
- Validation et remboursement

### RH & Paie simplifiée
- Fiche collaborateur
- Types de contrat : CDI, CDD, Freelance, Contrat gérant
- Récapitulatif par période de paie
- Export Excel pour le secrétariat social

### Reporting
- Tableau de bord avec indicateurs clés
- CA par mois
- TVA collectée/déductible
- Exports comptables (ventes, achats, TVA)

## Stack technique

### Backend
- Python 3.10+
- FastAPI
- SQLAlchemy + Alembic
- PostgreSQL
- WeasyPrint (PDF)
- lxml (UBL/Peppol)

### Frontend
- React 18 + Vite
- TypeScript
- TailwindCSS
- React Router
- React Hook Form

## Installation

### Prérequis
- Serveur Linux (Debian/Ubuntu ou RHEL/CentOS)
- Accès root

### Installation automatique

```bash
sudo ./install.sh
```

Le script d'installation :
1. Installe les dépendances système
2. Configure PostgreSQL
3. Installe le backend Python
4. Compile le frontend React
5. Configure Nginx comme reverse proxy
6. Crée les services systemd
7. Lance l'assistant de configuration initiale

### Mise à jour

```bash
sudo ./install.sh --update
```

## Développement local

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec vos paramètres

# Lancer le serveur
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Configuration

Après l'installation, configurez via l'interface web :
- Informations société
- Logo
- Taux TVA
- Paramètres Peppol
- Paramètres PayPal
- Configuration SMTP

## Structure du projet

```
.
├── backend/
│   ├── app/
│   │   ├── api/           # Routes API
│   │   ├── core/          # Config, sécurité
│   │   ├── db/            # Base de données
│   │   ├── models/        # Modèles SQLAlchemy
│   │   ├── schemas/       # Schémas Pydantic
│   │   ├── services/      # Services (PDF, email, Peppol)
│   │   └── templates/     # Templates HTML
│   └── migrations/        # Migrations Alembic
├── frontend/
│   └── src/
│       ├── components/    # Composants React
│       ├── context/       # Contextes (Auth)
│       ├── pages/         # Pages
│       └── services/      # API client
└── install.sh            # Script d'installation
```

## API Documentation

Une fois le serveur lancé, la documentation API est disponible :
- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`

## Licence

Propriétaire - Tous droits réservés
