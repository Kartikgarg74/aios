import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { invoke } from '@tauri-apps/api/tauri';
import { Cpu, HardDrive, MemoryStick, Network, Gauge, Activity } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';

type SystemStats = {
  cpu: {
    usage: number;
    cores: number;
    model: string;
  };
  memory: {
    total: number;
    used: number;
    free: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
  };
  network: {
    sent: number;
    received: number;
  };
  processes: {
    total: number;
    running: number;
  };
};

const formatBytes = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
};

const SystemMonitor: React.FC = () => {
  const { data: stats } = useQuery({
    queryKey: ['system-stats'],
    queryFn: () => invoke<SystemStats>('get_system_stats'),
    refetchInterval: 1000
  });

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-6 w-6" />
            System Monitor
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                <Cpu className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.cpu.usage.toFixed(1)}%</div>
                <p className="text-xs text-muted-foreground">
                  {stats?.cpu.cores} cores | {stats?.cpu.model}
                </p>
                <Progress value={stats?.cpu.usage} className="h-2 mt-2" />
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Memory</CardTitle>
                <MemoryStick className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.memory ? formatBytes(stats.memory.used) : '-'} / {stats?.memory ? formatBytes(stats.memory.total) : '-'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats?.memory ? ((stats.memory.used / stats.memory.total) * 100).toFixed(1) : 0}% used
                </p>
                <Progress 
                  value={stats?.memory ? (stats.memory.used / stats.memory.total) * 100 : 0} 
                  className="h-2 mt-2" 
                />
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Disk</CardTitle>
                <HardDrive className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.disk ? formatBytes(stats.disk.used) : '-'} / {stats?.disk ? formatBytes(stats.disk.total) : '-'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats?.disk ? ((stats.disk.used / stats.disk.total) * 100).toFixed(1) : 0}% used
                </p>
                <Progress 
                  value={stats?.disk ? (stats.disk.used / stats.disk.total) * 100 : 0} 
                  className="h-2 mt-2" 
                />
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Network</CardTitle>
                <Network className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.network ? formatBytes(stats.network.sent) : '-'} sent
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats?.network ? formatBytes(stats.network.received) : '-'} received
                </p>
              </CardContent>
            </Card>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Gauge className="h-5 w-5" />
                  Performance Metrics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Processes</span>
                      <span>{stats?.processes.running} / {stats?.processes.total} running</span>
                    </div>
                    <Progress 
                      value={stats?.processes ? (stats.processes.running / stats.processes.total) * 100 : 0} 
                      className="h-2" 
                    />
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>CPU Temperature</span>
                      <span>Loading...</span>
                    </div>
                    <Progress value={0} className="h-2" />
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>GPU Usage</span>
                      <span>Loading...</span>
                    </div>
                    <Progress value={0} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Real-time Charts
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 bg-secondary/50 rounded flex items-center justify-center">
                  <p className="text-muted-foreground">CPU/Memory usage charts will appear here</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SystemMonitor;