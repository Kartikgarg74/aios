import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { MessageSquare, User, Bot, Loader2, RefreshCw, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '../components/ui/card';
import { CommandInput } from '../components/ui/CommandInput';
import { CommandService } from '../services/commands';
import { mainWebSocket } from '../services/websocket';
import { Button } from '../components/ui/button';
import { Loading } from '../components/ui/loading';
import { useAppContext } from '../context/AppContext';
import { Badge } from '../components/ui/badge';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  status?: 'pending' | 'success' | 'error';
}

const AIChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeCommandId, setActiveCommandId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { clearError, isConnected } = useAppContext();

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch command history
  const { data, isLoading: historyLoading, refetch: refetchHistory } = useQuery({
    queryKey: ['command-history'],
    queryFn: () => CommandService.getCommandHistory(20),
    select: (data) => {
      // Convert command history to messages
      const historyMessages = data.map((cmd) => ({
        id: cmd.id,
        content: cmd.result?.message || JSON.stringify(cmd.result),
        sender: cmd.status === 'success' ? 'ai' : 'user' as 'user' | 'ai',
        timestamp: new Date(cmd.created_at || Date.now()),
        status: cmd.status,
      }));
      setMessages(historyMessages);
      setIsLoading(false);
      return data;
    },
    enabled: isConnected // Only fetch when connected
  });
  
  // Handle query errors
  useEffect(() => {
    if (historyLoading) return;
    
    if (!data && !isLoading) {
      console.error('Failed to fetch command history');
      setIsLoading(false);
    }
  }, [data, historyLoading, isLoading]
  });

  // Send command mutation
  const sendCommandMutation = useMutation({
    mutationFn: (command: string) => CommandService.sendCommand(command),
    onSuccess: (response) => {
      // Add user message
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        content: response.command || 'User command',
        sender: 'user',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // If response is immediate, add AI message
      if (response.status === 'success') {
        const aiMessage: Message = {
          id: response.id,
          content: response.result?.message || JSON.stringify(response.result),
          sender: 'ai',
          timestamp: new Date(),
          status: 'success',
        };
        setMessages((prev) => [...prev, aiMessage]);
      } else {
        // Set active command ID for pending commands
        setActiveCommandId(response.id);
        // Add a pending message
        const pendingMessage: Message = {
          id: response.id,
          content: 'Processing your request...',
          sender: 'ai',
          timestamp: new Date(),
          status: 'pending',
        };
        setMessages((prev) => [...prev, pendingMessage]);
      }
      
      // Clear input after sending
      setInputValue('');
    },
    onError: (err) => {
      console.error('Failed to send command:', err);
      // Add error message
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        content: 'Failed to send message. Please try again.',
        sender: 'ai',
        timestamp: new Date(),
        status: 'error',
      };
      setMessages((prev) => [...prev, errorMessage]);
    },
  });

  // Listen for command updates via WebSocket
  useEffect(() => {
    if (!activeCommandId) return;

    const handleCommandUpdate = (data: any) => {
      if (data.id !== activeCommandId) return;

      if (data.status === 'success' || data.status === 'error') {
        // Update the pending message instead of adding a new one
        setMessages((prev) => 
          prev.map(msg => 
            msg.id === activeCommandId 
              ? {
                  ...msg,
                  content: data.result?.message || JSON.stringify(data.result),
                  status: data.status,
                  timestamp: new Date(),
                }
              : msg
          )
        );
        setActiveCommandId(null);
      }
    };

    mainWebSocket.on('command_update', handleCommandUpdate);

    return () => {
      mainWebSocket.off('command_update', handleCommandUpdate);
    };
  }, [activeCommandId]);

  const handleSendCommand = (command: string) => {
    if (!command.trim()) return;
    if (!isConnected) {
      // Add error message if not connected
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        content: 'Cannot send message while disconnected. Please check your connection.',
        sender: 'ai',
        timestamp: new Date(),
        status: 'error',
      };
      setMessages((prev) => [...prev, errorMessage]);
      return;
    }
    sendCommandMutation.mutate(command);
  };

  const handleClearChat = () => {
    if (window.confirm('Are you sure you want to clear all messages?')) {
      setMessages([]);
    }
  };

  const handleRefresh = () => {
    setIsLoading(true);
    clearError();
    refetchHistory();
  };

  const handleInputChange = (value: string) => {
    setInputValue(value);
  };

  return (
    <div className="p-4 md:p-6 h-full flex flex-col">
      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-6 w-6" />
            AI Chat
            {activeCommandId && (
              <Badge variant="outline" className="ml-2 animate-pulse">
                Processing
              </Badge>
            )}
          </CardTitle>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleRefresh}
              disabled={isLoading}
              aria-label="Refresh chat history"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleClearChat}
              disabled={isLoading || messages.length === 0}
              aria-label="Clear chat history"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loading text="Loading messages..." centered />
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground text-center">
              <MessageSquare className="h-12 w-12 mb-4 opacity-20" />
              <h3 className="text-lg font-medium mb-2">No messages yet</h3>
              <p>Start a conversation with the AI assistant</p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`
                      max-w-[80%] p-3 rounded-lg
                      ${message.sender === 'user' 
                        ? 'bg-primary text-primary-foreground' 
                        : message.status === 'error'
                          ? 'bg-destructive text-destructive-foreground'
                          : 'bg-secondary'
                      }
                    `}
                    role="article"
                    aria-label={`${message.sender === 'user' ? 'Your message' : 'AI response'}`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      {message.sender === 'user' ? (
                        <>
                          <span className="font-medium">You</span>
                          <User className="h-4 w-4" aria-hidden="true" />
                        </>
                      ) : (
                        <>
                          <Bot className="h-4 w-4" aria-hidden="true" />
                          <span className="font-medium">AI</span>
                          {message.status === 'pending' && (
                            <Loader2 className="h-3 w-3 animate-spin ml-1" aria-hidden="true" />
                          )}
                        </>
                      )}
                    </div>
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    <div className="text-xs opacity-70 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </CardContent>
        <CardFooter className="p-4 pt-2">
          <div className="w-full">
            <CommandInput
              onSendCommand={handleSendCommand}
              isProcessing={!!activeCommandId || sendCommandMutation.isPending}
              placeholder="Ask the AI anything..."
              value={inputValue}
              onChange={handleInputChange}
            />
            <p className="text-xs text-muted-foreground mt-2">
              {!isConnected ? (
                <span className="text-destructive">Disconnected. Reconnect to send messages.</span>
              ) : (
                <span>Type a message and press Enter to send</span>
              )}
            </p>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
};

export default AIChat;