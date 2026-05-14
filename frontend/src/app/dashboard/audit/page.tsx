"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { auditApi } from "@/lib/api";
import { formatDateTime, cn } from "@/lib/utils";
import { Card, Skeleton, EmptyState, Button } from "@/components/ui";
import { PageHeader } from "@/components/layout/sidebar";
import type { AuditLog, AuditAction } from "@/types";

const ACTION_CONFIG: Record<
  AuditAction,
  { label: string; icon: string; color: string }
> = {
  item_created: { label: "Item Created", icon: "📋", color: "text-blue-400" },
  ai_draft_generated: {
    label: "AI Draft Generated",
    icon: "🤖",
    color: "text-purple-400",
  },
  draft_regenerated: {
    label: "Draft Regenerated",
    icon: "🔄",
    color: "text-purple-400",
  },
  draft_edited: { label: "Draft Edited", icon: "✏️", color: "text-amber-400" },
  item_approved: {
    label: "Item Approved",
    icon: "✅",
    color: "text-emerald-400",
  },
  item_rejected: { label: "Item Rejected", icon: "❌", color: "text-red-400" },
  job_started: {
    label: "Job Started",
    icon: "⚙️",
    color: "text-indigo-400",
  },
  job_completed: {
    label: "Email Sent",
    icon: "📨",
    color: "text-emerald-400",
  },
  job_failed: { label: "Job Failed", icon: "⚠️", color: "text-red-400" },
  user_login: { label: "User Login", icon: "🔑", color: "text-blue-400" },
};

export default function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);

  const loadLogs = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await auditApi.list({ page, page_size: 50 });
      setLogs(data.items);
      setTotal(data.total);
    } catch {
      // Error handling
    } finally {
      setIsLoading(false);
    }
  }, [page]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  return (
    <div className="max-w-5xl mx-auto animate-fade-in">
      <PageHeader
        title="Audit Log"
        description="Track all actions performed on work items"
      />

      <Card>
        {isLoading ? (
          <div className="p-6 space-y-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="w-8 h-8 rounded-full" />
                <Skeleton className="flex-1 h-5" />
                <Skeleton className="w-32 h-5" />
              </div>
            ))}
          </div>
        ) : logs.length === 0 ? (
          <EmptyState
            title="No audit entries"
            description="Actions will be recorded here as users interact with work items."
            icon={
              <svg
                className="w-12 h-12"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            }
          />
        ) : (
          <div className="divide-y divide-[var(--color-border-subtle)]">
            {logs.map((log) => {
              const config = ACTION_CONFIG[log.action] || {
                label: log.action,
                icon: "📝",
                color: "text-[var(--color-text-muted)]",
              };
              return (
                <div
                  key={log.id}
                  className="flex items-start gap-4 px-5 py-4 hover:bg-[var(--color-bg-hover)] transition-colors"
                >
                  <span className="text-lg flex-shrink-0 mt-0.5">
                    {config.icon}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className={cn("text-sm font-medium", config.color)}>
                      {config.label}
                    </p>
                    <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                      by {log.actor_name || "System"}
                    </p>
                    {log.metadata_json &&
                      Object.keys(log.metadata_json).length > 0 && (
                        <div className="mt-1.5 flex flex-wrap gap-1.5">
                          {Object.entries(log.metadata_json).map(
                            ([key, value]) => (
                              <span
                                key={key}
                                className="inline-flex text-[10px] bg-[var(--color-bg-tertiary)] text-[var(--color-text-muted)] px-2 py-0.5 rounded"
                              >
                                {key}: {String(value).substring(0, 50)}
                              </span>
                            )
                          )}
                        </div>
                      )}
                  </div>
                  <div className="flex-shrink-0 text-right">
                    <p className="text-xs text-[var(--color-text-muted)]">
                      {formatDateTime(log.created_at)}
                    </p>
                    {log.work_item_id && (
                      <Link
                        href={`/dashboard/work-items/${log.work_item_id}`}
                        className="text-[10px] text-indigo-400 hover:text-indigo-300"
                      >
                        View item →
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Pagination */}
      {total > 50 && (
        <div className="flex justify-center gap-2 mt-6">
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <span className="flex items-center px-3 text-sm text-[var(--color-text-muted)]">
            Page {page} of {Math.ceil(total / 50)}
          </span>
          <Button
            variant="secondary"
            size="sm"
            disabled={page >= Math.ceil(total / 50)}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
