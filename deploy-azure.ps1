# Honest Stylist Azure Deployment Script (PowerShell)
# Run this script to deploy the application to Azure

param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "honest-stylist-rg",
    
    [Parameter(Mandatory=$false)]
    [string]$RegistryName = "honeststylist",
    
    [Parameter(Mandatory=$false)]
    [string]$AppName = "honest-stylist",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus",
    
    [Parameter(Mandatory=$false)]
    [string]$PlanName = "honest-stylist-plan",
    
    [Parameter(Mandatory=$false)]
    [string]$GoogleApiKey = ""
)

# Colors
$Color_Success = "Green"
$Color_Error = "Red"
$Color_Warning = "Yellow"
$Color_Info = "Cyan"

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor $Color_Success
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor $Color_Error
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor $Color_Warning
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor $Color_Info
}

function Write-Section {
    param([string]$Title)
    Write-Host "`n=== $Title ===" -ForegroundColor $Color_Warning
}

# Check prerequisites
Write-Section "Checking Prerequisites"

try {
    $azVersion = az --version 2>$null
    Write-Success "Azure CLI found"
} catch {
    Write-Error-Custom "Azure CLI not found. Install from: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

try {
    $dockerVersion = docker --version 2>$null
    Write-Success "Docker found"
} catch {
    Write-Error-Custom "Docker not found. Install from: https://www.docker.com/products/docker-desktop"
    exit 1
}

# Login to Azure
Write-Section "Logging in to Azure"
Write-Info "Opening browser for login..."
az login

# Get subscription ID
$subscriptionId = az account show --query id -o tsv
Write-Success "Using subscription: $subscriptionId"

# Create resource group
Write-Section "Creating Resource Group"
Write-Info "Creating: $ResourceGroup in $Location"
az group create --name $ResourceGroup --location $Location
Write-Success "Resource group created"

# Create Container Registry
Write-Section "Creating Azure Container Registry"
Write-Info "Creating: $RegistryName"
az acr create `
    --resource-group $ResourceGroup `
    --name $RegistryName `
    --sku Basic `
    --admin-enabled true
Write-Success "Container registry created"

# Get registry credentials
Write-Section "Getting Registry Credentials"
$registryUsername = az acr credential show `
    --resource-group $ResourceGroup `
    --name $RegistryName `
    --query username -o tsv
    
$registryPassword = az acr credential show `
    --resource-group $ResourceGroup `
    --name $RegistryName `
    --query "passwords[0].value" -o tsv
    
$registryUrl = "$RegistryName.azurecr.io"
Write-Success "Registry credentials obtained"

# Build Docker image
Write-Section "Building Docker Image"
Write-Info "Building Docker image..."
docker build -t honeststylist:latest .
Write-Success "Docker image built successfully"

# Push image to registry
Write-Section "Pushing Image to Azure Container Registry"
Write-Info "Tagging image for registry..."
docker tag honeststylist:latest "$registryUrl/honeststylist:latest"

Write-Info "Logging in to registry..."
$registryPassword | docker login -u $registryUsername --password-stdin $registryUrl

Write-Info "Pushing image..."
docker push "$registryUrl/honeststylist:latest"
Write-Success "Image pushed to registry"

# Create App Service Plan
Write-Section "Creating App Service Plan"
Write-Info "Creating: $PlanName (SKU: B1)"
az appservice plan create `
    --name $PlanName `
    --resource-group $ResourceGroup `
    --sku B1 `
    --is-linux
Write-Success "App Service Plan created"

# Create Web App
Write-Section "Creating Web App"
Write-Info "Creating: $AppName"
az webapp create `
    --resource-group $ResourceGroup `
    --plan $PlanName `
    --name $AppName `
    --deployment-container-image-name "$registryUrl/honeststylist:latest"
Write-Success "Web App created"

# Configure container settings
Write-Section "Configuring Container Settings"
Write-Info "Setting up container configuration..."
az webapp config container set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --docker-custom-image-name "$registryUrl/honeststylist:latest" `
    --docker-registry-server-url "https://$registryUrl" `
    --docker-registry-server-user $registryUsername `
    --docker-registry-server-password $registryPassword
Write-Success "Container settings configured"

# Configure application settings
Write-Section "Configuring Application Settings"

if ([string]::IsNullOrEmpty($GoogleApiKey)) {
    Write-Warning-Custom "Google API Key not provided as parameter"
    $GoogleApiKey = Read-Host "Enter your Google API key (or press Enter to skip)"
}

if (-not [string]::IsNullOrEmpty($GoogleApiKey)) {
    Write-Info "Setting Google API Key..."
    az webapp config appsettings set `
        --resource-group $ResourceGroup `
        --name $AppName `
        --settings GOOGLE_API_KEY="$GoogleApiKey"
    Write-Success "Google API Key set"
}

Write-Info "Setting other configuration..."
az webapp config appsettings set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --settings `
    WEBSITES_PORT=8000 `
    STREAMLIT_SERVER_PORT=8000 `
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 `
    STREAMLIT_SERVER_HEADLESS=true `
    PYTHONUNBUFFERED=1
Write-Success "Application settings configured"

# Get app URL
Write-Section "Deployment Complete!"
$appUrl = az webapp show `
    --resource-group $ResourceGroup `
    --name $AppName `
    --query defaultHostName -o tsv

Write-Success "Your app is available at: https://$appUrl"
Write-Host "`nDeployment Summary:" -ForegroundColor $Color_Info
Write-Host "  Resource Group: $ResourceGroup"
Write-Host "  App Name: $AppName"
Write-Host "  Registry: $registryUrl"
Write-Host "  Location: $Location"
Write-Host "  URL: https://$appUrl"
Write-Host "`nNext steps:" -ForegroundColor $Color_Warning
Write-Host "  1. Open the URL in your browser"
Write-Host "  2. Monitor logs: az webapp log tail -g $ResourceGroup -n $AppName"
Write-Host "  3. View in Azure Portal: https://portal.azure.com"
Write-Host "`nUseful commands:" -ForegroundColor $Color_Info
Write-Host "  View logs: az webapp log tail -g $ResourceGroup -n $AppName"
Write-Host "  Restart app: az webapp restart -g $ResourceGroup -n $AppName"
Write-Host "  Scale up: az appservice plan update -g $ResourceGroup -n $PlanName --sku S1"
Write-Host "  Delete resources: az group delete -n $ResourceGroup --yes"
