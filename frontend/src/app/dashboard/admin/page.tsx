"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { adminApi } from "@/lib/api";
import { Card, Skeleton, StatsCard } from "@/components/ui";
import { PageHeader } from "@/components/layout/sidebar";
import type { DashboardStats } from "@/types";

export default function AdminDashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Client-side role check (server-side check happens on API)
  useEffect(() => {
    if (user && user.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [user, router]);

  const loadStats = useCallback(async () => {
    try {
      const data = await adminApi.dashboard();
      setStats(data);
    } catch {
      // Will be handled by API client (403 redirect)
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 15000);
    return () => clearInterval(interval);
  }, [loadStats]);

  if (user?.role !== "admin") {
    return null;
  }

  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      <PageHeader
        title="Admin Dashboard"
        description={`Organization overview · ${user?.organization_name}`}
      />

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(7)].map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      ) : stats ? (
        <div className="space-y-8">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatsCard
              title="Total Items"
              value={stats.total_items}
              color="indigo"
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 110 3.75H5.625a1.875 1.875 0 010-3.75z" />
                </svg>
              }
            />
            <StatsCard
              title="Pending Review"
              value={stats.pending_review}
              color="amber"
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />
            <StatsCard
              title="Sent"
              value={stats.sent}
              color="emerald"
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              }
            />
            <StatsCard
              title="Failed"
              value={stats.failed}
              color="red"
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
              }
            />
          </div>

          {/* Secondary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--color-text-muted)]">Processing</span>
                <span className="text-2xl font-bold text-indigo-400">
                  {stats.processing}
                </span>
              </div>
            </Card>
            <Card className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--color-text-muted)]">Approved</span>
                <span className="text-2xl font-bold text-blue-400">
                  {stats.approved}
                </span>
              </div>
            </Card>
            <Card className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--color-text-muted)]">Rejected</span>
                <span className="text-2xl font-bold text-red-400">
                  {stats.rejected}
                </span>
              </div>
            </Card>
          </div>

          {/* Quick Overview */}
          <Card className="p-5">
            <h2 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider mb-4">
              Pipeline Overview
            </h2>
            <div className="h-4 rounded-full bg-[var(--color-bg-tertiary)] overflow-hidden flex">
              {stats.total_items > 0 && (
                <>
                  {stats.sent > 0 && (
                    <div
                      className="bg-emerald-500 transition-all duration-500"
                      style={{
                        width: `${(stats.sent / stats.total_items) * 100}%`,
                      }}
                    />
                  )}
                  {stats.pending_review > 0 && (
                    <div
                      className="bg-amber-500 transition-all duration-500"
                      style={{
                        width: `${(stats.pending_review / stats.total_items) * 100}%`,
                      }}
                    />
                  )}
                  {stats.processing > 0 && (
                    <div
                      className="bg-indigo-500 transition-all duration-500"
                      style={{
                        width: `${(stats.processing / stats.total_items) * 100}%`,
                      }}
                    />
                  )}
                  {stats.failed > 0 && (
                    <div
                      className="bg-red-500 transition-all duration-500"
                      style={{
                        width: `${(stats.failed / stats.total_items) * 100}%`,
                      }}
                    />
                  )}
                  {stats.rejected > 0 && (
                    <div
                      className="bg-red-400/50 transition-all duration-500"
                      style={{
                        width: `${(stats.rejected / stats.total_items) * 100}%`,
                      }}
                    />
                  )}
                </>
              )}
            </div>
            <div className="flex flex-wrap gap-4 mt-3">
              <span className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Sent
              </span>
              <span className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Pending
              </span>
              <span className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" /> Processing
              </span>
              <span className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Failed
              </span>
              <span className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
                <span className="w-2.5 h-2.5 rounded-full bg-red-400/50" /> Rejected
              </span>
            </div>
          </Card>
        </div>
      ) : (
        <Card className="p-8 text-center">
          <p className="text-[var(--color-text-muted)]">
            Failed to load dashboard data.
          </p>
        </Card>
      )}
    </div>
  );
}
