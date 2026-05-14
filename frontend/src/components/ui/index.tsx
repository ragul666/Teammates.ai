"use client";

import { type ReactNode } from "react";
import { cn } from "@/lib/utils";
import type { WorkItemStatus } from "@/types";

/* ===== Status Badge ===== */

const STATUS_CONFIG: Record<
  WorkItemStatus,
  { label: string; className: string; dot: string }
> = {
  pending_review: {
    label: "Pending Review",
    className: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    dot: "bg-amber-400",
  },
  approved: {
    label: "Approved",
    className: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    dot: "bg-blue-400",
  },
  rejected: {
    label: "Rejected",
    className: "bg-red-500/10 text-red-400 border-red-500/20",
    dot: "bg-red-400",
  },
  regenerating: {
    label: "Regenerating",
    className: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    dot: "bg-purple-400 animate-pulse-dot",
  },
  processing: {
    label: "Processing",
    className: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    dot: "bg-indigo-400 animate-pulse-dot",
  },
  sent: {
    label: "Sent",
    className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    dot: "bg-emerald-400",
  },
  failed: {
    label: "Failed",
    className: "bg-red-500/10 text-red-400 border-red-500/20",
    dot: "bg-red-400",
  },
};

export function StatusBadge({ status }: { status: WorkItemStatus }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending_review;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full border",
        config.className
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", config.dot)} />
      {config.label}
    </span>
  );
}

/* ===== Button ===== */

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost" | "success";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  isLoading = false,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const variants = {
    primary:
      "bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm",
    secondary:
      "bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-hover)] text-[var(--color-text-primary)] border border-[var(--color-border)]",
    danger:
      "bg-red-600/10 hover:bg-red-600/20 text-red-400 border border-red-500/20",
    ghost:
      "hover:bg-[var(--color-bg-hover)] text-[var(--color-text-secondary)]",
    success:
      "bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-2.5 text-base",
  };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all duration-150 cursor-pointer",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg
          className="animate-spin h-4 w-4"
          viewBox="0 0 24 24"
          fill="none"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}

/* ===== Card ===== */

export function Card({
  children,
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

/* ===== Input ===== */

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({
  label,
  error,
  className,
  id,
  ...props
}: InputProps) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label
          htmlFor={id}
          className="block text-sm font-medium text-[var(--color-text-secondary)]"
        >
          {label}
        </label>
      )}
      <input
        id={id}
        className={cn(
          "w-full px-3 py-2.5 rounded-lg text-sm",
          "bg-[var(--color-bg-tertiary)] border border-[var(--color-border)]",
          "text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)]",
          "focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500",
          "transition-all duration-150",
          error && "border-red-500 focus:ring-red-500/40",
          className
        )}
        {...props}
      />
      {error && (
        <p className="text-xs text-red-400">{error}</p>
      )}
    </div>
  );
}

/* ===== Textarea ===== */

interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

export function Textarea({
  label,
  className,
  id,
  ...props
}: TextareaProps) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label
          htmlFor={id}
          className="block text-sm font-medium text-[var(--color-text-secondary)]"
        >
          {label}
        </label>
      )}
      <textarea
        id={id}
        className={cn(
          "w-full px-3 py-2.5 rounded-lg text-sm",
          "bg-[var(--color-bg-tertiary)] border border-[var(--color-border)]",
          "text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)]",
          "focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500",
          "transition-all duration-150 resize-y min-h-[120px]",
          className
        )}
        {...props}
      />
    </div>
  );
}

/* ===== Skeleton ===== */

export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("skeleton h-4", className)} {...props} />;
}

/* ===== Empty State ===== */

export function EmptyState({
  title,
  description,
  icon,
}: {
  title: string;
  description: string;
  icon?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {icon && (
        <div className="mb-4 text-[var(--color-text-muted)]">{icon}</div>
      )}
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-1">
        {title}
      </h3>
      <p className="text-sm text-[var(--color-text-muted)] max-w-md">
        {description}
      </p>
    </div>
  );
}

/* ===== Toast ===== */

export function Toast({
  message,
  type = "success",
  onClose,
}: {
  message: string;
  type?: "success" | "error" | "info";
  onClose: () => void;
}) {
  const colors = {
    success: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
    error: "bg-red-500/10 border-red-500/20 text-red-400",
    info: "bg-blue-500/10 border-blue-500/20 text-blue-400",
  };

  return (
    <div
      className={cn(
        "fixed bottom-6 right-6 z-50 px-4 py-3 rounded-lg border shadow-lg",
        "animate-slide-in backdrop-blur-sm",
        colors[type]
      )}
    >
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium">{message}</span>
        <button
          onClick={onClose}
          className="text-current opacity-60 hover:opacity-100 cursor-pointer"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

/* ===== Stats Card ===== */

export function StatsCard({
  title,
  value,
  icon,
  color = "indigo",
}: {
  title: string;
  value: number;
  icon: ReactNode;
  color?: "indigo" | "emerald" | "amber" | "red" | "blue";
}) {
  const colors = {
    indigo: "from-indigo-500/20 to-indigo-500/5 border-indigo-500/20",
    emerald: "from-emerald-500/20 to-emerald-500/5 border-emerald-500/20",
    amber: "from-amber-500/20 to-amber-500/5 border-amber-500/20",
    red: "from-red-500/20 to-red-500/5 border-red-500/20",
    blue: "from-blue-500/20 to-blue-500/5 border-blue-500/20",
  };

  return (
    <div
      className={cn(
        "rounded-xl border bg-gradient-to-br p-5",
        colors[color]
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-[var(--color-text-muted)] text-sm">
          {title}
        </span>
        <span className="text-[var(--color-text-muted)]">{icon}</span>
      </div>
      <p className="text-3xl font-bold text-[var(--color-text-primary)]">
        {value}
      </p>
    </div>
  );
}
