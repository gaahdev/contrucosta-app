# 📱 Compilação Local de APK - Guia Rápido

## ⚡ Opção 1: Script Automático (Recomendado)

### Linux/macOS
```bash
chmod +x build-apk-auto.sh
./build-apk-auto.sh debug   # ou release
```

### Windows (PowerShell)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\build-apk-windows.ps1 -BuildType debug   # ou release
```

**O script vai:**
- ✅ Verificar Java 17 e Android SDK
- ✅ Instalar dependências (yarn)
- ✅ Build web (React)
- ✅ Copiar assets para Android (Capacitor)
- ✅ Compilar APK
- ✅ Gerar `.apk` na raiz do projeto

---

## 🛠 Opção 2: Passo a Passo Manual

### 1. Instalar JDK 17

**Linux:**
```bash
sudo apt update && sudo apt install -y openjdk-17-jdk
```

**macOS:**
```bash
brew install openjdk@17
```

**Windows:**
Baixe de https://adoptium.net/temurin/releases/?version=17

### 2. Instalar Android SDK

**Recomendado:** Android Studio de https://developer.android.com/studio
- Instale SDK Platform 34
- Instale Build-Tools 34

**Ou linha de comando:**
```bash
# Linux/Mac
mkdir -p ~/Android/Sdk
cd ~/Downloads
wget https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip
unzip commandlinetools-linux-9477386_latest.zip
mv cmdline-tools ~/Android/Sdk/cmdline-tools/latest
echo 'export ANDROID_HOME=$HOME/Android/Sdk' >> ~/.bashrc
source ~/.bashrc
sdkmanager --install "platforms;android-34" "build-tools;34.0.0"
```

### 3. Configurar Variáveis de Ambiente

**Linux/Mac:**
```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

**Windows:**
```batch
setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-17.0.x"
setx ANDROID_HOME "%USERPROFILE%\Android\Sdk"
REM Feche e reabra o terminal
```

### 4. Compilar

```bash
cd frontend
yarn install
yarn build
npx cap copy android

cd android
chmod +x gradlew  # Linux/Mac apenas

./gradlew assembleDebug
# ou Windows: gradlew.bat assembleDebug
```

**APK estará em:**
```
frontend/android/app/build/outputs/apk/debug/app-debug.apk
```

---

## 🔐 Compilar APK Release (Para Loja)

### 1. Criar Keystore
```bash
cd frontend/android

keytool -genkey -v -keystore contrucosta-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias contrucosta-key
```

### 2. Configurar Assinatura

Crie/edite `frontend/android/gradle.properties`:
```properties
CONTRUCOSTA_RELEASE_STORE_FILE=./contrucosta-release-key.jks
CONTRUCOSTA_RELEASE_STORE_PASSWORD=sua_senha
CONTRUCOSTA_RELEASE_KEY_ALIAS=contrucosta-key
CONTRUCOSTA_RELEASE_KEY_PASSWORD=sua_senha
```

### 3. Compilar Release
```bash
./gradlew assembleRelease
```

**APK Release estará em:**
```
frontend/android/app/build/outputs/apk/release/app-release.apk
```

---

## 📚 Documentação Completa

Veja [GUIA_COMPILACAO_LOCAL.md](GUIA_COMPILACAO_LOCAL.md) para detalhes completos, troubleshooting e dicas avançadas.

---

## 🐛 Problemas Comuns

| Erro | Solução |
|------|---------|
| `SDK location not found` | Crie `frontend/android/local.properties` com `sdk.dir=/caminho/para/sdk` |
| `java: command not found` | Instale JDK 17 e configure `JAVA_HOME` |
| `ANDROID_HOME not set` | Configure a variável de ambiente |
| `Unsupported class file major version` | Use JDK 17, não 21+ |
| `gradlew permission denied` | Execute `chmod +x gradlew` |

---

## ✨ Pronto!

Após compilar, você terá:
- 📱 `app-debug.apk` → para teste em dispositivos
- 📦 `app-release.apk` → para enviar à Play Store

**Testar no seu dispositivo:**
```bash
adb install -r app-debug.apk
```

---

**Precisa de ajuda?** Veja [GUIA_COMPILACAO_LOCAL.md](GUIA_COMPILACAO_LOCAL.md) para documentação completa.
