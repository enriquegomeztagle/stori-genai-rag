import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Settings } from 'lucide-react';
import { sendMessage } from '../services/api';
import ReactMarkdown from 'react-markdown';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatResponse {
  response: string;
  conversation_id: string;
  sources: any[];
  tools_used: string[];
  confidence_score: number;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [showTools, setShowTools] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response: ChatResponse = await sendMessage({
        message: inputMessage,
        conversation_id: conversationId,
        use_tools: true
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
      setConversationId(response.conversation_id);

      if (response.tools_used.length > 0) {
        setShowTools(true);
        setTimeout(() => setShowTools(false), 5000);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your message. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearConversation = () => {
    setMessages([]);
    setConversationId(null);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="bg-gradient-to-r from-[#2a9d8f] to-[#1a7d6f] px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Bot className="h-8 w-8 text-white" />
              <div>
                <h1 className="text-xl font-bold text-white">
                  Stori GenAI RAG Assistant
                </h1>
                <p className="text-green-100 text-sm">
                  Ask me about the Mexican Revolution
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={clearConversation}
                className="px-3 py-1 bg-white/20 text-white rounded-md text-sm hover:bg-white/30 transition-colors"
              >
                Clear Chat
              </button>
            </div>
          </div>
        </div>

        <div className="h-96 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <Bot className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium">Welcome to the Mexican Revolution Assistant!</p>
              <p className="text-sm mt-2">
                Ask me questions about the Mexican Revolution and I'll help you find answers.
              </p>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-[#2a9d8f] text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    {message.role === 'assistant' && (
                      <Bot className="h-4 w-4 mt-1 text-gray-500 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <ReactMarkdown
                        className="prose prose-sm max-w-none"
                        components={{
                          p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                          ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
                          li: ({ children }) => <li className="mb-1">{children}</li>,
                          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                          em: ({ children }) => <em className="italic">{children}</em>,
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                    {message.role === 'user' && (
                      <User className="h-4 w-4 mt-1 text-green-200 flex-shrink-0" />
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 text-gray-800 px-4 py-2 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {showTools && (
          <div className="px-6 py-2 bg-yellow-50 border-t border-yellow-200">
            <div className="flex items-center space-x-2 text-sm text-yellow-800">
              <Settings className="h-4 w-4" />
              <span>Using AI tools to enhance response</span>
            </div>
          </div>
        )}

        <div className="border-t border-gray-200 p-4">
          <div className="flex space-x-4">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me about the Mexican Revolution..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#2a9d8f] focus:border-transparent resize-none"
                rows={2}
                disabled={isLoading}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={isLoading || !inputMessage.trim()}
              className="px-6 py-2 bg-[#2a9d8f] text-white rounded-lg hover:bg-[#1a7d6f] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
            >
              <Send className="h-4 w-4" />
              <span>Send</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface; 
