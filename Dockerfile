FROM ubuntu:24.04

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    ANDROID_SDK_ROOT=/usr/local/android-sdk \
    ANDROID_HOME=/usr/local/android-sdk \
    PATH=$PATH:/usr/lib/jvm/java-17-openjdk-amd64/bin:/usr/local/android-sdk/platform-tools:/usr/local/android-sdk/tools/bin

# Install dependencies
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk-headless \
    wget \
    unzip \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Download and install Android SDK
RUN mkdir -p ${ANDROID_SDK_ROOT} && \
    cd /tmp && \
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip && \
    unzip -q commandlinetools-linux-9477386_latest.zip -d ${ANDROID_SDK_ROOT}/ && \
    rm commandlinetools-linux-9477386_latest.zip && \
    mv ${ANDROID_SDK_ROOT}/cmdline-tools ${ANDROID_SDK_ROOT}/cmdline-tools-temp && \
    mkdir -p ${ANDROID_SDK_ROOT}/cmdline-tools/latest && \
    mv ${ANDROID_SDK_ROOT}/cmdline-tools-temp/* ${ANDROID_SDK_ROOT}/cmdline-tools/latest/ && \
    rmdir ${ANDROID_SDK_ROOT}/cmdline-tools-temp

# Accept licenses
RUN mkdir -p ${ANDROID_SDK_ROOT}/licenses && \
    echo -e "\n24333f8a63b6825ea9c5514f83c2829b004d1fee" > ${ANDROID_SDK_ROOT}/licenses/android-sdk-license && \
    echo -e "\n84831b9409646a918e30573bab4c9c91346d8abd" > ${ANDROID_SDK_ROOT}/licenses/android-sdk-preview-license

# Install SDK components
RUN yes | ${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin/sdkmanager --install \
    "platforms;android-34" \
    "build-tools;34.0.0" \
    "platform-tools" || true

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g yarn

WORKDIR /app

COPY . /app

# Build the frontend web
RUN cd /app/frontend && \
    yarn install && \
    yarn build && \
    npx cap copy android

# Compile APK
RUN cd /app/frontend/android && \
    chmod +x gradlew && \
    ./gradlew assembleDebug --no-daemon

# Copy output APK
RUN cp /app/frontend/android/app/build/outputs/apk/debug/app-debug.apk /app/app-debug.apk || true

CMD ["/bin/bash"]
