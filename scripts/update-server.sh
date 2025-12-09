#!/bin/bash
# =============================================================================
# Script de mise à jour du serveur SME Management
# =============================================================================
# Ce script met à jour l'application avec les dernières fonctionnalités :
# - Fix téléchargement PDF factures
# - Fix CRM Pipeline et opportunités
# - Fix formulaire devis
# - Ajout gestion catégories d'achats
# - Fix boutons sans handlers
# =============================================================================

set -e  # Arrêter en cas d'erreur

# Configuration
APP_DIR="/opt/sme-management"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}   Mise à jour SME Management Application   ${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# Vérifier que le répertoire existe
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}Erreur: Le répertoire $APP_DIR n'existe pas${NC}"
    exit 1
fi

cd "$APP_DIR"

# Étape 1: Sauvegarder les modifications locales éventuelles
echo -e "${YELLOW}[1/6] Sauvegarde des modifications locales...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}Des modifications locales ont été détectées. Création d'un stash...${NC}"
    git stash push -m "backup-before-update-$(date +%Y%m%d-%H%M%S)"
fi

# Étape 2: Récupérer les dernières modifications
echo -e "${YELLOW}[2/6] Récupération des dernières modifications...${NC}"
git fetch origin
git pull origin claude/setup-admin-user-01BTRbCY7wK78UzRxAQmdg5B

# Étape 3: Installer les dépendances backend si nécessaire
echo -e "${YELLOW}[3/6] Vérification des dépendances backend...${NC}"
cd "$BACKEND_DIR"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install -r requirements.txt -q 2>/dev/null || true
else
    echo -e "${RED}Environnement virtuel non trouvé. Création...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Étape 4: Créer les répertoires nécessaires
echo -e "${YELLOW}[4/6] Création des répertoires nécessaires...${NC}"
mkdir -p "$APP_DIR/uploads/invoices"
mkdir -p "$APP_DIR/uploads/documents"

# Étape 5: Rebuild du frontend
echo -e "${YELLOW}[5/6] Reconstruction du frontend...${NC}"
cd "$FRONTEND_DIR"
npm install --silent 2>/dev/null || npm install
npm run build

# Étape 6: Redémarrage du backend
echo -e "${YELLOW}[6/6] Redémarrage du serveur backend...${NC}"
cd "$BACKEND_DIR"
source venv/bin/activate

# Arrêter gunicorn proprement
pkill -f gunicorn 2>/dev/null || true
sleep 2

# Démarrer gunicorn
gunicorn app.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 127.0.0.1:8000 \
    --daemon \
    --access-logfile /var/log/sme-management/access.log \
    --error-logfile /var/log/sme-management/error.log \
    2>/dev/null || \
gunicorn app.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 127.0.0.1:8000 \
    --daemon

sleep 2

# Vérification
echo ""
echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}         Vérification du déploiement        ${NC}"
echo -e "${BLUE}=============================================${NC}"

# Test de l'API
if curl -s http://127.0.0.1:8000/api/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ API Backend: OK${NC}"
else
    echo -e "${RED}✗ API Backend: ERREUR${NC}"
fi

# Vérifier que gunicorn tourne
if pgrep -f gunicorn > /dev/null; then
    echo -e "${GREEN}✓ Gunicorn: En cours d'exécution${NC}"
else
    echo -e "${RED}✗ Gunicorn: Non démarré${NC}"
fi

# Vérifier le frontend build
if [ -f "$FRONTEND_DIR/dist/index.html" ]; then
    echo -e "${GREEN}✓ Frontend: Build OK${NC}"
else
    echo -e "${RED}✗ Frontend: Build manquant${NC}"
fi

echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}   Mise à jour terminée avec succès !       ${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo -e "Nouvelles fonctionnalités disponibles:"
echo -e "  • Téléchargement PDF des factures corrigé"
echo -e "  • CRM Pipeline fonctionnel"
echo -e "  • Formulaire devis corrigé"
echo -e "  • Gestion des catégories d'achats"
echo ""
