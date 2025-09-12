import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingProps {
  /** Text to display below the spinner */
  text?: string;
  /** Size of the spinner (small, medium, large) */
  size?: 'sm' | 'md' | 'lg';
  /** Whether to center the loading indicator */
  centered?: boolean;
  /** Whether to show a full-page overlay */
  fullPage?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Loading component for displaying loading states consistently across the application
 */
export function Loading({
  text = 'Loading...',
  size = 'md',
  centered = true,
  fullPage = false,
  className = '',
}: LoadingProps) {
  // Determine spinner size based on the size prop
  const spinnerSize = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }[size];

  // Base component
  const LoadingIndicator = (
    <div
      className={`flex flex-col items-center justify-center ${className}`}
      role="status"
      aria-live="polite"
    >
      <Loader2 className={`${spinnerSize} animate-spin text-primary`} aria-hidden="true" />
      {text && (
        <p className="mt-2 text-sm text-muted-foreground" aria-label={text}>
          {text}
        </p>
      )}
    </div>
  );

  // Full page overlay
  if (fullPage) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
        {LoadingIndicator}
      </div>
    );
  }

  // Centered in parent container
  if (centered) {
    return <div className="flex h-full w-full items-center justify-center">{LoadingIndicator}</div>;
  }

  // Default: inline loading
  return LoadingIndicator;
}

/**
 * Button loading spinner component
 */
export function ButtonLoading({ className = '' }: { className?: string }) {
  return <Loader2 className={`h-4 w-4 animate-spin ${className}`} aria-hidden="true" />;
}

/**
 * Inline loading spinner component
 */
export function InlineLoading({ className = '' }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 ${className}`} role="status" aria-live="polite">
      <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
      <span className="text-xs">Loading...</span>
    </span>
  );
}