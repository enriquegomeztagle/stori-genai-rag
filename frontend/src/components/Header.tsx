import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Upload, Activity } from 'lucide-react';

const Header: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-3">
            <img 
              src="/icon.png" 
              alt="Stori GenAI RAG Icon" 
              className="h-8 w-8 object-contain"
            />
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Stori GenAI RAG
              </h1>
              <p className="text-xs text-gray-500">
                Mexican Revolution Assistant
              </p>
            </div>
          </Link>

          <nav className="flex items-center space-x-1">
            <Link
              to="/"
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2 ${
                isActive('/')
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <span>Chat</span>
            </Link>
            
            <Link
              to="/upload"
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2 ${
                isActive('/upload')
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <Upload className="h-4 w-4" />
              <span>Upload</span>
            </Link>
            <a
              href="/health"
              className="px-4 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors flex items-center space-x-2"
            >
              <Activity className="h-4 w-4" />
              <span>Health</span>
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header; 
