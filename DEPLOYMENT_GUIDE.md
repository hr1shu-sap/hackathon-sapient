# Honest Stylist - Azure Deployment Guide

This guide walks you through deploying the Honest Stylist application to Azure Container Instances (ACI) or Azure App Service.

## Prerequisites

- Azure account with an active subscription
- Azure CLI installed ([Download](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli))
- Docker installed ([Download](https://www.docker.com/products/docker-desktop))
- Git installed
- API keys for Google Gemini (if using AI features)

## Option 1: Deploy Using Azure Container Registry + App Service (Recommended)

### Step 1: Create Resource Group

```bash
az group create --name honest-stylist-rg --location eastus
```

### Step 2: Create Azure Container Registry

```bash
az acr create --resource-group honest-stylist-rg \
  --name honeststylist \
  --sku Basic
```

### Step 3: Build and Push Docker Image

```bash
# Login to Azure Container Registry
az acr login --name honeststylist

# Build and push image
az acr build --registry honeststylist \
  --image honeststylist:latest \
  --file Dockerfile .
```

### Step 4: Create App Service Plan

```bash
az appservice plan create \
  --name honest-stylist-plan \
  --resource-group honest-stylist-rg \
  --sku B1 \
  --is-linux
```

### Step 5: Create Web App from Container

```bash
az webapp create \
  --resource-group honest-stylist-rg \
  --plan honest-stylist-plan \
  --name honest-stylist \
  --deployment-container-image-name honeststylist.azurecr.io/honeststylist:latest
```

### Step 6: Configure Container Settings

```bash
az webapp config container set \
  --name honest-stylist \
  --resource-group honest-stylist-rg \
  --docker-custom-image-name honeststylist.azurecr.io/honeststylist:latest \
  --docker-registry-server-url https://honeststylist.azurecr.io \
  --docker-registry-server-user <username> \
  --docker-registry-server-password <password>
```

Get your credentials:
```bash
az acr credential show --resource-group honest-stylist-rg --name honeststylist
```

### Step 7: Configure Application Settings

```bash
az webapp config appsettings set \
  --resource-group honest-stylist-rg \
  --name honest-stylist \
  --settings GOOGLE_API_KEY="your-api-key-here"
```

## Option 2: Deploy Using Azure Container Instances (Quick Start)

### Step 1: Build and Push Docker Image

```bash
# Build locally
docker build -t honeststylist:latest .

# Tag for ACR
docker tag honeststylist:latest honeststylist.azurecr.io/honeststylist:latest

# Login and push
az acr login --name honeststylist
docker push honeststylist.azurecr.io/honeststylist:latest
```

### Step 2: Deploy to Container Instances

```bash
az container create \
  --resource-group honest-stylist-rg \
  --name honest-stylist-container \
  --image honeststylist.azurecr.io/honeststylist:latest \
  --cpu 1 \
  --memory 1.5 \
  --registry-login-server honeststylist.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --environment-variables GOOGLE_API_KEY="your-api-key" \
  --ports 80 \
  --protocol TCP
```

### Step 3: Get Container URL

```bash
az container show \
  --resource-group honest-stylist-rg \
  --name honest-stylist-container \
  --query ipAddress.fqdn
```

## Option 3: Deploy Using GitHub Actions (CI/CD)

1. Fork/push this repository to GitHub
2. Create Azure Service Principal:

```bash
az ad sp create-for-rbac --name honest-stylist-sp \
  --role contributor \
  --scopes /subscriptions/{subscription-id}
```

3. Add GitHub secrets:
   - `AZURE_CREDENTIALS` (from service principal)
   - `GOOGLE_API_KEY` (your API key)

4. Push to main branch - GitHub Actions will automatically build and deploy

## Configuration

### Environment Variables

Set these in Azure App Service Configuration:

```
GOOGLE_API_KEY=your-key-here
STREAMLIT_SERVER_PORT=8000
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
PYTHONUNBUFFERED=1
```

### File Uploads

For persistent storage, use Azure Blob Storage:

```bash
# Create storage account
az storage account create \
  --resource-group honest-stylist-rg \
  --name honeststyliststorage \
  --kind StorageV2 \
  --sku Standard_LRS
```

## Monitoring & Logging

### View Logs

```bash
# App Service logs
az webapp log tail --resource-group honest-stylist-rg --name honest-stylist

# Container logs
az container logs --resource-group honest-stylist-rg --name honest-stylist-container
```

### Enable Application Insights

```bash
az monitor app-insights component create \
  --app honest-stylist-insights \
  --location eastus \
  --resource-group honest-stylist-rg \
  --application-type web
```

## Troubleshooting

### Application won't start
- Check logs: `az webapp log tail`
- Verify GOOGLE_API_KEY is set
- Ensure Docker image is built correctly

### Port issues
- Streamlit runs on port 8000 by default
- Azure App Service automatically maps ports

### Memory issues
- Increase App Service tier (B2 or higher)
- Optimize model loading

## Cost Estimation (Per Month)

- **App Service Plan B1**: ~$13
- **Container Registry Basic**: ~$5
- **Storage (if used)**: ~$0.024 per GB
- **Application Insights**: ~$2.30

**Total (minimal)**: ~$20/month

## Scaling

### Increase Instances

```bash
az appservice plan update \
  --name honest-stylist-plan \
  --resource-group honest-stylist-rg \
  --sku S1
```

### Auto-scale

```bash
az monitor autoscale create \
  --resource-group honest-stylist-rg \
  --resource-name-prefix honest-stylist-plan \
  --resource-type "Microsoft.Web/serverfarms" \
  --min-count 1 \
  --max-count 3 \
  --count 1
```

## Security

- Use Azure Key Vault for API keys
- Enable authentication (Azure AD or managed identity)
- Configure WAF (Web Application Firewall) for DDoS protection
- Regularly update dependencies

## Next Steps

1. Monitor application performance in Azure Portal
2. Set up continuous deployment from GitHub
3. Configure custom domain
4. Enable HTTPS/SSL certificate

## Support

For issues, check:
- Azure App Service diagnostics
- Application logs
- Container registry build history
