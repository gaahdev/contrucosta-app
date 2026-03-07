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

## Notificações Push (APK Android)

Para que o usuário receba notificação quando a comissão/entrega for lançada:

1. Firebase no app Android
	- Crie um projeto no Firebase e adicione app Android com package `com.contrucosta.app`.
	- Baixe o `google-services.json` e coloque em `frontend/android/app/google-services.json`.

2. Credencial do Firebase no backend
	- Gere uma Service Account no Firebase (JSON).
	- Configure no backend uma destas variáveis:
	  - `FIREBASE_SERVICE_ACCOUNT_JSON` (conteúdo JSON em string), ou
	  - `FIREBASE_SERVICE_ACCOUNT_FILE` (caminho para o arquivo JSON).

3. Build/sync do Capacitor
	- No frontend, rode `yarn install` (inclui `@capacitor/push-notifications`).
	- Rode `npx cap sync android` antes do build do APK.
	- Ative push no app com `REACT_APP_ENABLE_PUSH_NOTIFICATIONS=true` apenas depois de configurar `google-services.json` e credenciais Firebase no backend.

4. Fluxo de uso
	- Usuário faz login no APK -> token push é registrado no backend.
	- Admin lança comissão/entrega -> backend envia push para o usuário alvo.
