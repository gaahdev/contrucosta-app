#!/bin/bash

# Script para gerar APK no ambiente local
# Pré-requisitos:
# - Java 21+ instalado
# - Android SDK instalado (via Android Studio ou sdkmanager)
# - ANDROID_HOME configurado

echo "🚀 Iniciando compilação do APK..."

cd "$(dirname "$0")/frontend/android"

# Verificar ANDROID_HOME
if [ -z "$ANDROID_HOME" ]; then
    echo "❌ ANDROID_HOME não configurado"
    echo "Configure com: export ANDROID_HOME=/caminho/para/android-sdk"
    exit 1
fi

# Verificar Java
JAVA_VERSION=$(/usr/libexec/java_home -v 21+ --exec java -version 2>&1 | head -1)
echo "✅ Java: $JAVA_VERSION"

# Compilar APK
echo "📦 Compilando APK debug..."
export JAVA_HOME=$(/usr/libexec/java_home -v 21+)

./gradlew assembleDebug

if [ $? -eq 0 ]; then
    APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
    if [ -f "$APK_PATH" ]; then
        echo "✅ APK gerado com sucesso!"
        echo "📍 Localização: $APK_PATH"
        echo "📦 Tamanho: $(du -h "$APK_PATH" | cut -f1)"
    fi
else
    echo "❌ Falha ao gerar APK"
    exit 1
fi
