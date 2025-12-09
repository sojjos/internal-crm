#!/bin/bash

# =============================================================================
# Script d'installation complète - SME Management (Belgian)
# Pour Ubuntu 20.04/22.04 LTS sur serveur vierge
# =============================================================================

set -e

# Configuration
APP_DIR="/opt/sme-management"
DOMAIN="votre-domaine.com"  # Modifier selon votre domaine
GIT_REPO="https://github.com/sojjos/internal-crm.git"
GIT_BRANCH="claude/setup-admin-user-01BTRbCY7wK78UzRxAQmdg5B"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# 1. Mise à jour du système
# =============================================================================
echo_info "=== Mise à jour du système ==="
apt update && apt upgrade -y

# =============================================================================
# 2. Installation des dépendances système
# =============================================================================
echo_info "=== Installation des dépendances système ==="
apt install -y \
    curl \
    wget \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libpq-dev \
    postgresql \
    postgresql-contrib \
    supervisor \
    ufw

# =============================================================================
# 3. Installation de Node.js 20.x
# =============================================================================
echo_info "=== Installation de Node.js 20.x ==="
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
npm install -g npm@latest

echo_info "Node.js version: $(node -v)"
echo_info "NPM version: $(npm -v)"

# =============================================================================
# 4. Configuration de PostgreSQL
# =============================================================================
echo_info "=== Configuration de PostgreSQL ==="
systemctl start postgresql
systemctl enable postgresql

# Créer l'utilisateur et la base de données
sudo -u postgres psql <<EOF
CREATE USER smeadmin WITH PASSWORD 'VotreMotDePasseSecurise123!';
CREATE DATABASE sme_management OWNER smeadmin;
GRANT ALL PRIVILEGES ON DATABASE sme_management TO smeadmin;
EOF

echo_info "Base de données PostgreSQL créée"

# =============================================================================
# 5. Cloner le repository
# =============================================================================
echo_info "=== Clonage du repository ==="
if [ -d "$APP_DIR" ]; then
    echo_warn "Le répertoire $APP_DIR existe déjà. Suppression..."
    rm -rf "$APP_DIR"
fi

git clone "$GIT_REPO" "$APP_DIR"
cd "$APP_DIR"
git checkout "$GIT_BRANCH"

# =============================================================================
# 6. Configuration du Backend
# =============================================================================
echo_info "=== Configuration du Backend ==="
cd "$APP_DIR/backend"

# Créer l'environnement virtuel Python
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances Python
pip install --upgrade pip
pip install -r requirements.txt

# Créer le fichier .env
cat > .env <<EOF
# Database
DATABASE_URL=postgresql://smeadmin:VotreMotDePasseSecurise123!@localhost:5432/sme_management

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# App
APP_NAME="SME Management"
DEBUG=false
ENVIRONMENT=production

# Upload
UPLOAD_DIR=/opt/sme-management/uploads
MAX_UPLOAD_SIZE=10485760

# Email (configurer selon votre fournisseur)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre-email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe-app
SMTP_FROM=votre-email@gmail.com
EOF

# Créer les répertoires nécessaires
mkdir -p "$APP_DIR/uploads"
mkdir -p "$APP_DIR/uploads/invoices"
mkdir -p "$APP_DIR/uploads/documents"
mkdir -p "$APP_DIR/uploads/expenses"
mkdir -p "$APP_DIR/logs"

# Initialiser la base de données
echo_info "Initialisation de la base de données..."
python -c "from app.db.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"

# Créer l'utilisateur admin
echo_info "Création de l'utilisateur admin..."
python <<EOF
from app.db.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()

# Vérifier si admin existe déjà
existing = db.query(User).filter(User.email == "admin@sme.be").first()
if existing:
    print("Utilisateur admin existe déjà, mise à jour du mot de passe...")
    existing.hashed_password = get_password_hash("admin")
    existing.is_active = True
    existing.is_superuser = True
else:
    print("Création de l'utilisateur admin...")
    admin = User(
        email="admin@sme.be",
        username="admin",
        hashed_password=get_password_hash("admin"),
        first_name="Admin",
        last_name="System",
        is_active=True,
        is_superuser=True
    )
    db.add(admin)

db.commit()
db.close()
print("Utilisateur admin créé/mis à jour avec succès!")
print("Email: admin@sme.be")
print("Mot de passe: admin")
EOF

deactivate

# =============================================================================
# 7. Configuration du Frontend
# =============================================================================
echo_info "=== Configuration du Frontend ==="
cd "$APP_DIR/frontend"

# Créer le fichier .env
cat > .env <<EOF
VITE_API_URL=https://${DOMAIN}/api
EOF

# Installer les dépendances et construire
npm install
npm run build

# =============================================================================
# 8. Configuration de Supervisor pour le Backend
# =============================================================================
echo_info "=== Configuration de Supervisor ==="
cat > /etc/supervisor/conf.d/sme-backend.conf <<EOF
[program:sme-backend]
command=$APP_DIR/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
directory=$APP_DIR/backend
user=root
autostart=true
autorestart=true
stderr_logfile=$APP_DIR/logs/backend.err.log
stdout_logfile=$APP_DIR/logs/backend.out.log
environment=PATH="$APP_DIR/backend/venv/bin"
EOF

supervisorctl reread
supervisorctl update
supervisorctl start sme-backend

# =============================================================================
# 9. Configuration de Nginx
# =============================================================================
echo_info "=== Configuration de Nginx ==="
cat > /etc/nginx/sites-available/sme-management <<EOF
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};

    # Redirection vers HTTPS (décommenter après certbot)
    # return 301 https://\$server_name\$request_uri;

    # Frontend
    root $APP_DIR/frontend/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # API Backend
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        client_max_body_size 10M;
    }

    # Fichiers statiques uploadés
    location /uploads {
        alias $APP_DIR/uploads;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Frontend SPA routing
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Cache pour les assets statiques
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Activer le site
ln -sf /etc/nginx/sites-available/sme-management /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Tester et recharger Nginx
nginx -t
systemctl reload nginx

# =============================================================================
# 10. Configuration du Firewall
# =============================================================================
echo_info "=== Configuration du Firewall ==="
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# =============================================================================
# 11. Permissions
# =============================================================================
echo_info "=== Configuration des permissions ==="
chown -R www-data:www-data "$APP_DIR/uploads"
chmod -R 755 "$APP_DIR/uploads"

# =============================================================================
# 12. Installation SSL avec Certbot (optionnel)
# =============================================================================
echo_info "=== Configuration SSL ==="
echo_warn "Pour activer HTTPS, exécutez:"
echo_warn "  certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"

# =============================================================================
# Résumé
# =============================================================================
echo ""
echo "=============================================="
echo -e "${GREEN}Installation terminée avec succès!${NC}"
echo "=============================================="
echo ""
echo "Informations de connexion:"
echo "  URL: http://${DOMAIN} (ou IP du serveur)"
echo "  Email: admin@sme.be"
echo "  Mot de passe: admin"
echo ""
echo "Commandes utiles:"
echo "  Redémarrer le backend: supervisorctl restart sme-backend"
echo "  Logs backend: tail -f $APP_DIR/logs/backend.out.log"
echo "  Status: supervisorctl status"
echo ""
echo "IMPORTANT: Changez le mot de passe admin après la première connexion!"
echo ""
echo "Pour activer HTTPS:"
echo "  certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
echo ""
