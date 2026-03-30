# verify_environment.ps1

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "VERIFICATION ENVIRONNEMENT LOCAL" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$checks = @()

# 1. Node.js
Write-Host "1. Node.js..." -NoNewline
try {
    $nodeVersion = node --version 2>&1
    Write-Host " OK $nodeVersion" -ForegroundColor Green
    $checks += $true
} catch {
    Write-Host " Non installe" -ForegroundColor Red
    Write-Host "   Telecharger: https://nodejs.org/" -ForegroundColor Yellow
    $checks += $false
}

# 2. NPM
Write-Host "2. NPM..." -NoNewline
try {
    $npmVersion = npm --version 2>&1
    Write-Host " OK $npmVersion" -ForegroundColor Green
    $checks += $true
} catch {
    Write-Host " Non installe" -ForegroundColor Red
    $checks += $false
}

# 3. Python
Write-Host "3. Python..." -NoNewline
try {
    $pythonVersion = python --version 2>&1
    Write-Host " OK $pythonVersion" -ForegroundColor Green
    $checks += $true
} catch {
    Write-Host " Non installe" -ForegroundColor Red
    $checks += $false
}

# 4. Environnement virtuel Python
Write-Host "4. Environnement virtuel..." -NoNewline
if (Test-Path "venv") {
    Write-Host " OK trouve" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host " Non trouve (sera cree)" -ForegroundColor Yellow
    $checks += $true
}

# 5. Fichier app.py actuel
Write-Host "5. app.py actuel..." -NoNewline
if (Test-Path "app.py") {
    Write-Host " OK trouve" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host " Non trouve" -ForegroundColor Red
    $checks += $false
}

# 6. Service account JSON
Write-Host "6. ga4-service-account.json..." -NoNewline
if (Test-Path "ga4-service-account.json") {
    Write-Host " OK trouve" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host " Non trouve" -ForegroundColor Red
    Write-Host "   Telecharger depuis GCP Console ou Secret Manager" -ForegroundColor Yellow
    $checks += $false
}

# 7. Authentification gcloud
Write-Host "7. Authentification gcloud..." -NoNewline
try {
    $account = gcloud config get-value account 2>&1
    if ($account -and $account -ne "(unset)") {
        Write-Host " OK $account" -ForegroundColor Green
        $checks += $true
    } else {
        Write-Host " Non configure" -ForegroundColor Yellow
        Write-Host "   Executer: gcloud auth application-default login" -ForegroundColor Yellow
        $checks += $false
    }
} catch {
    Write-Host " gcloud non installe" -ForegroundColor Red
    $checks += $false
}

# Resume
$allGood = -not ($checks -contains $false)

Write-Host ""
Write-Host "============================================================" -ForegroundColor Gray

if ($allGood) {
    Write-Host "Environnement pret !" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Certains prerequis sont manquants" -ForegroundColor Yellow
    Write-Host "Corrigez les problemes ci-dessus avant de continuer" -ForegroundColor Yellow
    exit 1
}
