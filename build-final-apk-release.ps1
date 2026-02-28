param(
    [string]$AndroidHome = "$env:USERPROFILE\AppData\Local\Android\Sdk"
)

$ErrorActionPreference = "Stop"

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Ok($msg) { Write-Host "✅ $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "❌ $msg" -ForegroundColor Red; exit 1 }

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontend = Join-Path $root "frontend"
$android = Join-Path $frontend "android"

if (-not (Test-Path $frontend)) { Fail "Pasta frontend não encontrada em $frontend" }
if (-not (Test-Path $android)) { Fail "Pasta android não encontrada em $android" }

Step "Preparando JDK 17 portátil"
$jdkRoot = Join-Path $env:USERPROFILE ".contrucosta\jdks"
$zipPath = Join-Path $jdkRoot "temurin17.zip"
New-Item -Path $jdkRoot -ItemType Directory -Force | Out-Null

$jdkDir = Get-ChildItem $jdkRoot -Directory -Filter "jdk-17*" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $jdkDir) {
    $url = "https://github.com/adoptium/temurin17-binaries/releases/latest/download/OpenJDK17U-jdk_x64_windows_hotspot.zip"
    Write-Host "Baixando JDK 17 portátil..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $url -OutFile $zipPath
    Expand-Archive -Path $zipPath -DestinationPath $jdkRoot -Force
    $jdkDir = Get-ChildItem $jdkRoot -Directory -Filter "jdk-17*" | Select-Object -First 1
}
if (-not $jdkDir) { Fail "Não foi possível preparar o JDK 17 portátil" }

$env:JAVA_HOME = $jdkDir.FullName
$env:Path = "$($env:JAVA_HOME)\bin;$env:Path"
Ok "JAVA_HOME = $($env:JAVA_HOME)"

Step "Validando Android SDK"
if (-not (Test-Path $AndroidHome)) { Fail "ANDROID_HOME não encontrado em: $AndroidHome" }
$env:ANDROID_HOME = $AndroidHome
$env:ANDROID_SDK_ROOT = $AndroidHome
Ok "ANDROID_HOME = $AndroidHome"

if (-not (Test-Path (Join-Path $AndroidHome "platforms"))) { Fail "SDK sem platforms (instale via Android Studio > SDK Manager)" }
if (-not (Test-Path (Join-Path $AndroidHome "build-tools"))) { Fail "SDK sem build-tools (instale via Android Studio > SDK Manager)" }

Step "Instalando dependências frontend"
if (-not (Get-Command yarn -ErrorAction SilentlyContinue)) {
    Warn "Yarn não encontrado. Instalando com npm -g yarn..."
    npm install -g yarn
}
Push-Location $frontend
yarn install --frozen-lockfile

Step "Build web"
yarn build

Step "Sincronizando Capacitor"
npx cap sync android
Pop-Location

Step "Compilando APK Release"
Push-Location $android
.\gradlew.bat clean assembleRelease --no-daemon
Pop-Location

$apkReleaseUnsigned = Join-Path $android "app\build\outputs\apk\release\app-release-unsigned.apk"
$apkRelease = Join-Path $android "app\build\outputs\apk\release\app-release.apk"

Step "Resultado"
if (Test-Path $apkRelease) {
    Copy-Item $apkRelease (Join-Path $root "app-release.apk") -Force
    Ok "APK release gerado: $apkRelease"
    Ok "Cópia na raiz: $(Join-Path $root "app-release.apk")"
    exit 0
}

if (Test-Path $apkReleaseUnsigned) {
    Copy-Item $apkReleaseUnsigned (Join-Path $root "app-release-unsigned.apk") -Force
    Warn "Foi gerado APK unsigned: $apkReleaseUnsigned"
    Warn "Cópia na raiz: $(Join-Path $root "app-release-unsigned.apk")"
    Warn "Para distribuição final (Play Store), configure assinatura no Gradle/keystore."
    exit 0
}

Fail "Nenhum APK release foi gerado."
