import React, { createContext, useEffect, useState } from 'react';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [auth, setAuth] = useState({
    isAuthenticated: false,
    access_token: null,
    refresh_token: null,
    currentUser: null,
    isAdmin: false,
  });

  useEffect(() => {
    const access_token = localStorage.getItem('access_token');
    const refresh_token = localStorage.getItem('refresh_token');
    const currentUser = localStorage.getItem('current_user');
    if (access_token && currentUser) {
      setAuth({
        isAuthenticated: true,
        access_token,
        refresh_token,
        currentUser: JSON.parse(currentUser),
        isAdmin: false,
      });
    }
  }, []);

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('current_user');
    setAuth({
      isAuthenticated: false,
      access_token: null,
      refresh_token: null,
      currentUser: null,
      isAdmin: false,
    });
  };

  return (
    <AuthContext.Provider value={{ auth, setAuth, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
