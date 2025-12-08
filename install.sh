#!/bin/bash

# SME Management Application - Installation Script
# This script installs and configures the application on a Linux server
# With HTTPS support via Let's Encrypt

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="sme-management"
APP_DIR="/opt/${APP_NAME}"
DB_NAME="sme_management"
DB_USER="sme_user"
BACKEND_PORT=8000

# Server configuration
SERVER_IP="109.199.101.5"
DOMAIN_NAME=""  # Will be set during installation or use IP

# Print colored message
print_msg() {
    echo -e "${2}${1}${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_msg "This script must be run as root (use sudo)" $RED
        exit 1
    fi
}

# Parse arguments
UPDATE_MODE=false
SKIP_SSL=false
for arg in "$@"; do
    case $arg in
        --update)
            UPDATE_MODE=true
            shift
            ;;
        --skip-ssl)
            SKIP_SSL=true
            shift
            ;;
        --domain=*)
            DOMAIN_NAME="${arg#*=}"
            shift
            ;;
    esac
done

# Detect OS
detect_os() {
    if [ -f /etc/debian_version ]; then
        OS="debian"
        PKG_MANAGER="apt-get"
    elif [ -f /etc/redhat-release ]; then
        OS="redhat"
        PKG_MANAGER="yum"
    else
        print_msg "Unsupported OS. This script supports Debian/Ubuntu and RHEL/CentOS." $RED
        exit 1
    fi
    print_msg "Detected OS: $OS" $GREEN
}

# Install system dependencies
install_dependencies() {
    print_header "Installing System Dependencies"

    if [ "$OS" = "debian" ]; then
        apt-get update
        apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            nodejs \
            npm \
            postgresql \
            postgresql-contrib \
            nginx \
            git \
            curl \
            build-essential \
            libpq-dev \
            libpango-1.0-0 \
            libpangocairo-1.0-0 \
            libgdk-pixbuf2.0-0 \
            libffi-dev \
            shared-mime-info \
            certbot \
            python3-certbot-nginx

        # Install Node.js 20.x if older version
        NODE_VERSION=$(node -v 2>/dev/null | cut -d'.' -f1 | tr -d 'v' || echo "0")
        if [ "$NODE_VERSION" -lt 18 ]; then
            curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
            apt-get install -y nodejs
        fi

    elif [ "$OS" = "redhat" ]; then
        yum update -y
        yum install -y epel-release
        yum install -y \
            python3 \
            python3-pip \
            nodejs \
            npm \
            postgresql-server \
            postgresql-contrib \
            nginx \
            git \
            curl \
            gcc \
            postgresql-devel \
            pango \
            libffi-devel \
            certbot \
            python3-certbot-nginx

        # Initialize PostgreSQL on RHEL
        postgresql-setup --initdb || true
    fi

    print_msg "Dependencies installed successfully" $GREEN
}

# Setup PostgreSQL database
setup_database() {
    print_header "Setting up PostgreSQL Database"

    # Start PostgreSQL
    systemctl enable postgresql
    systemctl start postgresql

    # Generate random password
    DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 16)

    # Create database and user
    sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';" 2>/dev/null || \
        sudo -u postgres psql -c "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"
    sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"

    # Configure PostgreSQL to allow password authentication
    PG_HBA=$(sudo -u postgres psql -t -c "SHOW hba_file;" | xargs)
    if ! grep -q "${DB_USER}" "$PG_HBA"; then
        echo "local   ${DB_NAME}   ${DB_USER}   md5" >> "$PG_HBA"
        echo "host    ${DB_NAME}   ${DB_USER}   127.0.0.1/32   md5" >> "$PG_HBA"
        systemctl reload postgresql
    fi

    print_msg "Database setup complete" $GREEN
    print_msg "Database password: ${DB_PASSWORD}" $YELLOW
}

# Clone or update repository
setup_code() {
    print_header "Setting up Application Code"

    if [ -d "$APP_DIR" ]; then
        if [ "$UPDATE_MODE" = true ]; then
            print_msg "Updating existing installation..." $YELLOW
            cd "$APP_DIR"
            git pull origin main || git pull origin master || true
        else
            print_msg "Application directory already exists. Use --update to update." $YELLOW
        fi
    else
        # For development, copy current directory
        mkdir -p "$APP_DIR"
        cp -r . "$APP_DIR/"
    fi

    print_msg "Code setup complete" $GREEN
}

# Setup Python backend
setup_backend() {
    print_header "Setting up Backend"

    cd "${APP_DIR}/backend"

    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate

    # Install Python dependencies
    pip install --upgrade pip
    pip install -r requirements.txt

    # Determine URL scheme and origins
    if [ -n "$DOMAIN_NAME" ]; then
        SITE_URL="https://${DOMAIN_NAME}"
        CORS_ORIGINS="https://${DOMAIN_NAME},https://www.${DOMAIN_NAME}"
    else
        if [ "$SKIP_SSL" = true ]; then
            SITE_URL="http://${SERVER_IP}"
            CORS_ORIGINS="http://${SERVER_IP},http://localhost"
        else
            SITE_URL="https://${SERVER_IP}"
            CORS_ORIGINS="https://${SERVER_IP},http://${SERVER_IP},http://localhost"
        fi
    fi

    # Create .env file
    if [ ! -f .env ] || [ "$UPDATE_MODE" = false ]; then
        SECRET_KEY=$(openssl rand -base64 32)
        JWT_SECRET=$(openssl rand -base64 32)

        cat > .env << EOF
# Application
APP_NAME=SME Management
DEBUG=false
SECRET_KEY=${SECRET_KEY}

# Database
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}

# JWT
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# CORS
CORS_ORIGINS=${CORS_ORIGINS}

# File uploads
UPLOAD_DIR=${APP_DIR}/uploads
MAX_UPLOAD_SIZE=10485760

# Defaults
DEFAULT_CURRENCY=EUR
DEFAULT_VAT_RATE=21.0
DEFAULT_PAYMENT_TERMS=30

# Server
SITE_URL=${SITE_URL}
EOF
    fi

    # Create upload directories
    mkdir -p "${APP_DIR}/uploads"/{logos,invoices,receipts,payslips}
    chmod -R 755 "${APP_DIR}/uploads"

    # Run database migrations
    if [ "$UPDATE_MODE" = true ]; then
        alembic upgrade head 2>/dev/null || python -c "from app.db.database import init_db; init_db()"
    else
        python -c "from app.db.database import init_db; init_db()"
    fi

    deactivate
    print_msg "Backend setup complete" $GREEN
}

# Setup Node.js frontend
setup_frontend() {
    print_header "Setting up Frontend"

    cd "${APP_DIR}/frontend"

    # Install Node.js dependencies
    npm install

    # Build for production
    npm run build

    print_msg "Frontend setup complete" $GREEN
}

# Create systemd service for backend
create_backend_service() {
    print_header "Creating Backend Service"

    cat > /etc/systemd/system/sme-backend.service << EOF
[Unit]
Description=SME Management Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}/backend
Environment="PATH=${APP_DIR}/backend/venv/bin"
ExecStart=${APP_DIR}/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:${BACKEND_PORT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable sme-backend
    systemctl restart sme-backend

    print_msg "Backend service created and started" $GREEN
}

# Configure Nginx without SSL (initial setup)
configure_nginx_http() {
    print_header "Configuring Nginx (HTTP)"

    # Determine server name
    if [ -n "$DOMAIN_NAME" ]; then
        SERVER_NAME="$DOMAIN_NAME www.$DOMAIN_NAME"
    else
        SERVER_NAME="$SERVER_IP"
    fi

    cat > /etc/nginx/sites-available/sme-management << EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${SERVER_NAME};

    # Frontend (static files)
    root ${APP_DIR}/frontend/dist;
    index index.html;

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT}/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        client_max_body_size 10M;
    }

    # Uploads
    location /uploads/ {
        alias ${APP_DIR}/uploads/;
        expires 30d;
    }

    # Frontend routing (SPA)
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/sme-management /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

    # Test and reload Nginx
    nginx -t
    systemctl enable nginx
    systemctl restart nginx

    print_msg "Nginx HTTP configured and started" $GREEN
}

# Configure SSL with Let's Encrypt
configure_ssl() {
    print_header "Configuring HTTPS with Let's Encrypt"

    if [ -n "$DOMAIN_NAME" ]; then
        # Domain-based SSL certificate
        print_msg "Obtaining SSL certificate for ${DOMAIN_NAME}..." $YELLOW

        certbot --nginx -d "$DOMAIN_NAME" -d "www.$DOMAIN_NAME" \
            --non-interactive \
            --agree-tos \
            --email "admin@${DOMAIN_NAME}" \
            --redirect

        print_msg "SSL certificate obtained and configured" $GREEN
    else
        # IP-based self-signed certificate (Let's Encrypt doesn't support IP addresses)
        print_msg "Creating self-signed SSL certificate for IP ${SERVER_IP}..." $YELLOW

        # Create SSL directory
        mkdir -p /etc/nginx/ssl

        # Generate self-signed certificate
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/selfsigned.key \
            -out /etc/nginx/ssl/selfsigned.crt \
            -subj "/C=BE/ST=Brussels/L=Brussels/O=SME Management/CN=${SERVER_IP}"

        # Generate DH parameters
        if [ ! -f /etc/nginx/ssl/dhparam.pem ]; then
            openssl dhparam -out /etc/nginx/ssl/dhparam.pem 2048
        fi

        # Configure Nginx with SSL
        cat > /etc/nginx/sites-available/sme-management << EOF
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name ${SERVER_IP};
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${SERVER_IP};

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/selfsigned.crt;
    ssl_certificate_key /etc/nginx/ssl/selfsigned.key;
    ssl_dhparam /etc/nginx/ssl/dhparam.pem;

    # SSL Security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling off;

    # Frontend (static files)
    root ${APP_DIR}/frontend/dist;
    index index.html;

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT}/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        client_max_body_size 10M;
    }

    # Uploads
    location /uploads/ {
        alias ${APP_DIR}/uploads/;
        expires 30d;
    }

    # Frontend routing (SPA)
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
EOF

        # Reload Nginx
        nginx -t
        systemctl reload nginx

        print_msg "Self-signed SSL certificate configured" $GREEN
        print_msg "Note: Browser will show a security warning for self-signed certificates" $YELLOW
    fi
}

# Setup automatic certificate renewal
setup_ssl_renewal() {
    if [ -n "$DOMAIN_NAME" ]; then
        print_header "Setting up automatic SSL renewal"

        # Create renewal cron job
        cat > /etc/cron.d/certbot-renewal << EOF
# Renew Let's Encrypt certificates twice daily
0 0,12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF

        print_msg "Automatic SSL renewal configured" $GREEN
    fi
}

# Initial setup wizard
setup_wizard() {
    print_header "Initial Configuration"

    echo "Please provide the initial configuration:"
    echo ""

    read -p "Company name: " COMPANY_NAME
    read -p "Company VAT number (optional): " VAT_NUMBER
    read -p "Admin email: " ADMIN_EMAIL
    read -p "Admin first name: " ADMIN_FIRST_NAME
    read -p "Admin last name: " ADMIN_LAST_NAME
    read -s -p "Admin password: " ADMIN_PASSWORD
    echo ""

    # Create initial admin user and company settings via API
    cd "${APP_DIR}/backend"
    source venv/bin/activate

    python << EOF
import sys
sys.path.insert(0, '.')

from app.db.database import SessionLocal
from app.models.user import User
from app.models.company import CompanySettings
from app.models.expense import ExpenseType
from app.core.security import get_password_hash

db = SessionLocal()

# Create admin user
admin = User(
    email="${ADMIN_EMAIL}",
    hashed_password=get_password_hash("${ADMIN_PASSWORD}"),
    first_name="${ADMIN_FIRST_NAME}",
    last_name="${ADMIN_LAST_NAME}",
    is_active=True
)
db.add(admin)

# Create company settings
company = CompanySettings(
    company_name="${COMPANY_NAME}",
    vat_number="${VAT_NUMBER}" if "${VAT_NUMBER}" else None,
    vat_rates=[21.0, 12.0, 6.0, 0.0],
    default_vat_rate=21.0,
    default_currency="EUR",
    default_payment_terms=30
)
db.add(company)

# Create default expense types
expense_types = [
    "Déplacement",
    "Repas",
    "Hébergement",
    "Parking",
    "Matériel",
    "Fournitures bureau",
    "Télécommunications",
    "Formation",
    "Divers"
]
for name in expense_types:
    db.add(ExpenseType(name=name))

db.commit()
print("Initial setup complete!")
EOF

    deactivate
    print_msg "Initial configuration complete" $GREEN
}

# Print completion message
print_completion() {
    print_header "Installation Complete!"

    echo -e "${GREEN}The SME Management application has been installed successfully!${NC}"
    echo ""

    if [ -n "$DOMAIN_NAME" ]; then
        echo -e "Access the application at: ${BLUE}https://${DOMAIN_NAME}${NC}"
    else
        if [ "$SKIP_SSL" = true ]; then
            echo -e "Access the application at: ${BLUE}http://${SERVER_IP}${NC}"
        else
            echo -e "Access the application at: ${BLUE}https://${SERVER_IP}${NC}"
            echo -e "${YELLOW}Note: Accept the self-signed certificate warning in your browser${NC}"
        fi
    fi

    echo ""
    echo "Login with your admin credentials."
    echo ""
    echo -e "${YELLOW}Important next steps:${NC}"
    echo "1. Configure your email (SMTP) settings in the application"
    echo "2. Upload your company logo"
    echo "3. Configure PayPal if needed"
    echo "4. Configure Peppol/e-invoicing if needed"
    echo "5. Add your articles/services catalog"
    echo "6. Add your clients"
    echo ""

    if [ -z "$DOMAIN_NAME" ] && [ "$SKIP_SSL" = false ]; then
        echo -e "${YELLOW}For a proper SSL certificate:${NC}"
        echo "1. Point a domain name to ${SERVER_IP}"
        echo "2. Run: sudo ./install.sh --update --domain=yourdomain.com"
        echo ""
    fi

    echo -e "${YELLOW}Useful commands:${NC}"
    echo "  - View backend logs: journalctl -u sme-backend -f"
    echo "  - Restart backend: systemctl restart sme-backend"
    echo "  - Restart Nginx: systemctl restart nginx"
    echo "  - Renew SSL (if domain): certbot renew"
    echo ""
    echo -e "${BLUE}Server IP: ${SERVER_IP}${NC}"
}

# Main installation flow
main() {
    print_header "SME Management Application Installer"
    print_msg "Target server: ${SERVER_IP}" $BLUE

    if [ "$UPDATE_MODE" = true ]; then
        print_msg "Running in UPDATE mode" $YELLOW
    fi

    if [ -n "$DOMAIN_NAME" ]; then
        print_msg "Domain: ${DOMAIN_NAME}" $BLUE
    fi

    check_root
    detect_os

    if [ "$UPDATE_MODE" = false ]; then
        install_dependencies
        setup_database
    fi

    setup_code
    setup_backend
    setup_frontend
    create_backend_service
    configure_nginx_http

    if [ "$SKIP_SSL" = false ]; then
        configure_ssl
        setup_ssl_renewal
    fi

    if [ "$UPDATE_MODE" = false ]; then
        setup_wizard
    fi

    print_completion
}

# Run main
main
