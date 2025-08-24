import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { invoke } from '@tauri-apps/api/tauri';
import { Folder, File, HardDrive, Upload, Download, Trash2, Plus } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

type FileItem = {
  name: string;
  path: string;
  size: number;
  is_dir: boolean;
  modified: string;
};

const FileManager: React.FC = () => {
  const [currentPath, setCurrentPath] = React.useState('/');
  const [newFolderName, setNewFolderName] = React.useState('');
  const [selectedFile, setSelectedFile] = React.useState<string | null>(null);

  const { data: files, refetch } = useQuery({
    queryKey: ['files', currentPath],
    queryFn: () => invoke<FileItem[]>('list_directory', { path: currentPath })
  });

  const navigateTo = (path: string) => {
    if (path === '..') {
      setCurrentPath(prev => {
        const parts = prev.split('/').filter(Boolean);
        parts.pop();
        return parts.length ? `/${parts.join('/')}` : '/';
      });
    } else {
      setCurrentPath(prev => `${prev}${prev.endsWith('/') ? '' : '/'}${path}`);
    }
  };

  const createFolder = async () => {
    if (!newFolderName.trim()) return;
    
    try {
      await invoke('create_directory', {
        path: `${currentPath}${currentPath.endsWith('/') ? '' : '/'}${newFolderName}`
      });
      setNewFolderName('');
      refetch();
    } catch (error) {
      console.error('Error creating folder:', error);
    }
  };

  const deleteItem = async (path: string) => {
    try {
      await invoke('delete_file', { path });
      refetch();
    } catch (error) {
      console.error('Error deleting item:', error);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="h-6 w-6" />
            File Manager
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Input 
              value={currentPath} 
              onChange={(e) => setCurrentPath(e.target.value)} 
              className="flex-1" 
            />
            <Button onClick={() => refetch()} variant="outline">
              Refresh
            </Button>
          </div>
          
          <div className="flex items-center gap-2">
            <Input 
              value={newFolderName} 
              onChange={(e) => setNewFolderName(e.target.value)} 
              placeholder="New folder name" 
              className="flex-1" 
            />
            <Button onClick={createFolder}>
              <Plus className="h-4 w-4 mr-2" />
              Create Folder
            </Button>
          </div>
          
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Modified</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {currentPath !== '/' && (
                <TableRow onClick={() => navigateTo('..')} className="cursor-pointer">
                  <TableCell className="font-medium flex items-center gap-2">
                    <Folder className="h-4 w-4" />
                    ..
                  </TableCell>
                  <TableCell>-</TableCell>
                  <TableCell>-</TableCell>
                  <TableCell>-</TableCell>
                </TableRow>
              )}
              
              {files?.map((file) => (
                <TableRow 
                  key={file.path}
                  onClick={() => file.is_dir ? navigateTo(file.name) : setSelectedFile(file.path)}
                  className={`cursor-pointer ${selectedFile === file.path ? 'bg-secondary' : ''}`}
                >
                  <TableCell className="font-medium flex items-center gap-2">
                    {file.is_dir ? 
                      <Folder className="h-4 w-4" /> : 
                      <File className="h-4 w-4" />}
                    {file.name}
                  </TableCell>
                  <TableCell>{file.is_dir ? '-' : formatSize(file.size)}</TableCell>
                  <TableCell>{new Date(file.modified).toLocaleString()}</TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      {!file.is_dir && (
                        <>
                          <Button size="sm" variant="outline">
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button size="sm" variant="outline">
                            <Upload className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                      <Button 
                        size="sm" 
                        variant="destructive" 
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteItem(file.path);
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default FileManager;