import React from 'react';
import { Wifi, WifiOff, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';

interface StatusIndicatorProps {
  /** Show connection status */
  showConnection?: boolean;
  /** Show system status */
  showSystem?: boolean;
  /** Size of the indicator */
  size?: 'sm' | 'md' | 'lg';
  /** Additional CSS classes */
  className?: string;
}

/**
 * Status Indicator component for displaying connection and system status
 */
export function StatusIndicator({
  showConnection = true,
  showSystem = false,
  size = 'md',
  className = '',
}: StatusIndicatorProps) {
  const { isConnected, systemStatus, isLoading } = useAppContext();
  
  // Determine icon sizes based on the size prop
  const iconSize = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  }[size];
  
  // Determine text sizes based on the size prop
  const textSize = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  }[size];
  
  // Calculate overall system status
  const systemHealthy = Object.values(systemStatus.servers).every(status => status === true);
  
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {showConnection && (
        <div 
          className={`flex items-center gap-1.5 ${textSize}`}
          aria-live="polite"
        >
          {isConnected ? (
            <>
              <Wifi className={`${iconSize} text-green-500`} />
              <span>Connected</span>
            </>
          ) : (
            <>
              <WifiOff className={`${iconSize} text-destructive`} />
              <span>Disconnected</span>
            </>
          )}
        </div>
      )}
      
      {showSystem && (
        <div 
          className={`flex items-center gap-1.5 ${textSize}`}
          aria-live="polite"
        >
          {isLoading ? (
            <>
              <div className={`${iconSize} animate-pulse bg-muted rounded-full`}></div>
              <span>Checking...</span>
            </>
          ) : systemHealthy ? (
            <>
              <CheckCircle2 className={`${iconSize} text-green-500`} />
              <span>Systems normal</span>
            </>
          ) : (
            <>
              <AlertTriangle className={`${iconSize} text-amber-500`} />
              <span>System issues</span>
            </>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Compact Status Indicator that only shows icons
 */
export function CompactStatusIndicator({ className = '' }: { className?: string }) {
  const { isConnected, systemStatus } = useAppContext();
  
  // Calculate overall system status
  const systemHealthy = Object.values(systemStatus.servers).every(status => status === true);
  
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {isConnected ? (
        <Wifi className="h-4 w-4 text-green-500" aria-label="Connected" />
      ) : (
        <WifiOff className="h-4 w-4 text-destructive" aria-label="Disconnected" />
      )}
      
      {systemHealthy ? (
        <CheckCircle2 className="h-4 w-4 text-green-500" aria-label="Systems normal" />
      ) : (
        <AlertTriangle className="h-4 w-4 text-amber-500" aria-label="System issues" />
      )}
    </div>
  );
}