import React, { useState, KeyboardEvent } from 'react';
import { Send } from 'lucide-react';
import { Input } from './input';
import { Button } from './button';

interface CommandInputProps {
  onSendCommand: (command: string) => void;
  isProcessing?: boolean;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
}

export const CommandInput: React.FC<CommandInputProps> = ({
  onSendCommand,
  isProcessing = false,
  placeholder = 'Type a command...',
  value,
  onChange,
}) => {
  const [internalValue, setInternalValue] = useState('');
  
  // Use controlled or uncontrolled input based on whether value prop is provided
  const isControlled = value !== undefined;
  const inputValue = isControlled ? value : internalValue;

  const handleSend = () => {
    if (inputValue.trim() && !isProcessing) {
      onSendCommand(inputValue.trim());
      if (!isControlled) {
        setInternalValue('');
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    if (isControlled) {
      onChange?.(newValue);
    } else {
      setInternalValue(newValue);
    }
  };

  return (
    <div className="flex items-center space-x-2 p-2 border-t bg-background">
      <Input
        value={inputValue}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isProcessing}
        className="flex-1"
        aria-label="Command input"
      />
      <Button
        onClick={handleSend}
        disabled={!inputValue.trim() || isProcessing}
        size="icon"
        aria-label="Send command"
      >
        <Send className="h-4 w-4" />
      </Button>
    </div>
  );
};