# Instruções para Gerar APK - Contrucosta App

## ⚠️ Aviso
O APK **não pode ser compilado neste ambiente** porque não há Android SDK instalado. Compile no seu computador local seguindo os passos abaixo.

## 📋 Pré-requisitos

1. **Java 21+**
   - Download: https://www.oracle.com/java/technologies/downloads/
   - Ou via Homebrew (Mac): `brew install openjdk@21`

2. **Android SDK**
   - Instale Android Studio: https://developer.android.com/studio
   - Ou instale apenas Android SDK Command Line Tools

3. **Configure ANDROID_HOME**
   ```bash
   # Linux/Mac
   export ANDROID_HOME=~/Library/Android/sdk  # Mac
   export ANDROID_HOME=~/Android/Sdk          # Linux
   
   # Windows
   set ANDROID_HOME=C:\Users\%USERNAME%\AppData\Local\Android\sdk
   ```

## 🚀 Passos para Gerar o APK

### 1. Clone/Abra o Repositório
```bash
cd contrucosta-app/frontend/android
```

### 2. Execute o Build
```bash
# Debug APK
./gradlew assembleDebug

# Ou Release APK (recomendado para distribuição)
./gradlew assembleRelease
```

### 3. Localize o APK
```bash
# Debug
android/app/build/outputs/apk/debug/app-debug.apk

# Release
android/app/build/outputs/apk/release/app-release.apk
```

## 🔧 Usando o Script Automático (Mac/Linux)

```bash
cd contrucosta-app
chmod +x build-apk.sh
./build-apk.sh
```

## 📱 Instalar no Dispositivo

```bash
# Conecte o device e execute
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

## 🔗 Backend Configurado
- **URL**: https://territorial-shaylah-zetsu-0ec52e74.koyeb.app
- **Localização**: `frontend/.env`

Se precisar trocar, edite o arquivo `.env` e refaça o build.

## 🐛 Troubleshooting

### "SDK location not found"
```bash
echo "sdk.dir=/caminho/para/android-sdk" > android/local.properties
```

### "ANDROID_HOME not set"
```bash
export ANDROID_HOME=/caminho/para/android-sdk
```

### "Gradle version incompatible"
Versão Gradle foi atualizada para 8.11 (compatível com Java 21+).

---

**Suporte**: Veja [README.md](README.md) para mais informações.
