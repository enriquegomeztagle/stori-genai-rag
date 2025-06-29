import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadDocument, getDocumentStats, clearDocuments } from '../services/api';

interface UploadResult {
  document_id: string;
  filename: string;
  chunks_created: number;
  loader_chunks?: number;
  vector_chunks?: number;
  status: string;
  message?: string;
}

interface DocumentStats {
  total_documents: number;
  total_chunks: number;
  collection_name: string;
  embedding_model: string;
}

const DocumentUpload: React.FC = () => {
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isClearing, setIsClearing] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setIsUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const file = acceptedFiles[0];
      const formData = new FormData();
      formData.append('file', file);

      const result = await uploadDocument(formData);
      setUploadResult(result);
      
      await loadStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/plain': ['.txt']
    },
    multiple: false
  });

  const loadStats = async () => {
    try {
      const statsData = await getDocumentStats();
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const handleClearDocuments = async () => {
    setIsClearing(true);
    setError(null);
    setUploadResult(null);
    try {
      await clearDocuments();
      await loadStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to clear documents');
    } finally {
      setIsClearing(false);
    }
  };

  React.useEffect(() => {
    loadStats();
  }, []);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Document Upload
          </h1>
          <p className="text-gray-600">
            Upload documents about the Mexican Revolution to enhance the knowledge base.
          </p>
        </div>

        {stats && (
          <div className="mb-6 p-4 bg-[#2a9d8f]/10 rounded-lg border border-[#2a9d8f]/20">
            <h3 className="font-semibold text-[#2a9d8f] mb-2">Knowledge Base Stats</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-[#2a9d8f] font-medium">Total Documents:</span>
                <span className="ml-2 text-gray-900">{stats.total_documents}</span>
              </div>
              <div>
                <span className="text-[#2a9d8f] font-medium">Total Chunks:</span>
                <span className="ml-2 text-gray-900">{stats.total_chunks}</span>
              </div>
              <div>
                <span className="text-[#2a9d8f] font-medium">Collection:</span>
                <span className="ml-2 text-gray-900">{stats.collection_name}</span>
              </div>
              <div>
                <span className="text-[#2a9d8f] font-medium">Embedding Model:</span>
                <span className="ml-2 text-gray-900">{stats.embedding_model}</span>
              </div>
            </div>
            <button
              onClick={handleClearDocuments}
              disabled={isClearing}
              className="mt-4 w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
            >
              {isClearing ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <AlertCircle className="h-5 w-5" />
              )}
              <span>Delete All Documents</span>
            </button>
          </div>
        )}

        <div className="mb-6">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            {isDragActive ? (
              <p className="text-blue-600 font-medium">Drop the file here...</p>
            ) : (
              <div>
                <p className="text-lg font-medium text-gray-900 mb-2">
                  Drag & drop a document here
                </p>
                <p className="text-gray-500 mb-4">
                  or click to select a file
                </p>
                <p className="text-sm text-gray-400">
                  Supported formats: PDF, DOCX, DOC, XLSX, XLS, TXT
                </p>
              </div>
            )}
          </div>
        </div>

        {uploadResult && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <CheckCircle className="h-6 w-6 text-green-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-green-900">Upload Successful!</h4>
                <div className="mt-2 text-sm text-green-800">
                  <p><strong>File:</strong> {uploadResult.filename}</p>
                  <p><strong>Document ID:</strong> {uploadResult.document_id}</p>
                  <p><strong>Initial Chunks Created by Loader:</strong> {uploadResult.loader_chunks} <span className="text-gray-500">(EX: pages of the PDF)</span></p>
                  <p><strong>Final Chunks Saved in Vector Store:</strong> {uploadResult.vector_chunks} <span className="text-gray-500">(used for semantic search)</span></p>
                  <p><strong>Status:</strong> {uploadResult.status}</p>
                  {uploadResult.message && (
                    <p><strong>Message:</strong> {uploadResult.message}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <AlertCircle className="h-6 w-6 text-red-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-red-900">Upload Failed</h4>
                <p className="mt-1 text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {isUploading && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center space-x-3">
              <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
              <div>
                <h4 className="font-medium text-blue-900">Processing Document...</h4>
                <p className="text-sm text-blue-800">
                  Please wait while we process and index your document.
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2">Instructions</h3>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Upload documents related to the Mexican Revolution</li>
            <li>• Supported formats: PDF, DOCX, DOC, XLSX, XLS, TXT</li>
            <li>• Documents will be automatically processed and indexed</li>
            <li>• The AI will use these documents to answer questions</li>
            <li>• You can upload multiple documents to expand the knowledge base</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload; 
