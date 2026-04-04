import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../services/types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loginState: (user: User) => void;
  logoutState: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check local storage on mount
    const storedUser = localStorage.getItem('edi_auth_user');
    if (storedUser) {
      try {
        const parsed = JSON.parse(storedUser);
        if (parsed?.token) {
          setUser(parsed);
        } else {
          localStorage.removeItem('edi_auth_user');
        }
      } catch (e) {
        localStorage.removeItem('edi_auth_user');
      }
    }
    setLoading(false);
  }, []);

  const loginState = (newUser: User) => {
    setUser(newUser);
    localStorage.setItem('edi_auth_user', JSON.stringify(newUser));
  };

  const logoutState = () => {
    setUser(null);
    localStorage.removeItem('edi_auth_user');
  };

  if (loading) {
    return <div>Loading...</div>; // Could be a nicer spinner later
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user?.token, loginState, logoutState }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
