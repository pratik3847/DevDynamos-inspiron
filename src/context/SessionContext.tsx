import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';
import { Session } from '../services/types';

interface SessionContextType {
  activeSessionId: string | null;
  activeSession: Session | null;
  setActiveSessionId: (id: string | null) => void;
  refreshSession: () => Promise<void>;
  isLoading: boolean;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Load the session automatically when activeSessionId changes
  useEffect(() => {
    if (!activeSessionId) {
      setActiveSession(null);
      return;
    }

    const loadSession = async () => {
      setIsLoading(true);
      try {
        const session = await api.getSession(activeSessionId);
        setActiveSession(session);
      } catch (err) {
        console.error("Failed to load session:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadSession();
  }, [activeSessionId]);

  const refreshSession = async () => {
    if (!activeSessionId) return;
    setIsLoading(true);
    try {
      const session = await api.getSession(activeSessionId);
      setActiveSession(session);
    } catch (err) {
      console.error("Failed to refresh session:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SessionContext.Provider value={{ activeSessionId, activeSession, setActiveSessionId, refreshSession, isLoading }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
}
