# contrucosta-app

## APK (Capacitor)

Este projeto usa React (CRA). A forma mais rápida de gerar APK é com Capacitor.

### Pré-requisitos
- Android Studio + Android SDK configurado.
- Java 17.

### Passos
1. Instale dependências no frontend.
2. Build do web app.
3. Inicialize e adicione Android no Capacitor.
4. Copie o build e abra no Android Studio.
5. Gere o APK (Build > Build Bundle(s) / APK(s) > Build APK(s)).

### Observações
- O backend já está configurado no arquivo [.env](frontend/.env).
- Se precisar trocar o backend, altere `REACT_APP_BACKEND_URL` e refaça o build.
