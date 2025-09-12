import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, MessageSquare, FileText, Github, Phone, Activity, Settings } from 'lucide-react';
import { GlobalErrorHandler } from '../ui/error-alert';
import { StatusIndicator } from '../ui/status-indicator';
import { useAppContext } from '../../context/AppContext';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const { isConnected, refreshSystemStatus } = useAppContext();
  
  const navItems = [
    { icon: Home, label: 'Dashboard', path: '/dashboard' },
    { icon: MessageSquare, label: 'AI Chat', path: '/ai-chat' },
    { icon: FileText, label: 'Files', path: '/files' },
    { icon: Github, label: 'GitHub', path: '/github' },
    { icon: Phone, label: 'Communication', path: '/communication' },
    { icon: Activity, label: 'System', path: '/system' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ];

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className="w-64 border-r bg-card">
        <div className="p-4 border-b flex items-center justify-between">
          <h1 className="text-xl font-bold">AI OS</h1>
          <StatusIndicator size="sm" />
        </div>
        <nav className="p-2">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path || 
                (item.path === '/dashboard' && location.pathname === '/');
              
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`
                      flex items-center px-4 py-2 rounded-md text-sm
                      ${isActive ? 'bg-primary text-primary-foreground' : 'hover:bg-secondary'}
                    `}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <item.icon className="h-5 w-5 mr-3" />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        
        {/* Connection status at bottom of sidebar */}
        <div className="absolute bottom-0 w-64 p-4 border-t">
          <StatusIndicator showConnection={true} showSystem={true} />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto relative">
        {children}
        
        {/* Global error handler */}
        <GlobalErrorHandler />
        
        {/* Connection warning */}
        {!isConnected && (
          <div className="fixed top-0 left-0 right-0 bg-destructive text-destructive-foreground p-2 text-center text-sm">
            Connection lost. 
            <button 
              onClick={() => refreshSystemStatus()} 
              className="underline ml-2"
              aria-label="Try reconnecting"
            >
              Try reconnecting
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Layout;