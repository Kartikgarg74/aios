import { apiRequest, mainApi } from './api';

interface CommandRequest {
  command: string;
  context?: Record<string, any>;
}

export interface CommandResponse {
  id: string;
  command?: string;
  result: any;
  status: 'success' | 'error' | 'processing';
  message?: string;
  created_at?: string;
}

export class CommandService {
  /**
   * Send a command to the AI system
   */
  static async sendCommand(command: string, context?: Record<string, any>): Promise<CommandResponse> {
    const request: CommandRequest = {
      command,
      context
    };

    return apiRequest<CommandResponse>(mainApi.post('/commands', request));
  }

  /**
   * Get the status of a command
   */
  static async getCommandStatus(commandId: string): Promise<CommandResponse> {
    return apiRequest<CommandResponse>(mainApi.get(`/commands/${commandId}`));
  }

  /**
   * Cancel a running command
   */
  static async cancelCommand(commandId: string): Promise<CommandResponse> {
    return apiRequest<CommandResponse>(mainApi.delete(`/commands/${commandId}`));
  }

  /**
   * Get command history
   */
  static async getCommandHistory(limit: number = 10): Promise<CommandResponse[]> {
    return apiRequest<CommandResponse[]>(mainApi.get(`/commands/history?limit=${limit}`));
  }
}