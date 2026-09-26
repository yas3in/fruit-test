import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "../api/client";

interface AuthContextType {
  token: string | null;
  username: string | null;
  isAuthenticated: boolean;
  login: (token: string, username: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem("fc_token"));
  const [username, setUsername] = useState<string | null>(localStorage.getItem("fc_user"));

  const login = (newToken: string, newUsername: string) => {
    localStorage.setItem("fc_token", newToken);
    localStorage.setItem("fc_user", newUsername);
    setToken(newToken);
    setUsername(newUsername);
  };

  const logout = () => {
    localStorage.removeItem("fc_token");
    localStorage.removeItem("fc_user");
    setToken(null);
    setUsername(null);
  };

  useEffect(() => {
    const handleExpired = () => logout();
    window.addEventListener("auth-expired", handleExpired);
    return () => window.removeEventListener("auth-expired", handleExpired);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        token,
        username,
        isAuthenticated: !!token,
        login,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};
