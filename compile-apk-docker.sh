#!/bin/bash

# Script para compilar APK com Docker
# Uso: ./compile-apk-docker.sh

WORKDIR=$(pwd)
PROJECT_NAME="contrucosta-app"
IMAGE_NAME="contrucosta-apk-builder"

echo "🚀 Iniciando compilação da APK com Docker..."
echo "📂 Diretório: $WORKDIR"

# Verifica se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado. Por favor, instale Docker primeiro."
    exit 1
fi

# Build da imagem Docker
echo ""
echo "🐳 Compilando imagem Docker..."
docker build -t "${IMAGE_NAME}:latest" . -f Dockerfile

if [ $? -ne 0 ]; then
    echo "❌ Erro ao compilar imagem Docker"
    exit 1
fi

# Executar o container e extrair o APK
echo ""
echo "📦 Executando build dentro do container..."
docker run --rm -v "$WORKDIR:/app" "${IMAGE_NAME}:latest" bash -c "cd /app/frontend/android && ./gradlew assembleDebug --no-daemon"

# Copiar o APK para o host
echo ""
echo "💾 Copiando APK gerado..."
if [ -f "$WORKDIR/frontend/android/app/build/outputs/apk/debug/app-debug.apk" ]; then
    cp "$WORKDIR/frontend/android/app/build/outputs/apk/debug/app-debug.apk" "$WORKDIR/app-debug.apk"
    echo "✅ APK compilada com sucesso!"
    echo "📍 Localização: $WORKDIR/app-debug.apk"
    echo "📊 Tamanho: $(ls -lh $WORKDIR/app-debug.apk | awk '{print $5}')"
else
    echo "⚠️  APK não encontrada. Verifique erros acima."
    exit 1
fi

echo ""
echo "✨ Compilação concluída!"
