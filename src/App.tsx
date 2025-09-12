import { Toaster } from 'react-hot-toast';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Dashboard from './pages/Dashboard';
import AIChat from './pages/AIChat';
import FileManager from './pages/FileManager';
import GitHubIntegration from './pages/GitHubIntegration';
import CommunicationHub from './pages/CommunicationHub';
import SystemMonitor from './pages/SystemMonitor';
import Settings from './pages/Settings';
import { Layout } from './components/layout';
import './styles/globals.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/ai-chat" element={<AIChat />} />
          <Route path="/files" element={<FileManager />} />
          <Route path="/github" element={<GitHubIntegration />} />
          <Route path="/communication" element={<CommunicationHub />} />
          <Route path="/system" element={<SystemMonitor />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
      <Toaster />
    </Router>
  );
}

export default App;