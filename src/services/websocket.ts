/**
 * WebSocket service for real-time communication with the backend
 */

type WebSocketEventHandler = (data: any) => void;

interface WebSocketEventMap {
  [eventName: string]: WebSocketEventHandler[];
}

class WebSocketService {
  private socket: WebSocket | null = null;
  private eventHandlers: WebSocketEventMap = {};
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: number | null = null;
  private isConnecting = false;
  private url: string;
  private connectionStatus: 'connected' | 'disconnected' | 'connecting' | 'error' = 'disconnected';
  private statusListeners: ((status: string) => void)[] = [];

  constructor(url: string) {
    this.url = url;
  }

  /**
   * Connect to the WebSocket server
   */
  public connect(): Promise<void> {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    if (this.isConnecting) {
      return new Promise((resolve) => {
        const checkConnection = setInterval(() => {
          if (this.socket?.readyState === WebSocket.OPEN) {
            clearInterval(checkConnection);
            resolve();
          }
        }, 100);
      });
    }

    this.isConnecting = true;
    this.updateStatus('connecting');

    return new Promise((resolve, reject) => {
      try {
        this.socket = new WebSocket(this.url);

        this.socket.onopen = () => {
          this.reconnectAttempts = 0;
          this.isConnecting = false;
          this.updateStatus('connected');
          console.log('WebSocket connected');
          resolve();
        };

        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type && this.eventHandlers[data.type]) {
              this.eventHandlers[data.type].forEach((handler) => {
                try {
                  handler(data.payload || data);
                } catch (handlerError) {
                  console.error('Error in WebSocket event handler:', handlerError);
                }
              });
            }
          } catch (parseError) {
            console.error('Error parsing WebSocket message:', parseError);
          }
        };

        this.socket.onclose = () => {
          this.isConnecting = false;
          this.updateStatus('disconnected');
          console.log('WebSocket disconnected');
          this.attemptReconnect();
        };

        this.socket.onerror = (error) => {
          this.isConnecting = false;
          this.updateStatus('error');
          console.error('WebSocket error:', error);
          reject(error);
        };
      } catch (error) {
        this.isConnecting = false;
        this.updateStatus('error');
        console.error('Error creating WebSocket:', error);
        this.attemptReconnect();
        reject(error);
      }
    });
  }

  /**
   * Disconnect from the WebSocket server
   */
  public disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    this.updateStatus('disconnected');
  }

  /**
   * Send data to the WebSocket server
   */
  public send(type: string, payload: any): boolean {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      return false;
    }

    try {
      this.socket.send(JSON.stringify({ type, payload }));
      return true;
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
      return false;
    }
  }

  /**
   * Register an event handler
   */
  public on(eventName: string, handler: WebSocketEventHandler): void {
    if (!this.eventHandlers[eventName]) {
      this.eventHandlers[eventName] = [];
    }
    this.eventHandlers[eventName].push(handler);
  }

  /**
   * Remove an event handler
   */
  public off(eventName: string, handler?: WebSocketEventHandler): void {
    if (!this.eventHandlers[eventName]) return;

    if (handler) {
      this.eventHandlers[eventName] = this.eventHandlers[eventName].filter(
        (h) => h !== handler
      );
    } else {
      delete this.eventHandlers[eventName];
    }
  }

  /**
   * Get the current connection status
   */
  public getStatus(): string {
    return this.connectionStatus;
  }

  /**
   * Register a status change listener
   */
  public onStatusChange(listener: (status: string) => void): () => void {
    this.statusListeners.push(listener);
    
    // Return a function to unregister the listener
    return () => {
      this.statusListeners = this.statusListeners.filter(l => l !== listener);
    };
  }

  /**
   * Update the connection status and notify listeners
   */
  private updateStatus(status: 'connected' | 'disconnected' | 'connecting' | 'error'): void {
    this.connectionStatus = status;
    this.statusListeners.forEach(listener => {
      try {
        listener(status);
      } catch (error) {
        console.error('Error in status listener:', error);
      }
    });
  }

  /**
   * Attempt to reconnect to the WebSocket server
   */
  private attemptReconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(`Maximum reconnect attempts (${this.maxReconnectAttempts}) reached`);
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    this.reconnectTimeout = window.setTimeout(() => {
      this.reconnectAttempts++;
      this.connect().catch(() => {
        // Error handling is done in the connect method
      });
    }, delay);
  }
}

// Create a singleton instance for the main WebSocket connection
export const mainWebSocket = new WebSocketService('ws://localhost:8000/ws');

// Create a singleton instance for the system WebSocket connection
export const systemWebSocket = new WebSocketService('ws://localhost:8003/ws');

// Export the class for creating additional connections if needed
export default WebSocketService;