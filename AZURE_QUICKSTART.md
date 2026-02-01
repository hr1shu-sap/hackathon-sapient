# 🚀 Honest Stylist - Azure Deployment Quick Start

## 3-Minute Quick Deploy (Windows PowerShell)

### Prerequisites ✅
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- Azure Account with active subscription
- Google Gemini API key

### Deploy in 3 Steps

**Step 1: Open PowerShell in the project root**
```powershell
cd "C:\Users\riskumar23\Downloads\Honest Stylist"
```

**Step 2: Run the deployment script**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\deploy-azure.ps1 -GoogleApiKey "your-api-key-here"
```

**Step 3: Wait ~5-10 minutes for deployment**
- Your app URL will be displayed at the end
- Open it in browser and enjoy! 🎉

---

## Manual Azure Deployment (If you prefer)

### Option A: Using Azure Portal (GUI)

1. **Create Container Registry**
   - Search "Container Registries" in Azure Portal
   - Click "Create"
   - Name: `honeststylist`
   - SKU: Basic
   - Click Create

2. **Build and Push Image**
   ```powershell
   docker build -t honeststylist:latest .
   docker tag honeststylist:latest honeststylist.azurecr.io/honeststylist:latest
   docker login honeststylist.azurecr.io
   docker push honeststylist.azurecr.io/honeststylist:latest
   ```

3. **Create App Service**
   - Search "App Services" in Azure Portal
   - Click "Create"
   - Publish: Docker Container
   - Select your container registry and image
   - Configure settings
   - Click Create

4. **Add Environment Variables**
   - Go to Settings → Configuration
   - Add `GOOGLE_API_KEY`
   - Save

### Option B: Using Azure CLI Commands

```powershell
# 1. Create resource group
az group create --name honest-stylist-rg --location eastus

# 2. Create container registry
az acr create --resource-group honest-stylist-rg --name honeststylist --sku Basic

# 3. Build and push image
docker build -t honeststylist:latest .
docker tag honeststylist:latest honeststylist.azurecr.io/honeststylist:latest
docker push honeststylist.azurecr.io/honeststylist:latest

# 4. Create App Service Plan
az appservice plan create --name honest-stylist-plan --resource-group honest-stylist-rg --sku B1 --is-linux

# 5. Create Web App
az webapp create --resource-group honest-stylist-rg --plan honest-stylist-plan --name honest-stylist --deployment-container-image-name honeststylist.azurecr.io/honeststylist:latest

# 6. Configure container
az webapp config container set --name honest-stylist --resource-group honest-stylist-rg --docker-custom-image-name honeststylist.azurecr.io/honeststylist:latest --docker-registry-server-url https://honeststylist.azurecr.io --docker-registry-server-user <username> --docker-registry-server-password <password>

# 7. Set environment variables
az webapp config appsettings set --resource-group honest-stylist-rg --name honest-stylist --settings GOOGLE_API_KEY="your-key" WEBSITES_PORT=8000
```

### Option C: Using ARM Template

```powershell
# Update azuredeploy.parameters.json with your settings
# Then deploy:
az deployment group create `
  --resource-group honest-stylist-rg `
  --template-file azuredeploy.json `
  --parameters azuredeploy.parameters.json
```

---

## After Deployment

### Access Your App
```
https://honest-stylist.azurewebsites.net
```

### Monitor Logs
```powershell
az webapp log tail -g honest-stylist-rg -n honest-stylist
```

### Restart App
```powershell
az webapp restart -g honest-stylist-rg -n honest-stylist
```

### Scale Up (if needed)
```powershell
az appservice plan update -g honest-stylist-rg -n honest-stylist-plan --sku S1
```

### Delete Everything (cleanup)
```powershell
az group delete -n honest-stylist-rg --yes
```

---

## Troubleshooting

### ❌ App won't start
```powershell
# Check logs
az webapp log tail -g honest-stylist-rg -n honest-stylist

# Restart
az webapp restart -g honest-stylist-rg -n honest-stylist

# Verify settings
az webapp config appsettings list -g honest-stylist-rg -n honest-stylist
```

### ❌ Docker login fails
```powershell
# Get credentials
az acr credential show --resource-group honest-stylist-rg --name honeststylist

# Try again with correct username/password
```

### ❌ Out of memory
```powershell
# Upgrade to B2 or S1
az appservice plan update -g honest-stylist-rg -n honest-stylist-plan --sku B2
```

### ❌ Image won't push
```powershell
# Ensure you're logged into Docker
docker login honeststylist.azurecr.io

# Re-tag and push
docker tag honeststylist:latest honeststylist.azurecr.io/honeststylist:latest
docker push honeststylist.azurecr.io/honeststylist:latest
```

---

## Configuration Reference

### Environment Variables
| Variable | Value | Required |
|----------|-------|----------|
| `GOOGLE_API_KEY` | Your API key | Yes (for AI features) |
| `WEBSITES_PORT` | 8000 | Yes |
| `STREAMLIT_SERVER_HEADLESS` | true | Yes |
| `PYTHONUNBUFFERED` | 1 | Optional |

### Service Tiers & Pricing
| Tier | Cost/Month | CPU | Memory | Use Case |
|------|-----------|-----|--------|----------|
| B1 | ~$13 | 1 core | 1.75GB | Development/Testing |
| B2 | ~$27 | 2 cores | 3.5GB | Small production |
| S1 | ~$65 | 1 core | 1.75GB | Production |
| S2 | ~$130 | 2 cores | 3.5GB | Medium production |

---

## CI/CD with GitHub Actions

1. Fork repo to GitHub
2. Add secrets:
   - `AZURE_CREDENTIALS`
   - `GOOGLE_API_KEY`
3. Push to `main` branch
4. GitHub Actions auto-deploys! 🚀

See `azure-pipelines.yml` for pipeline configuration.

---

## Support Links

- [Azure CLI Documentation](https://learn.microsoft.com/en-us/cli/azure/)
- [Azure App Service](https://azure.microsoft.com/en-us/services/app-service/)
- [Docker Documentation](https://docs.docker.com/)
- [Streamlit Deployment Guide](https://docs.streamlit.io/deploy)

---

**Happy Deploying! 🎉**
