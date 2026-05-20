"use client";

import { createContext, useContext, useState, ReactNode } from "react";

type User = {
  name: string;
  email: string;
  role: string;
  initials: string;
};

type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = async (email: string, password: string) => {
    // TODO: Replace with actual API call
    // For MVP, simulate login with hardcoded user
    await new Promise((resolve) => setTimeout(resolve, 500));
    
    setUser({
      name: "Sarah Miller",
      email: email,
      role: "Engineering",
      initials: "SM",
    });
  };

  const signup = async (name: string, email: string, password: string) => {
    // TODO: Replace with actual API call
    // For MVP, simulate signup
    await new Promise((resolve) => setTimeout(resolve, 500));
    
    const initials = name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
    
    setUser({
      name,
      email,
      role: "Engineering",
      initials,
    });
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        signup,
        logout,
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
