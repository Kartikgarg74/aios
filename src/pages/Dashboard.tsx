import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { invoke } from '@tauri-apps/api/tauri';
import { Activity, Cpu, HardDrive, MessageSquare, GitBranch, Phone, Settings, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

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

  const { data: activeQueries } = useQuery({
    queryKey: ['active-queries'],
    queryFn: () => invoke<number>('get_active_ai_queries'),
    refetchInterval: 5000,
  });

  const { data: systemInfo } = useQuery({
    queryKey: ['system-info'],
    queryFn: () => invoke<SystemInfo>('get_system_info'),
    refetchInterval: 5000,
  });

  const { data: mcpStatus } = useQuery({
    queryKey: ['mcp-status'],
    queryFn: () => invoke<MCPServerStatus>('health_check'),
    refetchInterval: 10000,
  });

  const { data: currentPerformanceData } = useQuery({
    queryKey: ['performance-data'],
    queryFn: () => invoke<{ cpu_usage: number; memory_usage: number }>('get_performance_data'),
    refetchInterval: 1000,
  });

  useEffect(() => {
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
  }, [currentPerformanceData]);

  const memoryUsage = systemInfo ? (systemInfo.memory_used / systemInfo.memory_total) * 100 : 0;
  const uptimeHours = systemInfo ? Math.floor(systemInfo.uptime / 3600) : 0;

  const quickActions = [
    { icon: MessageSquare, label: 'AI Chat', path: '/ai-chat', color: 'bg-blue-500' },
    { icon: GitBranch, label: 'GitHub', path: '/github', color: 'bg-purple-500' },
    { icon: Phone, label: 'Communication', path: '/communication', color: 'bg-green-500' },
    { icon: Settings, label: 'System', path: '/system', color: 'bg-orange-500' },
  ];


  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">AI Operating System Dashboard</h1>
        <p className="text-muted-foreground">Manage your AI-powered development environment</p>
      </div>

      {/* System Overview */}
      <div className="grid gap-4 md:grid-cols-4">
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
            <CardTitle className="text-sm font-medium">CPU Cores</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemInfo?.cpu_count || 0}</div>
            <p className="text-xs text-muted-foreground">Processing units</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{memoryUsage.toFixed(1)}%</div>
            <Progress value={memoryUsage} className="h-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Uptime</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{uptimeHours}h</div>
            <p className="text-xs text-muted-foreground">System running</p>
          </CardContent>
        </Card>
      </div>

      {/* MCP Servers Status */}
      <Card>
        <CardHeader>
          <CardTitle>MCP Servers Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            {Object.entries(mcpStatus || {}).map(([server, status]) => (
              <div key={server} className="flex items-center justify-between">
                <span className="text-sm font-medium capitalize">{server}</span>
                <Badge variant={status ? 'default' : 'destructive'}>
                  {status ? 'Online' : 'Offline'}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-4">
        {quickActions.map((action) => (
          <Card key={action.label} className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className={`w-12 h-12 ${action.color} rounded-lg flex items-center justify-center mb-4`}>
                <action.icon className="h-6 w-6 text-white" />
              </div>
              <h3 className="font-semibold mb-2">{action.label}</h3>
              <Button 
                variant="ghost" 
                className="w-full"
                onClick={() => window.location.href = action.path}
              >
                Open
              </Button>
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
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="cpu" stroke="#8884d8" name="CPU %" />
              <Line type="monotone" dataKey="memory" stroke="#82ca9d" name="Memory %" />
            </LineChart>
          </ResponsiveContainer>
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
    </div>
  );
};

export default Dashboard;