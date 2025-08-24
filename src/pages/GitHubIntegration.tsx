import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { invoke } from '@tauri-apps/api/tauri';
import { GitPullRequest, Github, Star, Code } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

type Repository = {
  name: string;
  owner: string;
  description: string;
  stars: number;
  forks: number;
  last_updated: string;
  clone_url: string;
};

type PullRequest = {
  id: number;
  title: string;
  state: string;
  created_at: string;
  user: string;
};

const GitHubIntegration: React.FC = () => {
  const [repoUrl, setRepoUrl] = React.useState('');
  const [localPath, setLocalPath] = React.useState('');
  const [selectedRepo, setSelectedRepo] = React.useState<string | null>(null);

  const { data: repositories } = useQuery({
    queryKey: ['github-repos'],
    queryFn: () => invoke<Repository[]>('list_github_repositories')
  });

  const { data: pullRequests } = useQuery({
    queryKey: ['github-prs', selectedRepo],
    queryFn: () => invoke<PullRequest[]>('list_pull_requests', { repo: selectedRepo }),
    enabled: !!selectedRepo
  });

  const cloneRepository = async () => {
    if (!repoUrl.trim() || !localPath.trim()) return;
    
    try {
      await invoke('clone_repository', {
        url: repoUrl,
        localPath
      });
      setRepoUrl('');
      setLocalPath('');
    } catch (error) {
      console.error('Error cloning repository:', error);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Github className="h-6 w-6" />
            GitHub Integration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="font-medium mb-2">Clone Repository</h3>
              <div className="space-y-2">
                <Input 
                  value={repoUrl} 
                  onChange={(e) => setRepoUrl(e.target.value)} 
                  placeholder="Repository URL" 
                />
                <Input 
                  value={localPath} 
                  onChange={(e) => setLocalPath(e.target.value)} 
                  placeholder="Local path" 
                />
                <Button onClick={cloneRepository} className="w-full">
                  Clone
                </Button>
              </div>
            </div>
            
            <div>
              <h3 className="font-medium mb-2">Create Pull Request</h3>
              <div className="space-y-2">
                <Input placeholder="Base branch" />
                <Input placeholder="Compare branch" />
                <Input placeholder="Title" />
                <Button className="w-full">
                  <GitPullRequest className="h-4 w-4 mr-2" />
                  Create PR
                </Button>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Repositories</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Stars</TableHead>
                      <TableHead>Last Updated</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {repositories?.map((repo) => (
                      <TableRow 
                        key={`${repo.owner}/${repo.name}`}
                        onClick={() => setSelectedRepo(`${repo.owner}/${repo.name}`)}
                        className={`cursor-pointer ${selectedRepo === `${repo.owner}/${repo.name}` ? 'bg-secondary' : ''}`}
                      >
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            <Code className="h-4 w-4" />
                            {repo.owner}/{repo.name}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Star className="h-4 w-4" />
                            {repo.stars}
                          </div>
                        </TableCell>
                        <TableCell>{new Date(repo.last_updated).toLocaleDateString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Pull Requests</CardTitle>
              </CardHeader>
              <CardContent>
                {selectedRepo ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Title</TableHead>
                        <TableHead>State</TableHead>
                        <TableHead>Created</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pullRequests?.map((pr) => (
                        <TableRow key={pr.id}>
                          <TableCell className="font-medium">{pr.title}</TableCell>
                          <TableCell>
                            <span className={`px-2 py-1 rounded-full text-xs ${pr.state === 'open' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                              {pr.state}
                            </span>
                          </TableCell>
                          <TableCell>{new Date(pr.created_at).toLocaleDateString()}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    Select a repository to view pull requests
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GitHubIntegration;