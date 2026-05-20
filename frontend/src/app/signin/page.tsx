"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/contexts/auth-context";

export default function SignInPage() {
  const router = useRouter();
  const { login, signup } = useAuth();
  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      if (isSignUp) {
        await signup(name, email, password);
      } else {
        await login(email, password);
      }
      router.push("/dashboard");
    } catch (_err) {
      setError("Authentication failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="w-full max-w-md rounded-lg border border-border bg-card p-8 shadow-sm">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-semibold text-foreground">
            My<span className="text-brand-purple-600">Perks</span>
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            {isSignUp ? "Create your account" : "Sign in to your account"}
          </p>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          {isSignUp && (
            <div>
              <label
                className="mb-1.5 block text-sm font-medium text-foreground"
                htmlFor="name"
              >
                Name
              </label>
              <input
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-brand-purple-500 focus:outline-none focus:ring-1 focus:ring-brand-purple-500"
                id="name"
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your name"
                required
                type="text"
                value={name}
              />
            </div>
          )}

          <div>
            <label
              className="mb-1.5 block text-sm font-medium text-foreground"
              htmlFor="email"
            >
              Email
            </label>
            <input
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-brand-purple-500 focus:outline-none focus:ring-1 focus:ring-brand-purple-500"
              id="email"
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
              type="email"
              value={email}
            />
          </div>

          <div>
            <label
              className="mb-1.5 block text-sm font-medium text-foreground"
              htmlFor="password"
            >
              Password
            </label>
            <input
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-brand-purple-500 focus:outline-none focus:ring-1 focus:ring-brand-purple-500"
              id="password"
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              type="password"
              value={password}
            />
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <button
            className="w-full rounded-lg bg-brand-purple-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-purple-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isLoading}
            type="submit"
          >
            {isLoading ? "Loading..." : isSignUp ? "Sign Up" : "Sign In"}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            className="text-sm text-muted-foreground hover:text-brand-purple-600"
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError("");
            }}
            type="button"
          >
            {isSignUp
              ? "Already have an account? Sign in"
              : "Don't have an account? Sign up"}
          </button>
        </div>
      </div>
    </div>
  );
}
