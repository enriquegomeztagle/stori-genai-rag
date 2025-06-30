import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ChatInterface from './components/ChatInterface';
import DocumentUpload from './components/DocumentUpload';
import Header from './components/Header';
import HealthCheck from './components/HealthCheck';
import MetricsDashboard from './components/MetricsDashboard';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<ChatInterface />} />
            <Route path="/upload" element={<DocumentUpload />} />
            <Route path="/health" element={<HealthCheck />} />
            <Route path="/metrics" element={<MetricsDashboard />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App; 
