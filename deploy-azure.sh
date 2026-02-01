#!/bin/bash

# Honest Stylist Azure Deployment Script
# This script automates the deployment to Azure

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="honest-stylist-rg"
REGISTRY_NAME="honeststylist"
APP_NAME="honest-stylist"
LOCATION="eastus"
PLAN_NAME="honest-stylist-plan"
DOCKER_IMAGE="honeststylist"

# Functions
print_section() {
    echo -e "\n${YELLOW}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
print_section "Checking Prerequisites"

if ! command -v az &> /dev/null; then
    print_error "Azure CLI not found. Please install it from https://learn.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi
print_success "Azure CLI found"

if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please install it from https://www.docker.com/products/docker-desktop"
    exit 1
fi
print_success "Docker found"

# Login to Azure
print_section "Logging in to Azure"
az login

# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
print_success "Using subscription: $SUBSCRIPTION_ID"

# Create resource group
print_section "Creating Resource Group"
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION
print_success "Resource group created: $RESOURCE_GROUP"

# Create Container Registry
print_section "Creating Azure Container Registry"
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $REGISTRY_NAME \
    --sku Basic \
    --admin-enabled true
print_success "Container registry created: $REGISTRY_NAME"

# Get registry credentials
print_section "Getting Registry Credentials"
REGISTRY_USERNAME=$(az acr credential show \
    --resource-group $RESOURCE_GROUP \
    --name $REGISTRY_NAME \
    --query username -o tsv)
REGISTRY_PASSWORD=$(az acr credential show \
    --resource-group $RESOURCE_GROUP \
    --name $REGISTRY_NAME \
    --query passwords[0].value -o tsv)
REGISTRY_URL="$REGISTRY_NAME.azurecr.io"
print_success "Registry credentials obtained"

# Build and push image
print_section "Building Docker Image"
docker build -t $DOCKER_IMAGE:latest .
print_success "Docker image built"

print_section "Pushing Image to Azure Container Registry"
docker tag $DOCKER_IMAGE:latest $REGISTRY_URL/$DOCKER_IMAGE:latest
docker login -u $REGISTRY_USERNAME -p $REGISTRY_PASSWORD $REGISTRY_URL
docker push $REGISTRY_URL/$DOCKER_IMAGE:latest
print_success "Image pushed to registry"

# Create App Service Plan
print_section "Creating App Service Plan"
az appservice plan create \
    --name $PLAN_NAME \
    --resource-group $RESOURCE_GROUP \
    --sku B1 \
    --is-linux
print_success "App Service Plan created"

# Create Web App
print_section "Creating Web App"
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan $PLAN_NAME \
    --name $APP_NAME \
    --deployment-container-image-name $REGISTRY_URL/$DOCKER_IMAGE:latest
print_success "Web App created"

# Configure container settings
print_section "Configuring Container Settings"
az webapp config container set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-custom-image-name $REGISTRY_URL/$DOCKER_IMAGE:latest \
    --docker-registry-server-url https://$REGISTRY_URL \
    --docker-registry-server-user $REGISTRY_USERNAME \
    --docker-registry-server-password $REGISTRY_PASSWORD
print_success "Container settings configured"

# Prompt for API key
print_section "Configuring Application Settings"
read -p "Enter your Google API key: " GOOGLE_API_KEY

# Set environment variables
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --settings GOOGLE_API_KEY="$GOOGLE_API_KEY" \
    WEBSITES_PORT=8000
print_success "Application settings configured"

# Get the app URL
print_section "Deployment Complete"
APP_URL=$(az webapp show \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --query defaultHostName -o tsv)
echo -e "${GREEN}✓ Your app is available at: https://$APP_URL${NC}"
echo -e "\nDeployment Summary:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  App Name: $APP_NAME"
echo "  Registry: $REGISTRY_URL"
echo "  Location: $LOCATION"
echo "  URL: https://$APP_URL"
echo -e "\nNext steps:"
echo "  1. Open the URL in your browser"
echo "  2. Monitor logs: az webapp log tail -g $RESOURCE_GROUP -n $APP_NAME"
echo "  3. Scale up if needed: az appservice plan update -g $RESOURCE_GROUP -n $PLAN_NAME --sku S1"
