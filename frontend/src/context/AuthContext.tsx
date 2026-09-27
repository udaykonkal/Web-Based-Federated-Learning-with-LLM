import React, { createContext, useContext, useState, useEffect } from 'react';
import type { UserRole, TokenResponse } from '../types';

interface AuthContextType {
  token: string | null;
  role: UserRole | null;
  email: string | null;
  clientId: string | null;
  institutionName: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isClient: boolean;
  login: (authData: TokenResponse) => void;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [role, setRole] = useState<UserRole | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [clientId, setClientId] = useState<string | null>(null);
  const [institutionName, setInstitutionName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const syncAuthFromStorage = () => {
    const savedToken = localStorage.getItem('fl_auth_token');
    const savedData = localStorage.getItem('fl_auth_data');

    if (savedToken && savedData) {
      try {
        const parsed = JSON.parse(savedData) as TokenResponse;
        setToken(savedToken);
        setRole(parsed.role);
        setEmail(parsed.email);
        setClientId(parsed.client_id);
        setInstitutionName(parsed.institution_name);
      } catch (err) {
        localStorage.removeItem('fl_auth_token');
        localStorage.removeItem('fl_auth_data');
        setToken(null);
        setRole(null);
        setEmail(null);
        setClientId(null);
        setInstitutionName(null);
      }
    } else {
      setToken(null);
      setRole(null);
      setEmail(null);
      setClientId(null);
      setInstitutionName(null);
    }
  };

  useEffect(() => {
    syncAuthFromStorage();
    setLoading(false);

    const handleStorageChange = () => {
      syncAuthFromStorage();
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const login = (authData: TokenResponse) => {
    setToken(authData.access_token);
    setRole(authData.role);
    setEmail(authData.email);
    setClientId(authData.client_id);
    setInstitutionName(authData.institution_name);

    localStorage.setItem('fl_auth_token', authData.access_token);
    localStorage.setItem('fl_auth_data', JSON.stringify(authData));
  };

  const logout = () => {
    setToken(null);
    setRole(null);
    setEmail(null);
    setClientId(null);
    setInstitutionName(null);

    localStorage.removeItem('fl_auth_token');
    localStorage.removeItem('fl_auth_data');
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        role,
        email,
        clientId,
        institutionName,
        isAuthenticated: !!token,
        isAdmin: role === 'admin',
        isClient: role === 'client',
        login,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
