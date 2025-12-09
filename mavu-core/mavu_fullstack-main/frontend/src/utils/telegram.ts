/**
 * Telegram Web App utilities
 *
 * Provides utilities for detecting and interacting with Telegram Web App
 */

import WebApp from '@twa-dev/sdk';

// Extend Window interface to include Telegram
declare global {
  interface Window {
    Telegram?: {
      WebApp: typeof WebApp;
    };
  }
}

export interface TelegramWebApp {
  initData: string;
  initDataUnsafe: {
    user?: {
      id: number;
      first_name: string;
      last_name?: string;
      username?: string;
      language_code?: string;
      is_premium?: boolean;
      photo_url?: string;
    };
    query_id?: string;
    auth_date?: number;
    hash?: string;
  };
  colorScheme: 'light' | 'dark';
  themeParams: {
    bg_color?: string;
    text_color?: string;
    hint_color?: string;
    link_color?: string;
    button_color?: string;
    button_text_color?: string;
  };
  isExpanded: boolean;
  viewportHeight: number;
  viewportStableHeight: number;
  platform: string;
  version: string;
}

/**
 * Check if the app is running inside Telegram Web App
 */
export const isTelegramWebApp = (): boolean => {
  return typeof window !== 'undefined' && !!window.Telegram?.WebApp;
};

/**
 * Get Telegram Web App instance
 */
export const getTelegramWebApp = (): typeof WebApp | null => {
  if (!isTelegramWebApp()) {
    return null;
  }
  return WebApp;
};

/**
 * Initialize Telegram Web App
 */
export const initTelegramWebApp = (): typeof WebApp | null => {
  const webApp = getTelegramWebApp();

  if (!webApp) {
    console.warn('Not running in Telegram Web App environment');
    return null;
  }

  // Expand the Web App to full height
  webApp.expand();

  // Enable closing confirmation (optional)
  webApp.enableClosingConfirmation();

  // Set header color to match theme
  if (webApp.themeParams.bg_color) {
    webApp.setHeaderColor(webApp.themeParams.bg_color);
  }

  console.log('Telegram Web App initialized', {
    platform: webApp.platform,
    version: webApp.version,
    colorScheme: webApp.colorScheme,
  });

  return webApp;
};

/**
 * Get Telegram initData for authentication
 */
export const getTelegramInitData = (): string | null => {
  const webApp = getTelegramWebApp();

  if (!webApp || !webApp.initData) {
    console.warn('No Telegram initData available');
    return null;
  }

  return webApp.initData;
};

/**
 * Get Telegram user information
 */
export const getTelegramUser = () => {
  const webApp = getTelegramWebApp();

  if (!webApp || !webApp.initDataUnsafe.user) {
    return null;
  }

  return webApp.initDataUnsafe.user;
};

/**
 * Get user's language code from Telegram
 */
export const getTelegramLanguageCode = (): string => {
  const user = getTelegramUser();
  return user?.language_code || 'en';
};

/**
 * Show Telegram alert
 */
export const showTelegramAlert = (message: string): void => {
  const webApp = getTelegramWebApp();

  if (webApp) {
    webApp.showAlert(message);
  } else {
    alert(message);
  }
};

/**
 * Show Telegram confirm dialog
 */
export const showTelegramConfirm = (message: string): Promise<boolean> => {
  const webApp = getTelegramWebApp();

  if (webApp) {
    return new Promise((resolve) => {
      webApp.showConfirm(message, (confirmed) => {
        resolve(confirmed);
      });
    });
  } else {
    return Promise.resolve(confirm(message));
  }
};

/**
 * Close Telegram Web App
 */
export const closeTelegramWebApp = (): void => {
  const webApp = getTelegramWebApp();

  if (webApp) {
    webApp.close();
  }
};

/**
 * Show main button in Telegram Web App
 */
export const showMainButton = (
  text: string,
  onClick: () => void,
  options?: {
    color?: string;
    textColor?: string;
    isActive?: boolean;
    isVisible?: boolean;
  }
): void => {
  const webApp = getTelegramWebApp();

  if (!webApp) return;

  const mainButton = webApp.MainButton;

  mainButton.setText(text);

  if (options?.color) mainButton.color = options.color as `#${string}`;
  if (options?.textColor) mainButton.textColor = options.textColor as `#${string}`;
  if (options?.isActive !== undefined) {
    options.isActive ? mainButton.enable() : mainButton.disable();
  }

  mainButton.onClick(onClick);

  if (options?.isVisible !== false) {
    mainButton.show();
  }
};

/**
 * Hide main button
 */
export const hideMainButton = (): void => {
  const webApp = getTelegramWebApp();

  if (!webApp) return;

  webApp.MainButton.hide();
};

/**
 * Send data to Telegram bot
 */
export const sendDataToBot = (data: string): void => {
  const webApp = getTelegramWebApp();

  if (!webApp) {
    console.warn('Cannot send data: not in Telegram Web App');
    return;
  }

  webApp.sendData(data);
};

/**
 * Get theme parameters
 */
export const getThemeParams = () => {
  const webApp = getTelegramWebApp();

  if (!webApp) return null;

  return webApp.themeParams;
};

/**
 * Check if running in dark mode
 */
export const isDarkMode = (): boolean => {
  const webApp = getTelegramWebApp();

  if (!webApp) return false;

  return webApp.colorScheme === 'dark';
};
