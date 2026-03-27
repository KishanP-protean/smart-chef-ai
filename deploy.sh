#!/bin/bash
# ============================================================
# Smart Chef AI — One-Click Cloud Run Deployment
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
    vpcaccess.googleapis.com \
    compute.googleapis.com \
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

# ---- Auto-detect VPC Network and Subnet ----
echo -e "${YELLOW}🔍 Detecting VPC network...${NC}"
VPC_NETWORK=$(gcloud compute networks list --format="value(name)" --limit=1 2>/dev/null || echo "")
if [ -z "$VPC_NETWORK" ]; then
    echo -e "${RED}❌ No VPC network found. Creating default network...${NC}"
    gcloud compute networks create default --subnet-mode=auto --quiet 2>/dev/null || true
    VPC_NETWORK="default"
fi
echo -e "   Network: ${BOLD}${VPC_NETWORK}${NC}"

# Find subnet in the target region
VPC_SUBNET=$(gcloud compute networks subnets list --network="$VPC_NETWORK" --regions="$REGION" --format="value(name)" --limit=1 2>/dev/null || echo "")
if [ -z "$VPC_SUBNET" ]; then
    echo -e "${YELLOW}   No subnet in ${REGION}, trying to find any subnet...${NC}"
    VPC_SUBNET=$(gcloud compute networks subnets list --network="$VPC_NETWORK" --format="value(name)" --limit=1 2>/dev/null || echo "$VPC_NETWORK")
fi
echo -e "   Subnet:  ${BOLD}${VPC_SUBNET}${NC}"

# ---- Create Artifact Registry repo if needed ----
echo -e "${YELLOW}📦 Setting up Artifact Registry...${NC}"
gcloud artifacts repositories create cloud-run-source-deploy \
    --repository-format=docker \
    --location="${REGION}" \
    --quiet 2>/dev/null || echo -e "   Repository already exists, continuing..."

IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${SERVICE_NAME}:latest"

# ---- Step 1: Build the container image ----
echo ""
echo -e "${YELLOW}🔨 Step 1/2: Building container image (this may take 3-5 minutes)...${NC}"
echo ""

gcloud builds submit \
    --tag "${IMAGE_URL}" \
    --region="${REGION}" \
    .

echo -e "${GREEN}✅ Container image built successfully${NC}"

# ---- Step 2: Deploy to Cloud Run ----
echo ""
echo -e "${YELLOW}🚀 Step 2/2: Deploying to Cloud Run...${NC}"
echo ""

gcloud run deploy "$SERVICE_NAME" \
    --image "${IMAGE_URL}" \
    --region "$REGION" \
    --no-allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=1,MODEL=gemini-2.5-flash" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --min-instances 0 \
    --max-instances 5 \
    --ingress internal-and-cloud-load-balancing \
    --network "$VPC_NETWORK" \
    --subnet "$VPC_SUBNET" \
    --vpc-egress all-traffic \
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
echo -e "${YELLOW}💡 To access from browser, proxy the service:${NC}"
echo -e "   gcloud run services proxy ${SERVICE_NAME} --region ${REGION} --port 8080"
echo ""
echo -e "${YELLOW}💡 To delete this service later:${NC}"
echo -e "   gcloud run services delete ${SERVICE_NAME} --region ${REGION}"
echo ""
