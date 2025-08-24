import React from 'react';

const Select = React.forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement> & { onValueChange?: (value: string) => void }
>(({ className, ...props }, ref) => (
  <select
    ref={ref}
    className={`
      flex h-10 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-2
      text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none
      focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50
      ${className}
    `}
    {...props}
  />
));

Select.displayName = 'Select';

const SelectContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, children, ...props }, ref) => (
  <div ref={ref} className={className} {...props}>
    {children}
  </div>
));
SelectContent.displayName = 'SelectContent';

const SelectItem = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { value: string }>(({ className, children, ...props }, ref) => (
  <div ref={ref} className={className} {...props}>
    {children}
  </div>
));
SelectItem.displayName = 'SelectItem';

const SelectTrigger = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement>>(({ className, children, ...props }, ref) => (
  <button ref={ref} className={className} {...props}>
    {children}
  </button>
));
SelectTrigger.displayName = 'SelectTrigger';

const SelectValue = React.forwardRef<HTMLSpanElement, React.HTMLAttributes<HTMLSpanElement> & { placeholder?: string }>(({ className, children, ...props }, ref) => (
  <span ref={ref} className={className} {...props}>
    {children}
  </span>
));
SelectValue.displayName = 'SelectValue';

export { Select, SelectContent, SelectItem, SelectTrigger, SelectValue };