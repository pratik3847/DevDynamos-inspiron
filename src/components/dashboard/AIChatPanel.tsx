import React, { useState, useRef, useEffect } from 'react';
import { Session, ChatMessage } from '../../services/types';
import { api } from '../../services/api';
import { Send, Bot, User } from 'lucide-react';

export default function AIChatPanel({ session }: { session: Session }) {
  const [messages, setMessages] = useState<ChatMessage[]>(session.chatHistory);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = input;
    setInput('');
    
    // Optimistic UI
    const tempId = Date.now().toString();
    setMessages(prev => [...prev, { id: tempId, role: 'user', content: userMsg, timestamp: new Date().toISOString() }]);
    setIsTyping(true);

    try {
      const responseMsg = await api.sendChatMessage(session.id, userMsg);
      setMessages(prev => [...prev.filter(m => m.id !== tempId), 
         { id: tempId, role: 'user', content: userMsg, timestamp: new Date().toISOString() }, // keep user msg (real systems would sync from server)
         responseMsg
      ]);
    } catch (e) {
      console.error(e);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div style={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '24px' }} ref={scrollRef}>
        {messages.map(msg => (
          <div key={msg.id} style={{ display: 'flex', gap: '16px', alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '80%' }}>
            {msg.role === 'assistant' && (
              <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'rgba(0, 214, 255, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#00D6FF', flexShrink: 0 }}>
                <Bot size={20} />
              </div>
            )}
            
            <div style={{ 
              background: msg.role === 'user' ? 'var(--accent-blue)' : 'rgba(255,255,255,0.05)', 
              padding: '16px', 
              borderRadius: '16px',
              borderBottomRightRadius: msg.role === 'user' ? '4px' : '16px',
              borderBottomLeftRadius: msg.role === 'assistant' ? '4px' : '16px',
              color: '#fff',
              fontSize: '0.9375rem',
              lineHeight: 1.6
            }}>
              {msg.content}
            </div>

            {msg.role === 'user' && (
              <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'rgba(255, 255, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', flexShrink: 0 }}>
                <User size={20} />
              </div>
            )}
          </div>
        ))}
        
        {isTyping && (
          <div style={{ display: 'flex', gap: '16px', alignSelf: 'flex-start' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'rgba(0, 214, 255, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#00D6FF' }}>
              <Bot size={20} />
            </div>
            <div style={{ background: 'rgba(255,255,255,0.05)', padding: '16px', borderRadius: '16px', borderBottomLeftRadius: '4px', display: 'flex', gap: '4px', alignItems: 'center' }}>
              <div style={{ width: '8px', height: '8px', background: 'var(--text-secondary)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both' }}></div>
              <div style={{ width: '8px', height: '8px', background: 'var(--text-secondary)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.16s' }}></div>
              <div style={{ width: '8px', height: '8px', background: 'var(--text-secondary)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.32s' }}></div>
              <style>{`@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }`}</style>
            </div>
          </div>
        )}
      </div>

      <div style={{ padding: '16px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        <div style={{ display: 'flex', gap: '12px' }}>
          <input 
            type="text" 
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Ask the Explainer Agent a question about this EDI file..."
            style={{ 
              flex: 1, 
              background: 'rgba(0,0,0,0.3)', 
              border: '1px solid rgba(255,255,255,0.1)', 
              borderRadius: '24px', 
              padding: '12px 20px', 
              color: '#fff',
              outline: 'none',
              fontSize: '0.9375rem'
            }}
          />
          <button 
            className="btn btn-primary" 
            style={{ width: '46px', height: '46px', padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '50%' }}
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
          >
            <Send size={18} />
          </button>
        </div>
        <div style={{ display: 'flex', gap: '8px', marginTop: '12px', overflowX: 'auto', paddingBottom: '4px' }}>
          <span className="badge outline" style={{ cursor: 'pointer', whiteSpace: 'nowrap' }} onClick={() => setInput('Explain the NPI error.')}>Explain NPI error</span>
          <span className="badge outline" style={{ cursor: 'pointer', whiteSpace: 'nowrap' }} onClick={() => setInput('What does Loop 2300 mean?')}>What is Loop 2300?</span>
        </div>
      </div>
    </div>
  );
}
