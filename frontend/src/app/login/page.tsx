"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Button, Input, Toast } from "@/components/ui";

export default function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await login(email, password);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Login failed. Please try again.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="skeleton w-8 h-8 rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {/* Background gradient effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 mb-4 shadow-lg shadow-indigo-500/20">
            <svg
              className="w-7 h-7 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
            Welcome back
          </h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Sign in to the AI Sales Workbench
          </p>
        </div>

        {/* Login Form */}
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-6 shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              id="email"
              label="Email"
              type="email"
              placeholder="admin@acmecorp.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />

            <Input
              id="password"
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              error={error}
            />

            <Button
              type="submit"
              className="w-full"
              size="lg"
              isLoading={isSubmitting}
            >
              Sign in
            </Button>
          </form>
        </div>

        {/* Test Credentials */}
        <div className="mt-6 rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-bg-secondary)]/50 p-4">
          <p className="text-xs font-medium text-[var(--color-text-muted)] mb-3 uppercase tracking-wider">
            Test Credentials
          </p>
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => {
                setEmail("admin@acmecorp.com");
                setPassword("admin123");
              }}
              className="w-full text-left px-3 py-2 rounded-lg text-xs bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-hover)] transition-all border border-transparent hover:border-[var(--color-border)] cursor-pointer"
            >
              <span className="text-[var(--color-text-primary)] font-medium">
                Admin
              </span>
              <span className="text-[var(--color-text-muted)] ml-2">
                admin@acmecorp.com
              </span>
            </button>
            <button
              type="button"
              onClick={() => {
                setEmail("reviewer@acmecorp.com");
                setPassword("reviewer123");
              }}
              className="w-full text-left px-3 py-2 rounded-lg text-xs bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-hover)] transition-all border border-transparent hover:border-[var(--color-border)] cursor-pointer"
            >
              <span className="text-[var(--color-text-primary)] font-medium">
                Reviewer
              </span>
              <span className="text-[var(--color-text-muted)] ml-2">
                reviewer@acmecorp.com
              </span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <Toast message={error} type="error" onClose={() => setError("")} />
      )}
    </div>
  );
}
