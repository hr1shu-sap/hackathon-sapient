# 🚀 Deploy Honest Stylist to Azure - NO Installation Required

## ✅ What You Need
- Azure Account (free or existing)
- Browser (Chrome, Edge, Firefox)
- Your Google API key (optional, for AI features)

**That's it! No installations, no admin access needed.**

---

## 📋 COMPLETE STEP-BY-STEP GUIDE

### **STEP 1: Go to Azure Portal**
Open in browser: https://portal.azure.com

(If you don't have account, create free one at https://azure.microsoft.com/en-us/free/)

---

### **STEP 2: Open Cloud Shell**
1. In Azure Portal, click **">_"** icon (top right corner)
2. Select **PowerShell** (not Bash)
3. If first time, click **"Create storage"** and wait

✅ You now have a terminal in your browser - no installation!

---

### **STEP 3: Get Your Code**
Copy and paste this in Cloud Shell:

```powershell
git clone https://github.com/hr1shu-sap/hackathon-sapient.git
cd hackathon-sapient/"Honest Stylist"
ls
```

✅ This downloads your project code and navigates to the correct directory (where Dockerfile is)

---

### **STEP 4: Register Container Registry Provider**
Copy and paste this FIRST:

```powershell
az provider register --namespace Microsoft.ContainerRegistry
```

⏳ Wait 1-2 minutes (shows "Registering...")

---

### **STEP 5: Create Resource Group**
Copy and paste:

```powershell
az group create --name honest-stylist-rg --location eastus
```

✅ This creates a folder for all your resources

---

### **STEP 6: Create Container Registry**
Copy and paste:

```powershell
az acr create --resource-group honest-stylist-rg --name honeststylist$RANDOM --sku Basic --admin-enabled true
```

⚠️ **Important:** Save the registry name shown (will be something like `honeststylist12345`)

---

### **STEP 7: Verify You're in Correct Directory**
Make sure you see the Dockerfile:

```powershell
pwd
ls Dockerfile
```

✅ Should show the Dockerfile path

---
### **STEP 9: Create App Service Plan**
Copy and paste:

```powershell
az appservice plan create --name honest-stylist-plan --resource-group honest-stylist-rg --sku B1 --is-linux
```

✅ This creates the compute tier for your app

---

### **STEP 10: Create Web App**
Replace `YOUR-REGISTRY-NAME` with your registry name:
Copy and paste:

```powershell
az appservice plan create --name honest-stylist-plan --resource-group honest-stylist-rg --sku B1 --is-linux
```

✅ This creates the compute tier for your app

---

### **STEP 9: Create Web App**
Replace `YOUR-REGISTRY-NAME` with your registry name:

```powershell
az webapp create --resource-group honest-stylist-rg --plan honest-stylist-plan --name honest-stylist-app --deployment-container-image-name YOUR-REGISTRY-NAME.azurecr.io/honeststylist:latest
```

⏳ Wait 2-3 minutes

---

### **STEP 10: Configure Container Settings**
Replace `YOUR-REGISTRY-NAME` with your registry name:

```powershell
# Get registry password
$password = az acr credential show --resource-group honest-stylist-rg --name YOUR-REGISTRY-NAME --query "passwords[0].value" -o tsv

# Configure app
az webapp config container set --name honest-stylist-app --resource-group honest-stylist-rg --docker-custom-image-name YOUR-REGISTRY-NAME.azurecr.io/honeststylist:latest --docker-registry-server-url https://YOUR-REGISTRY-NAME.azurecr.io --docker-registry-server-user YOUR-REGISTRY-NAME --docker-registry-server-password $password
```

✅ Connects app to your Docker image

---

### **STEP 11: Set Environment Variables**
Replace `your-google-api-key` (or leave blank if you don't have one):

```powershell
az webapp config appsettings set --resource-group honest-stylist-rg --name honest-stylist-app --settings GOOGLE_API_KEY="your-google-api-key" WEBSITES_PORT=8000 STREAMLIT_SERVER_HEADLESS=true PYTHONUNBUFFERED=1
```

✅ Sets configuration for your app

---

### **STEP 12: Get Your App URL**
Copy and paste:

```powershell
az webapp show --resource-group honest-stylist-rg --name honest-stylist-app --query defaultHostName -o tsv
```

✅ Shows your app URL (copy it)

---

### **STEP 13: Open Your App**
1. Copy the URL from Step 12
2. Add `https://` at the beginning
3. Open in browser
4. **Wait 2-3 minutes for first startup**
5. 🎉 Your app is live!

---

## 🔥 SUPER FAST - All Commands Together

If you want to run everything at once, use this:

**First, set your registry name:**
```powershell
$registry = "honeststylist$RANDOM"
$rg = "honest-stylist-rg"
$app = "honest-stylist-app"
$location = "eastus"
$googleKey = "your-google-api-key-here"
```

**Then copy and paste entire block:**
```powershell
# Create resources
az group create --name $rg --location $location
az acr create --resource-group $rg --name $registry --sku Basic --admin-enabled true

# Build image
Write-Host "Building Docker image... (takes 3-5 min)"
az acr build --registry $registry --image honeststylist:latest --file Dockerfile .

# Create app service
az appservice plan create --name "$app-plan" --resource-group $rg --sku B1 --is-linux
az webapp create --resource-group $rg --plan "$app-plan" --name $app --deployment-container-image-name "$registry.azurecr.io/honeststylist:latest"

# Get password and configure
$password = az acr credential show --resource-group $rg --name $registry --query "passwords[0].value" -o tsv
az webapp config container set --name $app --resource-group $rg --docker-custom-image-name "$registry.azurecr.io/honeststylist:latest" --docker-registry-server-url "https://$registry.azurecr.io" --docker-registry-server-user $registry --docker-registry-server-password $password

# Set environment variables
az webapp config appsettings set --resource-group $rg --name $app --settings GOOGLE_API_KEY="$googleKey" WEBSITES_PORT=8000 STREAMLIT_SERVER_HEADLESS=true PYTHONUNBUFFERED=1

# Show app URL
Write-Host "Deployment complete!"
$url = az webapp show --resource-group $rg --name $app --query defaultHostName -o tsv
Write-Host "Your app URL: https://$url"
Write-Host "Wait 2-3 minutes, then open the URL in browser"
```

---

## 📊 Timeline
| Step | Time |
|------|------|
| Steps 1-3 | 1 min |
| Step 4 (Register provider) | 2 min |
| Step 5-6 | 1 min |
| Step 7 (Build image) | 5 min |
| Steps 8-11 | 3 min |
| **Total** | **~12 minutes** |

---

## ✅ Check Deployment Status

### View logs:
```powershell
az webapp log tail --resource-group honest-stylist-rg --name honest-stylist-app
```

### Restart app:
```powershell
az webapp restart --resource-group honest-stylist-rg --name honest-stylist-app
```

### Delete everything (cleanup):
```powershell
az group delete --name honest-stylist-rg --yes
```

---

## 🎯 Google API Key (Optional)

If you want AI features:
1. Go to https://aistudio.google.com/app/apikey
2. Click **"Create API key in new project"**
3. Copy the key
4. Use it in Step 10 above

---

## 💡 Tips

✅ **Copy commands one by one** - paste into Cloud Shell and wait for each to complete
✅ **Save your registry name** - you'll need it multiple times
✅ **First startup takes 2-3 minutes** - be patient!
✅ **Check logs if app doesn't load** - use `az webapp log tail` command

---

## ❌ Troubleshooting

### Command not found error?
→ Make sure you're in Cloud Shell (top right ">_" button)
→ Select PowerShell when prompted

### Build fails?
→ Check Dockerfile exists: `ls Dockerfile`
→ Make sure you're in correct directory

### App won't start?
→ Check logs: `az webapp log tail -g honest-stylist-rg -n honest-stylist-app`
→ Wait 3-5 minutes for startup
→ Restart: `az webapp restart -g honest-stylist-rg -n honest-stylist-app`

### Out of memory?
→ Upgrade plan: `az appservice plan update -g honest-stylist-rg -n honest-stylist-app-plan --sku B2`

---

## 🎉 YOU'RE DONE!

Your Honest Stylist app is now live on Azure with **zero installation required**!

**App URL format:** `https://honest-stylist-app.azurewebsites.net`
