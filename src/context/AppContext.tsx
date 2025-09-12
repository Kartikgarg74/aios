import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { mainWebSocket } from '../services/websocket';
import WebSocketService from '../services/websocket';
import { systemApi } from '../services/api';
import { apiRequest } from '../services/api';
import { SettingsService } from '../services/settings';
import { Settings } from '../services/settings';

interface SystemStatus {
  servers: Record<string, boolean>;
  cpu: number;
  memory: number;
  uptime: number;
}

interface AppContextType {
  systemStatus: SystemStatus;
  darkMode: boolean;
  toggleDarkMode: () => void;
  isConnected: boolean;
  isLoading: boolean;
  error: Error | null;
  clearError: () => void;
  settings: Settings | null;
  updateSettings: (newSettings: Partial<Settings>) => void;
  refreshSystemStatus: () => Promise<void>;
}

const defaultSystemStatus: SystemStatus = {
  servers: {},
  cpu: 0,
  memory: 0,
  uptime: 0,
};

export const AppContext = createContext<AppContextType>({
  systemStatus: defaultSystemStatus,
  darkMode: false,
  toggleDarkMode: () => {},
  isConnected: false,
  isLoading: false,
  error: null,
  clearError: () => {},
  settings: null,
  updateSettings: () => {},
  refreshSystemStatus: async () => {},
});

export const useAppContext = () => useContext(AppContext);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>(defaultSystemStatus);
  const [darkMode, setDarkMode] = useState<boolean>(false);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Update settings
  const updateSettings = useCallback((newSettings: Partial<Settings>) => {
    setSettings((prev) => {
      if (!prev) return null;
      const updated = { ...prev, ...newSettings };
      SettingsService.saveSettings(updated);
      return updated;
    });
  }, []);

  // Initialize settings
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const loadedSettings = await SettingsService.getSettings();
        setSettings(loadedSettings);
        setDarkMode(loadedSettings.theme === 'dark' || 
          (loadedSettings.theme === 'system' && 
            window.matchMedia('(prefers-color-scheme: dark)').matches));
      } catch (err) {
        console.error('Failed to load settings:', err);
        setError(err instanceof Error ? err : new Error('Failed to load settings'));
      }
    };

    loadSettings();
  }, []);

  // Apply dark mode class to document
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    
    // Update settings if they exist
    if (settings) {
      const newTheme = darkMode ? 'dark' : 'light';
      if (settings.theme !== newTheme && settings.theme !== 'system') {
        updateSettings({ theme: newTheme });
      }
    }
  }, [darkMode, settings, updateSettings]);

  // Toggle dark mode
  const toggleDarkMode = useCallback(() => {
    setDarkMode((prev) => !prev);
  }, []);

  // Connect to WebSockets
  useEffect(() => {
    const connectWebSockets = async () => {
      try {
        await mainWebSocket.connect();
        await systemWebSocket.connect();
        setIsConnected(true);
      } catch (err) {
        console.error('WebSocket connection error:', err);
        setError(err instanceof Error ? err : new Error('Failed to connect to WebSocket'));
        setIsConnected(false);
      }
    };

    connectWebSockets();

    // Listen for connection status changes
    const mainStatusListener = mainWebSocket.onStatusChange((status) => {
      setIsConnected(status === 'connected');
      if (status === 'error') {
        setError(new Error('WebSocket connection error'));
      }
    });

    // Listen for system status updates
    systemWebSocket.on('system_status', (data) => {
      setSystemStatus((prev) => ({
        ...prev,
        ...data,
      }));
    });

    // Cleanup
    return () => {
      mainStatusListener();
      mainWebSocket.disconnect();
      systemWebSocket.disconnect();
    };
  }, []);

  // Fetch system status
  const refreshSystemStatus = useCallback(async () => {
    setIsLoading(true);
    try {
      const status = await apiRequest<SystemStatus>(systemApi.get('/status'));
      setSystemStatus(status);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch system status:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch system status'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial system status fetch and periodic updates
  useEffect(() => {
    refreshSystemStatus();
    
    // Set up periodic refresh
    const interval = setInterval(() => {
      refreshSystemStatus();
    }, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, [refreshSystemStatus]);

  return (
    <AppContext.Provider
      value={{
        systemStatus,
        darkMode,
        toggleDarkMode,
        isConnected,
        isLoading,
        error,
        clearError,
        settings,
        updateSettings,
        refreshSystemStatus,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};