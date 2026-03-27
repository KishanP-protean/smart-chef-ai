#!/bin/bash
# ============================================================
# Chef Gemini — One-Click Cloud Run Deployment
# ============================================================
# Usage: bash deploy.sh
# ============================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}${BOLD}🧠👨‍🍳 Smart Chef AI — Multi-Agent Recipe Generator${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ---- Get Project ID ----
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || true)

if [ -n "$CURRENT_PROJECT" ]; then
    echo -e "${YELLOW}Current GCP project: ${BOLD}${CURRENT_PROJECT}${NC}"
    read -p "Use this project? (Y/n): " USE_CURRENT
    if [[ "$USE_CURRENT" =~ ^[Nn]$ ]]; then
        read -p "Enter your GCP Project ID: " PROJECT_ID
    else
        PROJECT_ID=$CURRENT_PROJECT
    fi
else
    read -p "Enter your GCP Project ID: " PROJECT_ID
fi

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Project ID is required. Exiting.${NC}"
    exit 1
fi

# ---- Set Region ----
DEFAULT_REGION="us-central1"
read -p "Enter deployment region [$DEFAULT_REGION]: " REGION
REGION=${REGION:-$DEFAULT_REGION}

# ---- Service Name ----
SERVICE_NAME="smart-chef-ai"

echo ""
echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo -e "   Project:  ${BOLD}${PROJECT_ID}${NC}"
echo -e "   Region:   ${BOLD}${REGION}${NC}"
echo -e "   Service:  ${BOLD}${SERVICE_NAME}${NC}"
echo ""

# ---- Set Project ----
echo -e "${YELLOW}🔧 Setting project...${NC}"
gcloud config set project "$PROJECT_ID"

# ---- Enable APIs ----
echo -e "${YELLOW}🔌 Enabling required APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com \
    --quiet

echo -e "${GREEN}✅ APIs enabled${NC}"

# ---- Create .env file ----
echo -e "${YELLOW}📝 Creating .env file...${NC}"
cat > .env << EOF
GOOGLE_CLOUD_PROJECT=${PROJECT_ID}
GOOGLE_CLOUD_LOCATION=${REGION}
GOOGLE_GENAI_USE_VERTEXAI=1
MODEL=gemini-2.5-flash
EOF
echo -e "${GREEN}✅ .env file created${NC}"

# ---- Deploy to Cloud Run ----
echo ""
echo -e "${YELLOW}🚀 Deploying to Cloud Run (this may take 3-5 minutes)...${NC}"
echo ""

gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=1,MODEL=gemini-2.5-flash" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --min-instances 0 \
    --max-instances 5 \
    --quiet

# ---- Get URL ----
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")

echo ""
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}✅ Deployment Successful!${NC}"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "   🌐 ${BOLD}Live URL: ${CYAN}${SERVICE_URL}${NC}"
echo ""
echo -e "   📡 Health Check: ${CYAN}${SERVICE_URL}/health${NC}"
echo -e "   🍽️  Web UI:      ${CYAN}${SERVICE_URL}/${NC}"
echo ""
echo -e "${YELLOW}💡 To delete this service later:${NC}"
echo -e "   gcloud run services delete ${SERVICE_NAME} --region ${REGION}"
echo ""
