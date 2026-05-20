"use client";

import { createContext, type ReactNode, useContext, useState } from "react";

type AuthContextType = {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  signup: (name: string, email: string, password: string) => Promise<void>;
  user: null | User;
};

type User = {
  email: string;
  initials: string;
  name: string;
  role: string;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<null | User>(null);

  const login = async (email: string, _password: string) => {
    await new Promise((resolve) => setTimeout(resolve, 500));
    setUser({
      email,
      initials: "SM",
      name: "Sarah Miller",
      role: "Engineering",
    });
  };

  const signup = async (name: string, email: string, _password: string) => {
    await new Promise((resolve) => setTimeout(resolve, 500));
    const initials = name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
    setUser({
      email,
      initials,
      name,
      role: "Engineering",
    });
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!user,
        login,
        logout,
        signup,
        user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
