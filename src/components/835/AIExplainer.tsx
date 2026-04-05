import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageSquare, Bot, User, Lightbulb, TrendingUp } from 'lucide-react';

interface AIExplainerProps {
  file: {
    file_id: string;
    filename: string;
    parsed_data: any;
  };
}

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{
    document: string;
    confidence: number;
    excerpt: string;
  }>;
  context?: any;
}

const AIExplainer: React.FC<AIExplainerProps> = ({ file }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [patterns, setPatterns] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initial welcome message and pattern analysis
    initializeChat();
  }, [file.file_id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const initializeChat = async () => {
    // Add welcome message
    const welcomeMessage: Message = {
      id: Date.now().toString(),
      type: 'assistant',
      content: `Hello! I'm your AI assistant for analyzing the remittance file "${file.filename}". I can explain payment adjustments, answer questions about specific claims, and help you understand payment patterns.

Here are some things you can ask me:
• "Why was claim ABC123 adjusted?"
• "What does CARC-27 mean?"
• "Show me claims with the most adjustments"
• "Explain the payment patterns in this file"`,
      timestamp: new Date()
    };

    setMessages([welcomeMessage]);

    // Fetch and analyze patterns
    await fetchPatternAnalysis();
  };

  const fetchPatternAnalysis = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/parser/analyze-patterns/${file.file_id}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPatterns(data);

        if (data.common_patterns && data.common_patterns.length > 0) {
          const patternMessage: Message = {
            id: (Date.now() + 1).toString(),
            type: 'assistant',
            content: `I've analyzed the payment patterns in this file. Here are the most common adjustment reasons I found:

${data.common_patterns.map((pattern: any, index: number) => 
  `${index + 1}. **CARC-${pattern.reason_code}** (${pattern.frequency} claims, ${pattern.percentage}%)
     ${pattern.explanation.substring(0, 120)}...`
).join('\n\n')}

Would you like me to explain any of these adjustment codes in more detail?`,
            timestamp: new Date(),
            context: { patterns: data.common_patterns }
          };

          setMessages(prev => [...prev, patternMessage]);
        }
      }
    } catch (error) {
      console.error('Error fetching pattern analysis:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/parser/ask-question/${file.file_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          question: userMessage.content
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: data.answer,
          timestamp: new Date(),
          sources: data.sources,
          context: data.file_context
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error('Failed to get response');
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'I apologize, but I encountered an error while processing your question. Please try asking again or rephrase your question.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const suggestedQuestions = [
    "What are the most common adjustment reasons?",
    "Which claims had the highest adjustments?",
    "Explain the payment summary for this file",
    "What does CARC-1 mean?",
    "Show me denied claims",
    "Why are some claims adjusted vs paid in full?"
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border h-[600px] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center">
          <MessageSquare className="w-5 h-5 text-blue-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">AI Payment Assistant</h3>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          Ask questions about your remittance file - I have access to all HIPAA documentation
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-3xl ${message.type === 'user' ? 'order-2' : ''}`}>
              <div className={`
                flex items-start space-x-2
                ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}
              `}>
                <div className={`
                  flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
                  ${message.type === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-green-100 text-green-600'
                  }
                `}>
                  {message.type === 'user' ? (
                    <User className="w-4 h-4" />
                  ) : (
                    <Bot className="w-4 h-4" />
                  )}
                </div>
                
                <div className={`
                  flex-1 px-4 py-3 rounded-lg
                  ${message.type === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-900'
                  }
                `}>
                  <div className="text-sm whitespace-pre-wrap">
                    {message.content}
                  </div>
                  
                  {/* Context Information */}
                  {message.context && (
                    <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-600">
                      <div className="flex items-center space-x-4">
                        <span>💰 ${message.context.payment_amount?.toLocaleString()}</span>
                        <span>📊 {message.context.claim_count} claims</span>
                        {message.context.top_adjustments?.length > 0 && (
                          <span>⚠️ Top: CARC-{message.context.top_adjustments[0]}</span>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-xs font-medium text-gray-700 mb-2">Sources:</p>
                      <div className="space-y-2">
                        {message.sources.map((source, index) => (
                          <div key={index} className="text-xs bg-white p-2 rounded border">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium text-gray-800">{source.document}</span>
                              <span className="text-gray-500">
                                {(source.confidence * 100).toFixed(0)}% confidence
                              </span>
                            </div>
                            <p className="text-gray-600">{source.excerpt}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              <div className={`
                text-xs text-gray-500 mt-1
                ${message.type === 'user' ? 'text-right' : 'text-left'}
              `}>
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="flex items-start space-x-2">
              <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <Bot className="w-4 h-4 text-green-600" />
              </div>
              <div className="bg-gray-100 px-4 py-3 rounded-lg">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600"></div>
                  <span className="text-sm text-gray-600">Analyzing with AI...</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Questions */}
      {messages.length <= 2 && (
        <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center mb-2">
            <Lightbulb className="w-4 h-4 text-yellow-500 mr-2" />
            <span className="text-sm font-medium text-gray-700">Quick Questions:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => setInputValue(question)}
                className="px-3 py-1 text-xs bg-white border border-gray-300 rounded-full hover:bg-gray-50 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about this remittance file..."
            className="flex-1 min-h-[40px] max-h-[120px] px-3 py-2 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
};

export default AIExplainer;