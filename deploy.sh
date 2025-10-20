#!/bin/bash

# Avisia UTM Builder - Script de déploiement automatique sur Cloud Run
# Usage: ./deploy.sh

set -e  # Exit on error

# Couleurs pour l'output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="your-project-id"  # À remplacer par votre PROJECT_ID
REGION="europe-west1"
SERVICE_NAME="avisia-utm-builder"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Déploiement Avisia UTM Builder      ${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Vérification des prérequis
echo -e "${YELLOW}📋 Vérification des prérequis...${NC}"

# Vérifier si gcloud est installé
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI n'est pas installé. Installez-le depuis https://cloud.google.com/sdk${NC}"
    exit 1
fi

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker n'est pas installé. Installez-le depuis https://www.docker.com${NC}"
    exit 1
fi

# Vérifier si client_secrets.json existe
if [ ! -f "client_secrets.json" ]; then
    echo -e "${RED}❌ Le fichier client_secrets.json est manquant!${NC}"
    echo -e "${YELLOW}Téléchargez-le depuis Google Cloud Console > APIs & Services > Credentials${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Tous les prérequis sont satisfaits${NC}\n"

# Configuration du projet
echo -e "${YELLOW}🔧 Configuration du projet GCP...${NC}"
gcloud config set project ${PROJECT_ID}
echo -e "${GREEN}✅ Projet configuré: ${PROJECT_ID}${NC}\n"

# Activation des APIs nécessaires
echo -e "${YELLOW}🔌 Activation des APIs nécessaires...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
echo -e "${GREEN}✅ APIs activées${NC}\n"

# Build de l'image Docker
echo -e "${YELLOW}🐳 Construction de l'image Docker...${NC}"
docker build -t ${IMAGE_NAME}:latest .
echo -e "${GREEN}✅ Image Docker construite${NC}\n"

# Push de l'image vers GCR
echo -e "${YELLOW}📤 Push de l'image vers Container Registry...${NC}"
docker push ${IMAGE_NAME}:latest
echo -e "${GREEN}✅ Image pushée${NC}\n"

# Déploiement sur Cloud Run
echo -e "${YELLOW}🚀 Déploiement sur Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "REDIRECT_URI=https://${SERVICE_NAME}-$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)' 2>/dev/null | cut -d'/' -f3)" \
  2>&1 | tee deploy.log

echo -e "${GREEN}✅ Déploiement réussi!${NC}\n"

# Récupération de l'URL du service
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} \
  --format "value(status.url)")

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ DÉPLOIEMENT TERMINÉ !            ${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${YELLOW}🔗 URL de votre application:${NC}"
echo -e "${GREEN}${SERVICE_URL}${NC}\n"

echo -e "${YELLOW}📋 Prochaines étapes:${NC}"
echo -e "1. Allez sur Google Cloud Console > APIs & Services > Credentials"
echo -e "2. Éditez votre OAuth 2.0 Client ID"
echo -e "3. Ajoutez cette URL dans 'Authorized redirect URIs':"
echo -e "   ${GREEN}${SERVICE_URL}${NC}"
echo -e "4. Ajoutez également dans 'Authorized JavaScript origins':"
echo -e "   ${GREEN}${SERVICE_URL}${NC}"
echo -e "5. Sauvegardez les modifications\n"

echo -e "${YELLOW}🔄 Pour redéployer plus tard, lancez:${NC}"
echo -e "   ${GREEN}./deploy.sh${NC}\n"

echo -e "${YELLOW}📊 Pour voir les logs:${NC}"
echo -e "   ${GREEN}gcloud run services logs tail ${SERVICE_NAME} --region ${REGION}${NC}\n"

# Proposer d'ouvrir l'URL dans le navigateur
read -p "Voulez-vous ouvrir l'application dans votre navigateur? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open ${SERVICE_URL}
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open ${SERVICE_URL}
    else
        echo -e "${YELLOW}Ouvrez cette URL dans votre navigateur: ${SERVICE_URL}${NC}"
    fi
fi

echo -e "\n${GREEN}🎉 Déploiement terminé avec succès!${NC}\n"
