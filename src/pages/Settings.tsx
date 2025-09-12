import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { Input } from '../components/ui/input';
import { Switch } from '../components/ui/switch';
import { Button } from '../components/ui/button';
import { Select } from '../components/ui/select';
import { useQuery, useMutation } from '@tanstack/react-query';
import { SettingsService } from '../services/settings';

interface SettingsState {
  apiKey: string;
  theme: 'light' | 'dark' | 'system';
  notifications: boolean;
  autoUpdate: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  maxHistoryItems: number;
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<SettingsState>({
    apiKey: '',
    theme: 'system',
    notifications: true,
    autoUpdate: true,
    logLevel: 'info',
    maxHistoryItems: 50,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Fetch settings
  const { data: fetchedSettings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => SettingsService.getSettings(),
    onSuccess: (data) => {
      setSettings(data);
    },
  });

  // Save settings mutation
  const saveSettingsMutation = useMutation({
    mutationFn: (newSettings: SettingsState) => SettingsService.saveSettings(newSettings),
    onMutate: () => {
      setIsSaving(true);
      setSaveSuccess(false);
    },
    onSuccess: () => {
      setIsSaving(false);
      setSaveSuccess(true);
      
      // Reset success message after 3 seconds
      setTimeout(() => {
        setSaveSuccess(false);
      }, 3000);
    },
    onError: () => {
      setIsSaving(false);
    },
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setSettings((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setSettings((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSaveSettings = () => {
    saveSettingsMutation.mutate(settings);
  };

  // Apply theme when it changes
  useEffect(() => {
    if (!fetchedSettings) return;
    
    const { theme } = settings;
    const root = window.document.documentElement;
    
    root.classList.remove('light', 'dark');
    
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
  }, [settings.theme, fetchedSettings]);

  if (isLoading) {
    return (
      <div className="p-4 md:p-6 h-full flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2 text-muted-foreground">Loading settings...</span>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 h-full overflow-y-auto">
      <Card className="max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <SettingsIcon className="h-6 w-6" />
            Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* API Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium" id="api-settings">API Settings</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="apiKey" className="flex items-center justify-between">
                  API Key
                  <span className="text-xs text-muted-foreground">(Required)</span>
                </Label>
                <Input
                  id="apiKey"
                  name="apiKey"
                  type="password"
                  value={settings.apiKey}
                  onChange={handleInputChange}
                  placeholder="Enter your API key"
                  aria-required="true"
                  aria-describedby="apikey-description"
                />
                <p id="apikey-description" className="text-xs text-muted-foreground">
                  Your API key is stored locally and never shared.
                </p>
              </div>
            </div>
          </div>

          {/* Appearance Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium" id="appearance-settings">Appearance</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="theme">Theme</Label>
                <Select
                  id="theme"
                  value={settings.theme}
                  onValueChange={(value) => handleSelectChange('theme', value)}
                  aria-label="Select theme"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="system">System</option>
                </Select>
              </div>
            </div>
          </div>

          {/* Notification Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium" id="notification-settings">Notifications</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="notifications" className="block">Enable Notifications</Label>
                  <p className="text-sm text-muted-foreground">Receive notifications for important events</p>
                </div>
                <Switch
                  id="notifications"
                  name="notifications"
                  checked={settings.notifications}
                  onCheckedChange={(checked) => {
                    setSettings((prev) => ({ ...prev, notifications: checked }));
                  }}
                  aria-label="Toggle notifications"
                />
              </div>
            </div>
          </div>

          {/* System Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium" id="system-settings">System</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="autoUpdate" className="block">Auto Update</Label>
                  <p className="text-sm text-muted-foreground">Automatically update the application</p>
                </div>
                <Switch
                  id="autoUpdate"
                  name="autoUpdate"
                  checked={settings.autoUpdate}
                  onCheckedChange={(checked) => {
                    setSettings((prev) => ({ ...prev, autoUpdate: checked }));
                  }}
                  aria-label="Toggle auto updates"
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="logLevel">Log Level</Label>
                  <Select
                    id="logLevel"
                    value={settings.logLevel}
                    onValueChange={(value) => handleSelectChange('logLevel', value)}
                    aria-label="Select log level"
                  >
                    <option value="debug">Debug</option>
                    <option value="info">Info</option>
                    <option value="warn">Warning</option>
                    <option value="error">Error</option>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="maxHistoryItems">Max History Items</Label>
                  <Input
                    id="maxHistoryItems"
                    name="maxHistoryItems"
                    type="number"
                    min="10"
                    max="500"
                    value={settings.maxHistoryItems}
                    onChange={handleInputChange}
                    aria-label="Maximum history items to keep"
                  />
                </div>
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-between items-center border-t p-4">
          <div aria-live="polite">
            {saveSuccess && (
              <p className="text-sm text-green-500 flex items-center">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Settings saved successfully
              </p>
            )}
          </div>
          <Button 
            onClick={handleSaveSettings} 
            disabled={isSaving}
            className="flex items-center gap-2"
            aria-busy={isSaving}
          >
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                Save Settings
              </>
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default Settings;