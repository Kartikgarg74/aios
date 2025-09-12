/**
 * Settings service for managing application settings
 */

export interface Settings {
  apiKey: string;
  theme: 'light' | 'dark' | 'system';
  notifications: boolean;
  autoUpdate: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  maxHistoryItems: number;
}

const DEFAULT_SETTINGS: Settings = {
  apiKey: '',
  theme: 'system',
  notifications: true,
  autoUpdate: true,
  logLevel: 'info',
  maxHistoryItems: 50,
};

const STORAGE_KEY = 'app_settings';

export class SettingsService {
  /**
   * Get all application settings
   */
  public static async getSettings(): Promise<Settings> {
    try {
      const storedSettings = localStorage.getItem(STORAGE_KEY);
      if (!storedSettings) {
        return DEFAULT_SETTINGS;
      }

      const parsedSettings = JSON.parse(storedSettings);
      return { ...DEFAULT_SETTINGS, ...parsedSettings };
    } catch (error) {
      console.error('Error retrieving settings:', error);
      return DEFAULT_SETTINGS;
    }
  }

  /**
   * Save all application settings
   */
  public static async saveSettings(settings: Settings): Promise<void> {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
      
      // Apply theme immediately
      SettingsService.applyTheme(settings.theme);
      
      return Promise.resolve();
    } catch (error) {
      console.error('Error saving settings:', error);
      return Promise.reject(error);
    }
  }

  /**
   * Get a specific setting value
   */
  public static async getSetting<K extends keyof Settings>(key: K): Promise<Settings[K]> {
    const settings = await SettingsService.getSettings();
    return settings[key];
  }

  /**
   * Update a specific setting value
   */
  public static async updateSetting<K extends keyof Settings>(
    key: K,
    value: Settings[K]
  ): Promise<void> {
    const settings = await SettingsService.getSettings();
    settings[key] = value;
    return SettingsService.saveSettings(settings);
  }

  /**
   * Reset settings to defaults
   */
  public static async resetSettings(): Promise<void> {
    return SettingsService.saveSettings(DEFAULT_SETTINGS);
  }

  /**
   * Apply theme to document
   */
  private static applyTheme(theme: 'light' | 'dark' | 'system'): void {
    const root = window.document.documentElement;
    
    // Remove existing theme classes
    root.classList.remove('light', 'dark');
    
    // Apply new theme
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
  }
}