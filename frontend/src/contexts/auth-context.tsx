"use client";

import { createContext, useContext } from "react";

type AuthContextType = {
  isAuthenticated: boolean;
  user: null | User;
};

type User = {
  email: string;
  initials: string;
  name: string;
  role: string;
};

const MOCK_USER: User = {
  email: "sarah.miller@company.com",
  initials: "SM",
  name: "Sarah Miller",
  role: "Engineering",
};

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: true,
  user: MOCK_USER,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return (
    <AuthContext.Provider value={{ isAuthenticated: true, user: MOCK_USER }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
