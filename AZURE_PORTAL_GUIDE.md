# 🎯 Azure Portal Deployment Guide - No CLI/Docker Required

## Step 1: Prepare Your Files
✅ **Already done** - Your Dockerfile is ready in the project root

## Step 2: Create Azure Account
1. Go to https://azure.microsoft.com/en-us/free/
2. Sign up for free account ($200 credit for 30 days)
3. Once verified, go to https://portal.azure.com/

---

## DEPLOYMENT STEPS (Via Azure Portal)

### **STEP 1: Create Resource Group**
1. In Azure Portal, search for **"Resource groups"**
2. Click **"+ Create"**
3. Fill in:
   - **Subscription:** (default)
   - **Resource group:** `honest-stylist-rg`
   - **Region:** `East US`
4. Click **"Review + Create"** → **"Create"**
⏳ Wait 30 seconds

---

### **STEP 2: Create Container Registry**
1. Search for **"Container registries"** in portal
2. Click **"+ Create"**
3. Fill in:
   - **Resource group:** Select `honest-stylist-rg`
   - **Registry name:** `honeststylist` (must be unique)
   - **Location:** `East US`
   - **SKU:** `Basic`
4. Click **"Review + Create"** → **"Create"**
⏳ Wait 1-2 minutes

---

### **STEP 3: Enable Admin Access**
1. Go to your created Container Registry (search: `honeststylist`)
2. Left sidebar → **"Access keys"**
3. Toggle **"Admin user"** to **"Enabled"**
4. Copy and save:
   - **Username**
   - **Password** (either one)

---

### **STEP 4: Create App Service Plan**
1. Search for **"App Service plans"** in portal
2. Click **"+ Create"**
3. Fill in:
   - **Resource group:** `honest-stylist-rg`
   - **Name:** `honest-stylist-plan`
   - **Operating System:** `Linux`
   - **Region:** `East US`
   - **Pricing tier:** `Basic B1` (click to select - costs ~$13/month)
4. Click **"Review + Create"** → **"Create"**
⏳ Wait 2-3 minutes

---

### **STEP 5: Create Web App**
1. Search for **"App Services"** in portal
2. Click **"+ Create"**
3. Fill in:
   - **Resource group:** `honest-stylist-rg`
   - **Name:** `honest-stylist` (becomes URL)
   - **Publish:** `Docker Container`
   - **Operating System:** `Linux`
   - **Region:** `East US`
   - **App Service Plan:** Select `honest-stylist-plan`
4. Click **"Next: Docker >"**

---

### **STEP 6: Configure Docker Settings**
1. Fill in Docker tab:
   - **Image Source:** `Azure Container Registry`
   - **Registry:** `honeststylist`
   - **Image:** Leave blank (we'll push manually)
   - **Tag:** `latest`
2. Click **"Review + Create"** → **"Create"**
⏳ Wait 3-5 minutes

---

### **STEP 7: Push Docker Image to Registry**

You have **3 options**:

#### **Option A: Use Azure Cloud Shell (EASIEST - No Installation)**
1. In Azure Portal top right, click **">_"** (Cloud Shell icon)
2. If prompted, click **"Create storage"** (one-time)
3. Copy and paste these commands one by one:

```bash
# Clone or prepare your code
cd /tmp
git clone https://github.com/hr1shu-sap/hackathon-sapient.git
cd hackathon-sapient/Honest\ Stylist

# Build image
az acr build --registry honeststylist --image honeststylist:latest --file Dockerfile .
```

#### **Option B: Manual Upload via Azure Portal**
1. Go to your Container Registry (search: `honeststylist`)
2. Left sidebar → **"Repositories"**
3. If no image, continue to Option C

#### **Option C: Use ACR Portal Build (Recommended)**
1. In Container Registry → **"Tasks"** (left sidebar)
2. Click **"+ Add"**
3. Configure:
   - **Task name:** `build-app`
   - **Trigger:** `Manual`
   - **Source:** URL to your Dockerfile
   - **Dockerfile:** `Dockerfile`
   - **Registry:** `honeststylist`
   - **Image:** `honeststylist:latest`
4. Click **"Create"** → **"Run"** (Wait 3-5 minutes)

---

### **STEP 8: Configure Web App to Use Image**
1. Go to your Web App (search: `honest-stylist`)
2. Left sidebar → **"Deployment Center"**
3. Configure:
   - **Registry:** `honeststylist`
   - **Image:** `honeststylist`
   - **Tag:** `latest`
   - **Startup Command:** Leave empty
4. Click **"Save"**
⏳ Wait 2-3 minutes for deployment

---

### **STEP 9: Set Environment Variables**
1. In Web App → Left sidebar → **"Configuration"** (under Settings)
2. Click **"+ New application setting"**
3. Add these one by one:

| Name | Value |
|------|-------|
| `GOOGLE_API_KEY` | `your-google-api-key-here` |
| `WEBSITES_PORT` | `8000` |
| `STREAMLIT_SERVER_HEADLESS` | `true` |
| `PYTHONUNBUFFERED` | `1` |

4. Click **"Save"** and confirm restart

---

### **STEP 10: Get Your App URL**
1. Go to Web App overview
2. Copy the **URL** (format: `https://honest-stylist.azurewebsites.net`)
3. Open in browser and wait 2-3 minutes for startup

---

## ✅ VERIFICATION

### Check if app is running:
1. Go to Web App → **"Activity log"** (left sidebar)
2. Should show recent activity

### Check logs:
1. Web App → **"Log stream"** (left sidebar)
2. Should show Streamlit startup messages

### Restart if needed:
1. Web App → Top menu → **"Restart"**

---

## 📝 QUICK REFERENCE - Portal Navigation

```
Azure Portal (portal.azure.com)
├── Resource groups → Select "honest-stylist-rg"
├── Container registries → Select "honeststylist"
│   └── Access keys (for credentials)
├── App Service plans → Select "honest-stylist-plan"
└── App Services → Select "honest-stylist"
    ├── Deployment Center (configure image)
    ├── Configuration (environment variables)
    ├── Log stream (view logs)
    └── Overview (get URL)
```

---

## 🔗 Google API Key Setup

1. Go to https://aistudio.google.com/app/apikey
2. Click **"Create API key"**
3. Copy the key
4. Paste in Web App Configuration → `GOOGLE_API_KEY`

---

## 💰 Cost Breakdown
- App Service B1: ~$13/month
- Container Registry Basic: ~$5/month
- **Total: ~$18/month**

---

## ❌ Troubleshooting

### App shows error page:
→ Check Configuration settings
→ Check Log stream for errors
→ Restart Web App

### Image won't deploy:
→ Verify image exists in Container Registry
→ Check Deployment Center settings
→ Retry the build

### Can't see logs:
→ Wait 5 minutes after creation
→ Check "Application Insights" is enabled

---

## 🎉 SUCCESS!
Once everything is set up, your app will be live at:
```
https://honest-stylist.azurewebsites.net
```
