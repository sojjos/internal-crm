#!/bin/bash
# SME Management - Quick Install Script
# Usage: curl -fsSL https://raw.githubusercontent.com/sojjos/internal-crm/main/quickinstall.sh | sudo bash
# Or: wget -qO- https://raw.githubusercontent.com/sojjos/internal-crm/main/quickinstall.sh | sudo bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        SME Management - Installation automatique           ║"
echo "║        Application de gestion PME (Belgique)               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Erreur: Ce script doit être exécuté en tant que root (sudo)${NC}"
    exit 1
fi

# Configuration
REPO_URL="https://github.com/sojjos/internal-crm.git"
INSTALL_DIR="/opt/sme-management"
BRANCH="main"

# Parse arguments
DOMAIN=""
SKIP_SSL=false

for arg in "$@"; do
    case $arg in
        --domain=*)
            DOMAIN="${arg#*=}"
            ;;
        --skip-ssl)
            SKIP_SSL=true
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --domain=DOMAIN    Configure SSL with Let's Encrypt for this domain"
            echo "  --skip-ssl         Skip SSL configuration (HTTP only)"
            echo "  --help             Show this help message"
            exit 0
            ;;
    esac
done

# Install git if not present
echo -e "${YELLOW}[1/4] Vérification des prérequis...${NC}"
if ! command -v git &> /dev/null; then
    echo "Installation de git..."
    if command -v apt-get &> /dev/null; then
        apt-get update -qq
        apt-get install -y -qq git
    elif command -v yum &> /dev/null; then
        yum install -y -q git
    else
        echo -e "${RED}Erreur: Gestionnaire de paquets non supporté${NC}"
        exit 1
    fi
fi

# Clone or update repository
echo -e "${YELLOW}[2/4] Téléchargement du code source...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    echo "Mise à jour du dépôt existant..."
    cd "$INSTALL_DIR"
    git fetch origin
    git reset --hard origin/$BRANCH
else
    echo "Clonage du dépôt..."
    git clone --depth 1 --branch $BRANCH "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Make install script executable
chmod +x install.sh

# Build install command
echo -e "${YELLOW}[3/4] Lancement de l'installation...${NC}"
INSTALL_CMD="./install.sh"

if [ -n "$DOMAIN" ]; then
    INSTALL_CMD="$INSTALL_CMD --domain=$DOMAIN"
fi

if [ "$SKIP_SSL" = true ]; then
    INSTALL_CMD="$INSTALL_CMD --skip-ssl"
fi

# Run installation
echo "Exécution: $INSTALL_CMD"
$INSTALL_CMD

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Installation terminée !                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Show access info
if [ -n "$DOMAIN" ]; then
    echo -e "Accès: ${GREEN}https://$DOMAIN${NC}"
else
    SERVER_IP=$(hostname -I | awk '{print $1}')
    if [ "$SKIP_SSL" = true ]; then
        echo -e "Accès: ${GREEN}http://$SERVER_IP${NC}"
    else
        echo -e "Accès: ${GREEN}https://$SERVER_IP${NC}"
    fi
fi

echo ""
echo "Documentation API: /docs"
echo "Logs: journalctl -u sme-backend -f"
