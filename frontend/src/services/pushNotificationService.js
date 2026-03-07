import axios from 'axios';
import { Capacitor } from '@capacitor/core';
import { PushNotifications } from '@capacitor/push-notifications';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const PUSH_ENABLED = process.env.REACT_APP_ENABLE_PUSH_NOTIFICATIONS === 'true';

export const initializePushNotifications = async ({ user, authToken, onNotification }) => {
  if (!user?.id || !authToken) return null;
  if (user.role === 'admin') return null;
  if (!Capacitor.isNativePlatform()) return null;
  if (!PUSH_ENABLED) {
    console.info('Push desabilitado: defina REACT_APP_ENABLE_PUSH_NOTIFICATIONS=true após configurar Firebase.');
    return null;
  }

  try {
    let permissions = await PushNotifications.checkPermissions();
    if (permissions.receive === 'prompt') {
      permissions = await PushNotifications.requestPermissions();
    }

    if (permissions.receive !== 'granted') {
      return null;
    }

    await PushNotifications.removeAllListeners();

    PushNotifications.addListener('registration', async ({ value }) => {
      try {
        await axios.post(
          `${BACKEND_URL}/api/notifications/token`,
          {
            token: value,
            platform: Capacitor.getPlatform(),
          },
          {
            headers: {
              Authorization: `Bearer ${authToken}`,
            },
            timeout: 5000,
          }
        );
      } catch (error) {
        console.error('Erro ao registrar token de push:', error?.message);
      }
    });

    PushNotifications.addListener('registrationError', (error) => {
      console.error('Erro no registro de push:', error);
    });

    PushNotifications.addListener('pushNotificationReceived', (notification) => {
      if (onNotification) {
        onNotification(notification);
      }
    });

    await PushNotifications.register();

    return () => {
      PushNotifications.removeAllListeners();
    };
  } catch (error) {
    console.error('Falha ao inicializar push notifications:', error?.message || error);
    return null;
  }
};
