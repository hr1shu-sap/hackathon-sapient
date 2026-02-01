# Honest Stylist - Pre-Deployment Verification Script (PowerShell)

param(
    [switch]$Verbose = $false
)

# Colors
$Color_Success = "Green"
$Color_Error = "Red"
$Color_Warning = "Yellow"

function Check-Tool {
    param(
        [string]$ToolName,
        [string]$Command,
        [string]$MinVersion = ""
    )
    
    try {
        $output = Invoke-Expression $Command 2>$null
        Write-Host "✓ $ToolName found" -ForegroundColor $Color_Success
        if ($Verbose) {
            Write-Host "  $output" -ForegroundColor Gray
        }
        return $true
    } catch {
        Write-Host "✗ $ToolName not found" -ForegroundColor $Color_Error
        return $false
    }
}

function Check-File {
    param(
        [string]$FilePath,
        [string]$Description
    )
    
    if (Test-Path $FilePath) {
        Write-Host "✓ $Description" -ForegroundColor $Color_Success
        return $true
    } else {
        Write-Host "✗ $Description - Missing: $FilePath" -ForegroundColor $Color_Error
        return $false
    }
}

Write-Host "`n=== Honest Stylist - Pre-Deployment Verification ===" -ForegroundColor Cyan
Write-Host "Checking prerequisites for Azure deployment...`n"

$allGood = $true

# Check Tools
Write-Host "Checking Required Tools:" -ForegroundColor Yellow
$allGood = (Check-Tool "PowerShell" '$PSVersionTable.PSVersion.Major' -and $allGood) -or $allGood
$allGood = (Check-Tool "Azure CLI" 'az --version' -and $allGood) -or $allGood
$allGood = (Check-Tool "Docker" 'docker --version' -and $allGood) -or $allGood
$allGood = (Check-Tool "Git" 'git --version' -and $allGood) -or $allGood

# Check Deployment Files
Write-Host "`nChecking Deployment Files:" -ForegroundColor Yellow
$allGood = (Check-File ".\Dockerfile" "Dockerfile" -and $allGood) -or $allGood
$allGood = (Check-File ".\deploy-azure.ps1" "PowerShell deployment script" -and $allGood) -or $allGood
$allGood = (Check-File ".\azuredeploy.json" "ARM template" -and $allGood) -or $allGood
$allGood = (Check-File ".\azure-pipelines.yml" "CI/CD pipeline" -and $allGood) -or $allGood
$allGood = (Check-File ".\AZURE_QUICKSTART.md" "Quick start guide" -and $allGood) -or $allGood

# Check Project Files
Write-Host "`nChecking Project Files:" -ForegroundColor Yellow
$allGood = (Check-File ".\honest_stylist\requirements.txt" "Python requirements" -and $allGood) -or $allGood
$allGood = (Check-File ".\honest_stylist\app\app.py" "Streamlit app" -and $allGood) -or $allGood
$allGood = (Check-File ".\honest_stylist\README.md" "README" -and $allGood) -or $allGood

# Check Azure CLI login
Write-Host "`nChecking Azure CLI Status:" -ForegroundColor Yellow
try {
    $account = az account show --query user.name -o tsv 2>$null
    if ($account) {
        Write-Host "✓ Azure CLI logged in as: $account" -ForegroundColor $Color_Success
    } else {
        Write-Host "⚠ Not logged in to Azure (you'll be prompted during deployment)" -ForegroundColor $Color_Warning
    }
} catch {
    Write-Host "⚠ Could not check Azure login status (will prompt during deployment)" -ForegroundColor $Color_Warning
}

# Summary
Write-Host "`n=== Summary ===" -ForegroundColor Cyan

if ($allGood) {
    Write-Host "✓ All checks passed! Ready to deploy." -ForegroundColor $Color_Success
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. Get your Google API key from: https://aistudio.google.com/app/apikey"
    Write-Host "  2. Run: .\deploy-azure.ps1 -GoogleApiKey 'your-api-key'"
    Write-Host "  3. Or read AZURE_QUICKSTART.md for more options"
} else {
    Write-Host "✗ Some checks failed. Please install missing tools and try again." -ForegroundColor $Color_Error
    Write-Host "`nMissing tools:" -ForegroundColor Yellow
    
    if (-not (Check-Tool "Azure CLI" 'az --version' 2>$null)) {
        Write-Host "  - Azure CLI: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli"
    }
    if (-not (Check-Tool "Docker" 'docker --version' 2>$null)) {
        Write-Host "  - Docker: https://www.docker.com/products/docker-desktop"
    }
}

Write-Host "`n"
