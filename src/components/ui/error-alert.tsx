import React from 'react';
import { AlertCircle, X, RefreshCw } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';

interface ErrorAlertProps {
  /** Custom error message to display instead of the one from context */
  message?: string;
  /** Custom retry function */
  onRetry?: () => void;
  /** Whether to show the close button */
  dismissable?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Error Alert component for displaying application errors with retry and dismiss options
 */
export function ErrorAlert({
  message,
  onRetry,
  dismissable = true,
  className = '',
}: ErrorAlertProps) {
  const { error, clearError, refreshSystemStatus } = useAppContext();
  
  // If no error in context and no custom message, don't render anything
  if (!error && !message) return null;
  
  const errorMessage = message || (error ? error.message : '');
  
  const handleRetry = () => {
    if (onRetry) {
      onRetry();
    } else {
      // Default retry action is to refresh system status
      refreshSystemStatus();
    }
  };
  
  const handleDismiss = () => {
    clearError();
  };
  
  return (
    <div 
      className={`bg-destructive/15 border border-destructive text-destructive px-4 py-3 rounded-md flex items-start justify-between ${className}`}
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="font-medium text-sm">An error occurred</h3>
          <p className="text-sm mt-1">{errorMessage}</p>
        </div>
      </div>
      <div className="flex items-center gap-2 ml-4">
        <button
          onClick={handleRetry}
          className="p-1.5 hover:bg-destructive/20 rounded-md transition-colors"
          aria-label="Retry"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
        {dismissable && (
          <button
            onClick={handleDismiss}
            className="p-1.5 hover:bg-destructive/20 rounded-md transition-colors"
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Global Error Handler component that displays errors from the AppContext
 */
export function GlobalErrorHandler() {
  const { error } = useAppContext();
  
  if (!error) return null;
  
  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-md w-full shadow-lg">
      <ErrorAlert />
    </div>
  );
}