import { useMemo, useRef, useState } from 'react';
import { Bot, Send, X, Sparkles } from 'lucide-react';

type EddieTheme = 'dark' | 'light';

type EddieMessage = {
  id: string;
  role: 'assistant' | 'user';
  content: string;
};

type EddieAssistantProps = {
  theme: EddieTheme;
};

const QUICK_TOPICS = [
  'How do I upload a file?',
  'Show parser details',
  'What validation errors matter?',
  'How do I fix this claim?',
];

export default function EddieAssistant({ theme }: EddieAssistantProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState<EddieMessage[]>([
    {
      id: 'eddie-welcome',
      role: 'assistant',
      content: 'Hi, I am Eddie. Ask me about upload, parser, validation, or fixes.'
    }
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const palette = useMemo(() => {
    const dark = {
      shell: 'rgba(8, 12, 24, 0.82)',
      panel: 'rgba(15, 20, 36, 0.96)',
      border: 'rgba(0, 214, 255, 0.22)',
      text: '#F4FAFF',
      muted: 'rgba(244, 250, 255, 0.62)',
      bubble: 'rgba(0, 80, 255, 0.18)',
      bubbleBorder: 'rgba(0, 214, 255, 0.18)',
      userBg: 'rgba(0, 214, 255, 0.14)',
      assistantBg: 'rgba(255, 255, 255, 0.06)',
    };

    const light = {
      shell: 'rgba(248, 250, 255, 0.92)',
      panel: 'rgba(255, 255, 255, 0.98)',
      border: 'rgba(6, 113, 219, 0.24)',
      text: '#0B0E14',
      muted: 'rgba(11, 14, 20, 0.62)',
      bubble: 'rgba(6, 113, 219, 0.12)',
      bubbleBorder: 'rgba(6, 113, 219, 0.16)',
      userBg: 'rgba(6, 113, 219, 0.12)',
      assistantBg: 'rgba(11, 14, 20, 0.04)',
    };

    return theme === 'light' ? light : dark;
  }, [theme]);

  const scrollToBottom = () => {
    window.requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    });
  };

  const sendMessage = async (value: string) => {
    const text = value.trim();
    if (!text || isSending) return;

    const userMessage: EddieMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
    };

    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInputValue('');
    scrollToBottom();

    setIsSending(true);
    try {
      const response = await fetch('/api/ai/eddie-chat', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: nextMessages.map((m) => ({ role: m.role, content: m.content })),
          page_context: window.location.pathname,
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to reach Eddie backend');
      }

      const result = await response.json();
      const assistantText =
        result?.data?.response ||
        result?.data?.answer ||
        'I could not generate a response right now.';

      const assistantMessage: EddieMessage = {
        id: `eddie-${Date.now()}`,
        role: 'assistant',
        content: String(assistantText),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      scrollToBottom();
    } catch (e: any) {
      const assistantError: EddieMessage = {
        id: `eddie-error-${Date.now()}`,
        role: 'assistant',
        content: e?.message || 'Eddie backend is unavailable right now.',
      };
      setMessages((prev) => [...prev, assistantError]);
      scrollToBottom();
    } finally {
      setIsSending(false);
    }
  };

  const openWithTopic = (topic: string) => {
    setIsOpen(true);
    void sendMessage(topic);
  };

  return (
    <div
      style={{
        position: 'fixed',
        right: '24px',
        bottom: '24px',
        zIndex: 90,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        gap: '12px',
      }}
    >
      {isOpen && (
        <div
          style={{
            width: '320px',
            maxWidth: 'calc(100vw - 32px)',
            height: '420px',
            background: palette.panel,
            border: `1px solid ${palette.border}`,
            borderRadius: '18px',
            boxShadow: '0 24px 60px rgba(0, 0, 0, 0.35)',
            overflow: 'hidden',
            backdropFilter: 'blur(22px)',
            WebkitBackdropFilter: 'blur(22px)',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '14px 16px',
              borderBottom: `1px solid ${palette.border}`,
              background: palette.shell,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: 'linear-gradient(135deg, #0050FF, #00D6FF)',
                  color: '#fff',
                }}
              >
                <Bot size={18} />
              </div>
              <div>
                <div style={{ color: palette.text, fontWeight: 700, fontSize: '0.95rem' }}>Eddie</div>
                <div style={{ color: palette.muted, fontSize: '0.72rem' }}>UI assistant only</div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '10px',
                border: 'none',
                background: palette.bubble,
                color: palette.text,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              aria-label="Close Eddie"
            >
              <X size={16} />
            </button>
          </div>

          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '14px 14px 8px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            {messages.map((message) => (
              <div
                key={message.id}
                style={{
                  alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '88%',
                  background: message.role === 'user' ? palette.userBg : palette.assistantBg,
                  color: palette.text,
                  border: `1px solid ${palette.border}`,
                  borderRadius: '14px',
                  padding: '10px 12px',
                  fontSize: '0.875rem',
                  lineHeight: 1.45,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {message.content}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div style={{ padding: '0 14px 12px' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '10px' }}>
              {QUICK_TOPICS.map((topic) => (
                <button
                  key={topic}
                  type="button"
                  onClick={() => openWithTopic(topic)}
                  style={{
                    border: `1px solid ${palette.border}`,
                    background: palette.bubble,
                    color: palette.text,
                    borderRadius: '999px',
                    padding: '6px 10px',
                    fontSize: '0.72rem',
                    cursor: 'pointer',
                  }}
                >
                  <Sparkles size={12} style={{ marginRight: '6px', verticalAlign: '-1px' }} />
                  {topic}
                </button>
              ))}
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                void sendMessage(inputValue);
              }}
              style={{ display: 'flex', gap: '8px' }}
            >
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask Eddie anything..."
                disabled={isSending}
                style={{
                  flex: 1,
                  minWidth: 0,
                  borderRadius: '12px',
                  border: `1px solid ${palette.border}`,
                  background: palette.shell,
                  color: palette.text,
                  padding: '10px 12px',
                  outline: 'none',
                  fontSize: '0.875rem',
                }}
              />
              <button
                type="submit"
                disabled={isSending}
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '12px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #0050FF, #00D6FF)',
                  color: '#fff',
                  cursor: isSending ? 'not-allowed' : 'pointer',
                  opacity: isSending ? 0.7 : 1,
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
                aria-label="Send to Eddie"
              >
                <Send size={16} />
              </button>
            </form>
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label="Ask Eddie"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: 'none',
          background: 'transparent',
          padding: 0,
          cursor: 'pointer',
          boxShadow: 'none',
          backdropFilter: 'none',
          WebkitBackdropFilter: 'none',
        }}
      >
        <div
          style={{
            width: '52px',
            height: '52px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #0050FF, #00D6FF)',
            border: 'none',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            position: 'relative',
            zIndex: 2,
          }}
        >
          <Bot size={18} strokeWidth={1.9} />
        </div>
      </button>
    </div>
  );
}