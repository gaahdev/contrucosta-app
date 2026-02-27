╔══════════════════════════════════════════════════════════════════════════════╗
║                    CONTRUCOSTA APP - BUILD CHECKLIST                         ║
║                                                                              ║
║  Você escolheu: OPÇÃO 2 - Compilar no seu PC/Laptop                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

📌 ARQUIVOS IMPORTANTES (na raiz do projeto):

  ✅ OPCAO_2_LOCAL.md          → LEIA ISTO PRIMEIRO! Resumo executivo
  ✅ COMPILACAO_RAPIDA.md      → Guia rápido (2 minutos)
  ✅ GUIA_COMPILACAO_LOCAL.md  → Guia completo com troubleshooting
  ✅ Dockerfile                → Para compilar com Docker (alternativa)

📱 COMO COMPILAR (Escolha uma opção):

  OPÇÃO A: Scripts Automatizados (Recomendado)
  ─────────────────────────────────────────────
  
  Linux/macOS:
  $ chmod +x build-apk-auto.sh
  $ ./build-apk-auto.sh debug
  
  Windows (PowerShell):
  > Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  > .\build-apk-windows.ps1 -BuildType debug
  
  Resultado: app-debug.apk na raiz do projeto


  OPÇÃO B: Manualmente (4 passos)
  ──────────────────────────────
  
  1) Instalar Java 17 + Android SDK (ver OPCAO_2_LOCAL.md)
  2) Configurar JAVA_HOME + ANDROID_HOME
  3) $ cd frontend && yarn install && yarn build
  4) $ npx cap copy android && cd android && ./gradlew assembleDebug
  
  Resultado: frontend/android/app/build/outputs/apk/debug/app-debug.apk


  OPÇÃO C: Docker (Se tiver Docker instalado)
  ────────────────────────────────────────────
  
  $ docker build -t contrucosta-apk . 
  $ docker run -v $(pwd):/app contrucosta-apk
  
  (Mais lento na primeira vez, mas funciona independente do setup)

═══════════════════════════════════════════════════════════════════════════════

🎯 PROJETO: React + Capacitor (NÃO é Flutter!)

  Frontend:  React 18 + Tailwind CSS + Radix UI
  Backend:   Python (FastAPI) → /backend/server.py
  Mobile:    Capacitor 6 (React → Android APK)
  
  Build Web: ✅ PRONTO (frontend/build/)
  Build APK: ⏳ POR FAZER (seu PC)

═══════════════════════════════════════════════════════════════════════════════

📋 PRÉ-REQUISITOS (antes de começar):

  [ ] Java 17 JDK instalado
  [ ] Android SDK instalado (Android 30+ ou 34 recomendado)
  [ ] Node.js + Yarn instalados
  [ ] JAVA_HOME configurado
  [ ] ANDROID_HOME configurado
  
  Verificar:
  $ java -version          (deve ser 17.x)
  $ node --version         (qualquer versão recente)
  $ yarn --version         (qualquer versão)
  $ echo $ANDROID_HOME     (deve mostrar caminho)

═══════════════════════════════════════════════════════════════════════════════

🚀 PRÓXIMAS ETAPAS:

  1. Leia: OPCAO_2_LOCAL.md (15 minutos)
  2. Instale pré-requisitos (30-60 minutos, primeira vez)
  3. Execute script OU siga passos manuais (10-30 minutos)
  4. Teste APK em seu dispositivo (5 minutos)
  5. Para Play Store, crie keystore (5 minutos)

═══════════════════════════════════════════════════════════════════════════════

💬 QUICK REFERENCE:

  # Configurar (Linux/macOS)
  export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
  export ANDROID_HOME=$HOME/Android/Sdk
  export PATH=$PATH:$ANDROID_HOME/platform-tools

  # Compilar
  cd frontend
  yarn install && yarn build
  npx cap copy android
  cd android
  ./gradlew assembleDebug

  # Testar
  adb install -r app-debug.apk

═══════════════════════════════════════════════════════════════════════════════

❓ PRECISA DE AJUDA?

  1. Consulte OPCAO_2_LOCAL.md (tudo está lá)
  2. Se der erro, procure por "Error message" em GUIA_COMPILACAO_LOCAL.md
  3. Use Google + Stack Overflow para erros específicos
  4. Tente: ./gradlew clean (antes de compilar de novo)

═══════════════════════════════════════════════════════════════════════════════

✨ BOA SORTE! Você consegue! 🎉

