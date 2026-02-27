#!/bin/bash

# Script para compilar APK manualmente sem Gradle (usando Capacitor + assets web prontos)

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$PROJECT_DIR/frontend"
ANDROID_DIR="$FRONTEND_DIR/android"

echo "📦 Contrucosta App - Compilação APK"
echo "===================================="
echo ""

# 1. Sincronizar assets web
echo "1️⃣  Sincronizando assets web..."
cd "$FRONTEND_DIR"
npx cap sync android
echo "✅ Assets sincronizados"
echo ""

# 2. Verificar build
echo "2️⃣  Verificando build React..."
if [ ! -d "$FRONTEND_DIR/build" ]; then
    echo "❌ Build não encontrado. Executando yarn build..."
    yarn build
fi
ls -lh "$FRONTEND_DIR/build/index.html" || { echo "❌ Falha no build"; exit 1; }
echo "✅ Build React pronto"
echo ""

# 3. Copiar assets para Android
echo "3️⃣  Copiando assets..."
mkdir -p "$ANDROID_DIR/app/src/main/assets/public"
cp -r "$FRONTEND_DIR/build"/* "$ANDROID_DIR/app/src/main/assets/public/"
echo "✅ Assets copiados"
echo ""

# 4. Compilar APK
echo "4️⃣  Compilando APK..."
cd "$ANDROID_DIR"

# Verificar ANDROID_HOME
if [ -z "$ANDROID_HOME" ]; then
    echo "❌ ANDROID_HOME não está definido"
    echo "Configure com: export ANDROID_HOME=/caminho/para/android-sdk"
    exit 1
fi

# Compilar
if ! command -v gradle &> /dev/null; then
    # Usar gradlew se gradle não está disponível
    export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
    ./gradlew assembleDebug
else
    gradle assembleDebug
fi

# 5. Verificar APK
APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK_PATH" ]; then
    echo ""
    echo "✅✅✅ APK GERADO COM SUCESSO! ✅✅✅"
    echo ""
    echo "📍 Localização: $APK_PATH"
    echo "📦 Tamanho: $(du -h "$APK_PATH" | cut -f1)"
    echo ""
    echo "Para instalar no device:"
    echo "  adb install -r $APK_PATH"
    echo ""
else
    echo "❌ APK não foi gerado"
    exit 1
fi
