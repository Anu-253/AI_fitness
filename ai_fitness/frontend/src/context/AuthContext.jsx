import React, { createContext, useContext, useState, useCallback } from 'react';
import { login as apiLogin, register as apiRegister } from '../utils/api';

const AuthContext = createContext(null);

const GUEST_PSEUDO_TOKEN = 'guest-no-token';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('fitness_user');
      if (!stored) return null;
      const parsed = JSON.parse(stored);
      // Don't auto-restore guest — always show landing page first
      if (parsed?.username === 'Guest') {
        localStorage.removeItem('fitness_token');
        localStorage.removeItem('fitness_user');
        localStorage.removeItem('fitness_user_id');
        localStorage.removeItem('fitness_username');
        return null;
      }
      return parsed;
    } catch {
      return null;
    }
  });

  const _persist = (userData, token) => {
    localStorage.setItem('fitness_token',    token);
    localStorage.setItem('fitness_user_id',  userData.user_id);
    localStorage.setItem('fitness_username', userData.username);
    localStorage.setItem('fitness_user',     JSON.stringify(userData));
    setUser(userData);
  };

  const login = useCallback(async (username, password) => {
    const res = await apiLogin({ username, password });
    const { access_token, user_id } = res.data;
    const userData = { username, user_id };
    _persist(userData, access_token);
    return userData;
  }, []);

  const register = useCallback(async (username, email, password) => {
    const res = await apiRegister({ username, email, password });
    const { access_token, user_id } = res.data;
    const userData = { username, user_id };
    _persist(userData, access_token);
    return userData;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('fitness_token');
    localStorage.removeItem('fitness_user_id');
    localStorage.removeItem('fitness_username');
    localStorage.removeItem('fitness_user');
    setUser(null);
  }, []);

  const guestLogin = useCallback(() => {
    const userData = { username: 'Guest', user_id: 'default_user' };
    localStorage.setItem('fitness_token',    GUEST_PSEUDO_TOKEN);
    localStorage.setItem('fitness_user_id',  'default_user');
    localStorage.setItem('fitness_username', 'Guest');
    localStorage.setItem('fitness_user',     JSON.stringify(userData));
    setUser(userData);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, register, logout, guestLogin }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
