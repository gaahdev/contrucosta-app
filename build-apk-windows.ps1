# ==========================================
# Script de Compilação de APK - Contrucosta (Windows)
# ==========================================
# Uso: .\build-apk.ps1 -BuildType debug
# Exemplo: .\build-apk.ps1 -BuildType debug
# ==========================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("debug", "release")]
    [string]$BuildType = "debug"
)

# Configurações
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $ScriptDir "frontend"
$AndroidDir = Join-Path $FrontendDir "android"

# Funções
function Write-Header {
    Write-Host "`n======================================" -ForegroundColor Cyan
    Write-Host $args[0] -ForegroundColor Cyan
    Write-Host "======================================`n" -ForegroundColor Cyan
}

function Write-Success {
    Write-Host "✅ $($args[0])" -ForegroundColor Green
}

function Write-Error {
    Write-Host "❌ $($args[0])" -ForegroundColor Red
}

function Write-Warning {
    Write-Host "⚠️  $($args[0])" -ForegroundColor Yellow
}

function Write-Info {
    Write-Host "ℹ️  $($args[0])" -ForegroundColor Cyan
}

function Test-Command {
    param([string]$Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            return $true
        }
    }
    catch {
        return $false
    }
}

# ==========================================
# Início do Script
# ==========================================

Clear-Host
Write-Header "🚀 Compilador de APK - Contrucosta App (Windows)"

Write-Info "Tipo de build: $BuildType"
Write-Info "Diretório: $ScriptDir"

# ==========================================
# Verificar Pré-requisitos
# ==========================================

Write-Header "📋 Verificando Pré-requisitos"

# Java
if (-not (Test-Command "java")) {
    Write-Error "Java não está instalado ou não está no PATH"
    Write-Info "Instale de: https://adoptium.net/temurin/releases/?version=17"
    exit 1
}
Write-Success "Java encontrado"
java -version 2>&1 | Select-Object -First 1

# Node/npm
if (-not (Test-Command "npm")) {
    Write-Error "npm não está instalado"
    Write-Info "Instale de: https://nodejs.org/"
    exit 1
}
Write-Success "npm encontrado"

# Yarn
if (-not (Test-Command "yarn")) {
    Write-Warning "yarn não está instalado, tentando instalar globalmente..."
    npm install -g yarn
}
Write-Success "yarn encontrado"

# Android Home
if (-not $env:ANDROID_HOME) {
    if (Test-Path "$env:USERPROFILE\Android\Sdk") {
        $env:ANDROID_HOME = "$env:USERPROFILE\Android\Sdk"
        Write-Success "ANDROID_HOME configurado automaticamente"
    }
    elseif (Test-Path "C:\Android\sdk") {
        $env:ANDROID_HOME = "C:\Android\sdk"
        Write-Success "ANDROID_HOME configurado automaticamente"
    }
    else {
        Write-Error "Android SDK não encontrado"
        Write-Info "Instale Android Studio ou configure ANDROID_HOME manualmente"
        exit 1
    }
}
Write-Success "ANDROID_HOME: $env:ANDROID_HOME"

# Verificar SDK Platform
$platformFound = Get-ChildItem "$env:ANDROID_HOME\platforms" -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "android-\d+" }
if (-not $platformFound) {
    Write-Error "Android SDK Platform não encontrado"
    Write-Info "Instale via Android Studio: Tools > SDK Manager > API Level 34"
    exit 1
}
Write-Success "Android SDK Platform encontrado"

# Verificar Build-Tools
$buildToolsFound = Get-ChildItem "$env:ANDROID_HOME\build-tools" -ErrorAction SilentlyContinue | Where-Object { $_.PSIsContainer }
if (-not $buildToolsFound) {
    Write-Error "Android SDK Build-Tools não encontrado"
    Write-Info "Instale via Android Studio: Tools > SDK Manager > Build Tools"
    exit 1
}
Write-Success "Android SDK Build-Tools encontrado"

# ==========================================
# Instalação de Dependências
# ==========================================

Write-Header "📦 Instalando Dependências"

if (-not (Test-Path "$FrontendDir\node_modules")) {
    Write-Info "Instalando packages npm/yarn..."
    Push-Location $FrontendDir
    yarn install
    Pop-Location
    Write-Success "Dependências instaladas"
}
else {
    Write-Success "Dependências já instaladas"
}

# ==========================================
# Build Web (React)
# ==========================================

Write-Header "🌐 Compilando Web (React)"

if (Test-Path "$FrontendDir\build") {
    Write-Info "Limpando build anterior..."
    Remove-Item "$FrontendDir\build" -Recurse -Force
}

Push-Location $FrontendDir
Write-Info "Executando: yarn build"
yarn build
Pop-Location

if (-not (Test-Path "$FrontendDir\build\index.html")) {
    Write-Error "Build web falhou"
    exit 1
}

$buildSize = (Get-ChildItem $FrontendDir\build -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Success "Build web concluído (${buildSize:F2} MB)"

# ==========================================
# Capacitor Copy
# ==========================================

Write-Header "⚙️  Copiando Assets para Android"

Push-Location $FrontendDir
Write-Info "Executando: npx cap copy android"
npx cap copy android
Pop-Location

if (-not (Test-Path "$AndroidDir\app\src\main\assets\public\index.html")) {
    Write-Error "Cópia de assets falhou"
    exit 1
}

Write-Success "Assets copiados com sucesso"

# ==========================================
# Gradle Build
# ==========================================

Write-Header "🔨 Compilando APK ($BuildType)"

Push-Location $AndroidDir

# Limpar build anterior
if ($BuildType -eq "release") {
    Write-Info "Limpando builds anteriores..."
    .\gradlew.bat clean
}

# Verificar keystore para release
if ($BuildType -eq "release") {
    if (-not (Test-Path "$AndroidDir\contrucosta-release-key.jks")) {
        Write-Error "Keystore não encontrado: contrucosta-release-key.jks"
        Write-Info "Para criar um keystore, execute:"
        Write-Info '  keytool -genkey -v -keystore contrucosta-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias contrucosta-key'
        exit 1
    }
    Write-Success "Keystore encontrado"
}

# Executar gradle
Write-Info "Executando gradle assemble${BuildType}..."
$BuildTypeCapitalized = $BuildType.Substring(0,1).ToUpper() + $BuildType.Substring(1)
.\gradlew.bat "assemble$BuildTypeCapitalized" --no-daemon

Pop-Location

# ==========================================
# Verificar Output
# ==========================================

Write-Header "📍 Verificando APK Gerada"

if ($BuildType -eq "debug") {
    $ApkPath = "$AndroidDir\app\build\outputs\apk\debug\app-debug.apk"
    $ApkName = "app-debug.apk"
}
else {
    $ApkPath = "$AndroidDir\app\build\outputs\apk\release\app-release.apk"
    $ApkName = "app-release.apk"
}

if (Test-Path $ApkPath) {
    $ApkSize = (Get-Item $ApkPath).Length / 1MB
    Write-Success "APK compilada com sucesso!"
    Write-Host ""
    Write-Info "📊 Detalhes:"
    Write-Host "   Nome: $ApkName"
    Write-Host "   Tamanho: $($ApkSize:F2) MB"
    Write-Host "   Localização: $ApkPath"
    Write-Host ""
    
    # Copiar para raiz
    Copy-Item $ApkPath "$ScriptDir\$ApkName" -Force
    Write-Success "APK copiada para: $ScriptDir\$ApkName"
}
else {
    Write-Error "APK não foi gerada"
    Write-Info "Verifique os erros acima"
    exit 1
}

# ==========================================
# Resumo Final
# ==========================================

Write-Header "✨ Compilação Concluída!"

Write-Host "Próximas etapas:" -ForegroundColor Green
Write-Host ""
Write-Host "1. " -ForegroundColor Yellow -NoNewline
Write-Host "Testar em dispositivo:"
Write-Host "   adb install -r '$ScriptDir\$ApkName'"
Write-Host ""
Write-Host "2. " -ForegroundColor Yellow -NoNewline
Write-Host "Enviar para teste:"
Write-Host "   Copie '$ApkName' para seu dispositivo ou serviço de entrega"
Write-Host ""
Write-Host "3. " -ForegroundColor Yellow -NoNewline
Write-Host "Fazer upload na Play Store (release):"
Write-Host "   Use '$ApkName' no Google Play Console"
Write-Host ""

Write-Success "Tudo pronto! 🎉"
