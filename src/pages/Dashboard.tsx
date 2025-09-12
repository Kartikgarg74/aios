import React, { useState, useEffect, useContext } from 'react';
import { useQuery } from '@tanstack/react-query';
import { mainApi, systemApi } from '../services/api';
import { Activity, Cpu, HardDrive, MessageSquare, GitBranch, Phone, Settings, Zap, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Loading } from '../components/ui/loading';
import { useAppContext } from '../context/AppContext';

interface SystemInfo {
  hostname: string;
  platform: string;
  cpu_count: number;
  memory_total: number;
  memory_used: number;
  uptime: number;
}

interface MCPServerStatus {
  [key: string]: boolean;
}

interface PerformanceMetric {
  time: string;
  cpu: number;
  memory: number;
}

const Dashboard: React.FC = () => {
  const [performanceChartData, setPerformanceChartData] = useState<PerformanceMetric[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Get global app context for error handling
  const { error, clearError, refreshSystemStatus, systemStatus } = useAppContext();

  const { data: activeQueries, isLoading: queriesLoading, refetch: refetchQueries, error: queriesError } = useQuery({
    queryKey: ['active-queries'],
    queryFn: () => mainApi.get<number>('/ai/active-queries'),
    select: (response) => response.data,
    refetchInterval: 5000,
    retry: 2
  });
  
  // Handle query errors
  useEffect(() => {
    if (queriesError) {
      console.error('Failed to fetch active queries:', queriesError);
    }
  }, [queriesError]);

  const { data: systemInfo, isLoading: systemInfoLoading, refetch: refetchSystemInfo, error: systemInfoError } = useQuery({
    queryKey: ['system-info'],
    queryFn: () => systemApi.get<SystemInfo>('/info'),
    select: (response) => response.data,
    refetchInterval: 5000,
    retry: 2
  });
  
  // Handle system info query errors
  useEffect(() => {
    if (systemInfoError) {
      console.error('Failed to fetch system info:', systemInfoError);
    }
  }, [systemInfoError]);

  const { data: mcpStatus, isLoading: mcpStatusLoading, refetch: refetchMcpStatus, error: mcpStatusError } = useQuery({
    queryKey: ['mcp-status'],
    queryFn: () => mainApi.get<MCPServerStatus>('/health'),
    select: (response) => response.data,
    refetchInterval: 10000,
    retry: 2
  });
  
  // Handle MCP status query errors
  useEffect(() => {
    if (mcpStatusError) {
      console.error('Failed to fetch MCP status:', mcpStatusError);
    }
  }, [mcpStatusError]);

  const { data: currentPerformanceData, isLoading: performanceLoading, refetch: refetchPerformance, error: performanceError } = useQuery({
    queryKey: ['performance-data'],
    queryFn: () => systemApi.get<{ cpu_usage: number; memory_usage: number }>('/performance'),
    select: (response) => response.data,
    refetchInterval: 1000,
    retry: 2
  });
  
  // Handle performance data query errors
  useEffect(() => {
    if (performanceError) {
      console.error('Failed to fetch performance data:', performanceError);
    }
  }, [performanceError]);

  // Function to refresh all data
  const refreshAllData = () => {
    refetchQueries();
    refetchSystemInfo();
    refetchMcpStatus();
    refetchPerformance();
    refreshSystemStatus();
    clearError(); // Clear any existing errors
  };

  useEffect(() => {
    // Update loading state based on all data fetching states
    setIsLoading(queriesLoading || systemInfoLoading || mcpStatusLoading || performanceLoading);
    
    if (currentPerformanceData) {
      setPerformanceChartData((prevData) => {
        const newEntry = {
          time: new Date().toLocaleTimeString(),
          cpu: currentPerformanceData.cpu_usage,
          memory: currentPerformanceData.memory_usage,
        };
        // Keep only the last 20 data points for the chart
        return [...prevData, newEntry].slice(-20);
      });
    }
  }, [currentPerformanceData, queriesLoading, systemInfoLoading, mcpStatusLoading, performanceLoading]);

  const memoryUsage = systemInfo ? (systemInfo.memory_used / systemInfo.memory_total) * 100 : 0;
  const uptimeHours = systemInfo ? Math.floor(systemInfo.uptime / 3600) : 0;

  const quickActions = [
    { icon: MessageSquare, label: 'AI Chat', path: '/ai-chat', color: 'bg-blue-500' },
    { icon: GitBranch, label: 'GitHub', path: '/github', color: 'bg-purple-500' },
    { icon: Phone, label: 'Communication', path: '/communication', color: 'bg-green-500' },
    { icon: Settings, label: 'System', path: '/system', color: 'bg-orange-500' },
  ];


  return (
    <div className="p-4 md:p-6 space-y-4 md:space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-2">
        <div className="space-y-2 mb-4 md:mb-0">
          <h1 className="text-2xl md:text-3xl font-bold">AI Operating System Dashboard</h1>
          <p className="text-muted-foreground">Manage your AI-powered development environment</p>
        </div>
        
        <Button 
          onClick={refreshAllData} 
          disabled={isLoading}
          className="flex items-center gap-2"
          aria-label="Refresh dashboard data"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {isLoading && (
        <div className="flex justify-center items-center py-8">
          <Loading text="Loading dashboard data..." centered />
        </div>
      )}

      {!isLoading && (
        <>
          {/* System Overview */}
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">System Status</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{systemInfo?.platform || 'Loading...'}</div>
                <p className="text-xs text-muted-foreground">{systemInfo?.hostname}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                <Cpu className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{currentPerformanceData?.cpu_usage.toFixed(1)}%</div>
                <p className="text-xs text-muted-foreground">{systemInfo?.cpu_count} Cores</p>
                <Progress 
                  className="mt-2" 
                  value={currentPerformanceData?.cpu_usage || 0} 
                  aria-label={`CPU usage ${currentPerformanceData?.cpu_usage.toFixed(1)}%`}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
                <HardDrive className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{memoryUsage.toFixed(1)}%</div>
                <p className="text-xs text-muted-foreground">
                  {(systemInfo?.memory_used / 1024 / 1024 / 1024).toFixed(2)} GB / 
                  {(systemInfo?.memory_total / 1024 / 1024 / 1024).toFixed(2)} GB
                </p>
                <Progress 
                  className="mt-2" 
                  value={memoryUsage} 
                  aria-label={`Memory usage ${memoryUsage.toFixed(1)}%`}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Uptime</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{uptimeHours} hours</div>
                <p className="text-xs text-muted-foreground">
                  {Math.floor((systemInfo?.uptime || 0) % 3600 / 60)} minutes
                </p>
              </CardContent>
            </Card>
          </div>

          {/* MCP Server Status */}
          <Card>
            <CardHeader>
              <CardTitle>MCP Server Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                {mcpStatus && Object.entries(mcpStatus).map(([server, status]) => (
                  <div key={server} className="flex items-center space-x-2">
                    <div 
                      className={`w-3 h-3 rounded-full ${status ? 'bg-green-500' : 'bg-red-500'}`}
                      aria-hidden="true"
                    ></div>
                    <span className="text-sm">{server}</span>
                    <span className="sr-only">{status ? 'Online' : 'Offline'}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <div className="grid gap-4 grid-cols-2 sm:grid-cols-4">
            {quickActions.map((action) => (
              <Card key={action.label} className="overflow-hidden">
                <div className={`${action.color} h-1`} aria-hidden="true"></div>
                <CardContent className="pt-6">
                  <div className="flex flex-col items-center text-center space-y-2">
                    <action.icon className="h-8 w-8 mb-2" aria-hidden="true" />
                    <h3 className="font-medium">{action.label}</h3>
                    <Button 
                      variant="ghost" 
                      className="w-full"
                      onClick={() => window.location.href = action.path}
                      aria-label={`Open ${action.label}`}
                    >
                      Open
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Performance Chart */}
          <Card>
            <CardHeader>
              <CardTitle>System Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] w-full" aria-label="System performance chart showing CPU and memory usage over time">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={performanceChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="cpu" stroke="#8884d8" name="CPU %" />
                    <Line type="monotone" dataKey="memory" stroke="#82ca9d" name="Memory %" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Active Queries */}
          <Card>
            <CardHeader>
              <CardTitle>Active AI Queries</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Processing tasks</span>
                <Badge variant="outline">{activeQueries || 0}</Badge>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};

export default Dashboard;