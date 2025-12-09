#!/bin/bash

# =============================================================================
# Script d'installation complète - SME Management (Belgian)
# Pour Ubuntu 20.04/22.04 LTS sur serveur vierge
# Usage: ./install-server.sh [IP_OU_DOMAINE]
# Exemple: ./install-server.sh 109.199.101.5
# =============================================================================

set -e

# Configuration
APP_DIR="/opt/sme-management"
DOMAIN="${1:-109.199.101.5}"  # Premier argument ou IP par défaut
GIT_REPO="https://github.com/sojjos/internal-crm.git"
GIT_BRANCH="claude/setup-admin-user-01BTRbCY7wK78UzRxAQmdg5B"
DB_PASSWORD="SmeSecure2024!"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo_info "=== Installation SME Management ==="
echo_info "Domaine/IP: $DOMAIN"

# =============================================================================
# 1. Mise à jour du système
# =============================================================================
echo_info "=== 1/12 Mise à jour du système ==="
apt update && apt upgrade -y

# =============================================================================
# 2. Installation des dépendances système
# =============================================================================
echo_info "=== 2/12 Installation des dépendances système ==="
apt install -y \
    curl wget git nginx certbot python3-certbot-nginx \
    python3 python3-pip python3-venv \
    build-essential libpq-dev \
    postgresql postgresql-contrib \
    supervisor ufw

# =============================================================================
# 3. Installation de Node.js 20.x
# =============================================================================
echo_info "=== 3/12 Installation de Node.js 20.x ==="
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
fi
npm install -g npm@latest
echo_info "Node.js: $(node -v) | NPM: $(npm -v)"

# =============================================================================
# 4. Configuration de PostgreSQL
# =============================================================================
echo_info "=== 4/12 Configuration de PostgreSQL ==="
systemctl start postgresql
systemctl enable postgresql

# Créer l'utilisateur et la base de données (ignorer si existe)
sudo -u postgres psql -c "CREATE USER smeadmin WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo_warn "User smeadmin existe déjà"
sudo -u postgres psql -c "CREATE DATABASE sme_management OWNER smeadmin;" 2>/dev/null || echo_warn "Database sme_management existe déjà"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE sme_management TO smeadmin;" 2>/dev/null || true

# =============================================================================
# 5. Cloner le repository
# =============================================================================
echo_info "=== 5/12 Clonage du repository ==="
if [ -d "$APP_DIR" ]; then
    echo_warn "Suppression de l'ancienne installation..."
    supervisorctl stop sme-backend 2>/dev/null || true
    rm -rf "$APP_DIR"
fi

git clone "$GIT_REPO" "$APP_DIR"
cd "$APP_DIR"
git checkout "$GIT_BRANCH"

# Créer les répertoires nécessaires
mkdir -p "$APP_DIR/uploads/invoices"
mkdir -p "$APP_DIR/uploads/documents"
mkdir -p "$APP_DIR/uploads/expenses"
mkdir -p "$APP_DIR/logs"

# =============================================================================
# 6. Configuration du Backend
# =============================================================================
echo_info "=== 6/12 Configuration du Backend ==="
cd "$APP_DIR/backend"

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Créer le fichier .env
SECRET_KEY=$(openssl rand -hex 32)
cat > .env << ENVEOF
DATABASE_URL=postgresql://smeadmin:${DB_PASSWORD}@localhost:5432/sme_management
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
APP_NAME=SME Management
DEBUG=false
ENVIRONMENT=production
UPLOAD_DIR=${APP_DIR}/uploads
MAX_UPLOAD_SIZE=10485760
ENVEOF

# =============================================================================
# 7. Initialiser la base de données
# =============================================================================
echo_info "=== 7/12 Initialisation de la base de données ==="
python -c "from app.db.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"

# Créer l'utilisateur admin
python << 'ADMINEOF'
from app.db.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
existing = db.query(User).filter(User.email == "admin@sme.be").first()
if existing:
    existing.hashed_password = get_password_hash("admin")
    existing.is_active = True
    print("Admin mis à jour")
else:
    admin = User(
        email="admin@sme.be",
        hashed_password=get_password_hash("admin"),
        first_name="Admin",
        last_name="System",
        is_active=True
    )
    db.add(admin)
    print("Admin créé")
db.commit()
db.close()
ADMINEOF

deactivate

# =============================================================================
# 8. Configuration du Frontend
# =============================================================================
echo_info "=== 8/12 Configuration du Frontend ==="
cd "$APP_DIR/frontend"

cat > .env << ENVEOF
VITE_API_URL=http://${DOMAIN}/api
ENVEOF

npm install
npm run build

# =============================================================================
# 9. Configuration de Supervisor
# =============================================================================
echo_info "=== 9/12 Configuration de Supervisor ==="
cat > /etc/supervisor/conf.d/sme-backend.conf << SUPEOF
[program:sme-backend]
command=${APP_DIR}/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
directory=${APP_DIR}/backend
user=root
autostart=true
autorestart=true
stderr_logfile=${APP_DIR}/logs/backend.err.log
stdout_logfile=${APP_DIR}/logs/backend.out.log
SUPEOF

systemctl enable supervisor
systemctl start supervisor
sleep 2
supervisorctl reread
supervisorctl update
supervisorctl restart sme-backend || supervisorctl start sme-backend

# =============================================================================
# 10. Configuration de Nginx
# =============================================================================
echo_info "=== 10/12 Configuration de Nginx ==="
cat > /etc/nginx/sites-available/sme-management << 'NGINXEOF'
server {
    listen 80;
    server_name _;

    root /opt/sme-management/frontend/dist;
    index index.html;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        client_max_body_size 10M;
    }

    location /uploads {
        alias /opt/sme-management/uploads;
        expires 30d;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINXEOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/sme-management /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# =============================================================================
# 11. Configuration du Firewall
# =============================================================================
echo_info "=== 11/12 Configuration du Firewall ==="
ufw allow ssh
ufw allow 80
ufw allow 443
ufw --force enable

# =============================================================================
# 12. Permissions
# =============================================================================
echo_info "=== 12/12 Configuration des permissions ==="
chown -R www-data:www-data "$APP_DIR/uploads"
chmod -R 755 "$APP_DIR/uploads"

# =============================================================================
# Vérification finale
# =============================================================================
echo_info "=== Vérification ==="
sleep 3
supervisorctl status sme-backend
curl -s http://localhost/api/health || echo_warn "API health check non disponible"

# =============================================================================
# Résumé
# =============================================================================
echo ""
echo "=============================================="
echo -e "${GREEN}Installation terminée avec succès!${NC}"
echo "=============================================="
echo ""
echo "URL: http://$DOMAIN"
echo "Email: admin@sme.be"
echo "Mot de passe: admin"
echo ""
echo "Commandes utiles:"
echo "  supervisorctl restart sme-backend"
echo "  tail -f $APP_DIR/logs/backend.out.log"
echo ""
