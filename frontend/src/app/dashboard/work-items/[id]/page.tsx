"use client";

import { useState, useEffect, useCallback, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { workItemsApi, auditApi } from "@/lib/api";
import { formatDateTime, cn } from "@/lib/utils";
import {
  StatusBadge,
  Button,
  Card,
  Textarea,
  Skeleton,
  Toast,
} from "@/components/ui";
import type { WorkItem, AuditLog, AuditAction } from "@/types";

/* ===== Audit Action Labels ===== */

const ACTION_LABELS: Record<AuditAction, { label: string; icon: string; color: string }> = {
  item_created: { label: "Item created", icon: "📋", color: "text-blue-400" },
  ai_draft_generated: { label: "AI draft generated", icon: "🤖", color: "text-purple-400" },
  draft_regenerated: { label: "Draft regenerated", icon: "🔄", color: "text-purple-400" },
  draft_edited: { label: "Draft edited", icon: "✏️", color: "text-amber-400" },
  item_approved: { label: "Approved", icon: "✅", color: "text-emerald-400" },
  item_rejected: { label: "Rejected", icon: "❌", color: "text-red-400" },
  job_started: { label: "Processing started", icon: "⚙️", color: "text-indigo-400" },
  job_completed: { label: "Email sent", icon: "📨", color: "text-emerald-400" },
  job_failed: { label: "Processing failed", icon: "⚠️", color: "text-red-400" },
  user_login: { label: "User login", icon: "🔑", color: "text-blue-400" },
};

export default function ReviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const router = useRouter();
  const { user } = useAuth();

  const [item, setItem] = useState<WorkItem | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [editedContent, setEditedContent] = useState("");
  const [note, setNote] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);

  const showToast = (message: string, type: "success" | "error" | "info" = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const loadData = useCallback(async () => {
    try {
      const [itemData, logsData] = await Promise.all([
        workItemsApi.get(resolvedParams.id),
        auditApi.byWorkItem(resolvedParams.id),
      ]);
      setItem(itemData);
      setAuditLogs(logsData);
      // Initialize edit content
      if (!isEditing) {
        setEditedContent(itemData.edited_output || itemData.ai_output);
      }
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Failed to load work item",
        "error"
      );
    } finally {
      setIsLoading(false);
    }
  }, [resolvedParams.id, isEditing]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Poll for status updates when processing
  useEffect(() => {
    if (
      item &&
      (item.status === "processing" || item.status === "approved")
    ) {
      const interval = setInterval(loadData, 2000);
      return () => clearInterval(interval);
    }
  }, [item?.status, loadData]);

  const handleApprove = async () => {
    if (actionLoading) return;
    setActionLoading("approve");
    try {
      const updated = await workItemsApi.approve(
        resolvedParams.id,
        note || undefined,
        isEditing ? editedContent : undefined
      );
      setItem(updated);
      setIsEditing(false);
      showToast("Draft approved successfully. Processing will begin shortly.");
      loadData();
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Failed to approve",
        "error"
      );
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async () => {
    if (actionLoading) return;
    setActionLoading("reject");
    try {
      const updated = await workItemsApi.reject(
        resolvedParams.id,
        note || undefined
      );
      setItem(updated);
      showToast("Draft rejected.", "info");
      loadData();
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Failed to reject",
        "error"
      );
    } finally {
      setActionLoading(null);
    }
  };

  const handleRegenerate = async () => {
    if (actionLoading) return;
    setActionLoading("regenerate");
    try {
      const updated = await workItemsApi.regenerate(resolvedParams.id);
      setItem(updated);
      setEditedContent(updated.ai_output);
      setIsEditing(false);
      showToast("Draft regenerated with fresh AI output.");
      loadData();
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Failed to regenerate",
        "error"
      );
    } finally {
      setActionLoading(null);
    }
  };

  const handleRetry = async () => {
    if (actionLoading) return;
    setActionLoading("retry");
    try {
      const updated = await workItemsApi.retry(resolvedParams.id);
      setItem(updated);
      showToast("Retrying failed email delivery...");
      loadData();
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Failed to retry",
        "error"
      );
    } finally {
      setActionLoading(null);
    }
  };

  const handleSaveEdit = async () => {
    if (actionLoading) return;
    setActionLoading("save");
    try {
      const updated = await workItemsApi.update(
        resolvedParams.id,
        editedContent
      );
      setItem(updated);
      setIsEditing(false);
      showToast("Draft saved.");
      loadData();
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Failed to save",
        "error"
      );
    } finally {
      setActionLoading(null);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto animate-fade-in">
        <div className="flex items-center gap-3 mb-8">
          <Skeleton className="w-8 h-8 rounded" />
          <Skeleton className="w-48 h-6" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Skeleton className="w-full h-64" />
            <Skeleton className="w-full h-48" />
          </div>
          <div className="space-y-6">
            <Skeleton className="w-full h-48" />
            <Skeleton className="w-full h-32" />
          </div>
        </div>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="max-w-6xl mx-auto text-center py-16">
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">
          Work item not found
        </h2>
        <Link
          href="/dashboard"
          className="text-indigo-400 hover:text-indigo-300 text-sm mt-2 inline-block"
        >
          ← Back to queue
        </Link>
      </div>
    );
  }

  const isPending = item.status === "pending_review";
  const isFailed = item.status === "failed";
  const isProcessing = item.status === "processing" || item.status === "approved";

  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="p-2 rounded-lg hover:bg-[var(--color-bg-hover)] text-[var(--color-text-muted)] transition-colors"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15.75 19.5L8.25 12l7.5-7.5"
              />
            </svg>
          </Link>
          <div>
            <h1 className="text-xl font-bold text-[var(--color-text-primary)]">
              {item.lead_name}
            </h1>
            <p className="text-sm text-[var(--color-text-muted)]">
              {item.company_name}
            </p>
          </div>
        </div>
        <StatusBadge status={item.status} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content — Left 2/3 */}
        <div className="lg:col-span-2 space-y-6">
          {/* Lead Context */}
          <Card className="p-5">
            <h2 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider mb-3">
              Lead Context
            </h2>
            <p className="text-sm text-[var(--color-text-primary)] leading-relaxed">
              {item.lead_context}
            </p>
            <div className="mt-4 pt-4 border-t border-[var(--color-border-subtle)]">
              <h3 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">
                Original Signal
              </h3>
              <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed italic">
                &ldquo;{item.original_input}&rdquo;
              </p>
            </div>
          </Card>

          {/* AI Draft / Editor */}
          <Card className="p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                {isEditing ? "Edit Draft" : "AI-Generated Follow-up"}
              </h2>
              {isPending && !isEditing && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsEditing(true)}
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                  </svg>
                  Edit
                </Button>
              )}
            </div>

            {isEditing ? (
              <div className="space-y-4">
                <Textarea
                  id="draft-editor"
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  className="min-h-[300px] font-mono text-sm"
                />
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleSaveEdit}
                    isLoading={actionLoading === "save"}
                  >
                    Save Changes
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setIsEditing(false);
                      setEditedContent(
                        item.edited_output || item.ai_output
                      );
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <div className="bg-[var(--color-bg-tertiary)] rounded-lg p-4 border border-[var(--color-border-subtle)]">
                <pre className="text-sm text-[var(--color-text-primary)] whitespace-pre-wrap font-sans leading-relaxed">
                  {item.edited_output || item.ai_output}
                </pre>
              </div>
            )}

            {item.edited_output && !isEditing && (
              <p className="text-xs text-[var(--color-text-muted)] mt-2 flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                </svg>
                Edited by reviewer
              </p>
            )}
          </Card>

          {/* Reviewer Note */}
          {isPending && (
            <Card className="p-5">
              <Textarea
                id="reviewer-note"
                label="Reviewer Note (optional)"
                placeholder="Add a note explaining your decision..."
                value={note}
                onChange={(e) => setNote(e.target.value)}
                className="min-h-[80px]"
              />
            </Card>
          )}
        </div>

        {/* Right Sidebar — Actions & Timeline */}
        <div className="space-y-6">
          {/* Actions */}
          <Card className="p-5">
            <h2 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider mb-4">
              Actions
            </h2>
            <div className="space-y-2.5">
              {isPending && (
                <>
                  <Button
                    variant="success"
                    className="w-full"
                    onClick={handleApprove}
                    isLoading={actionLoading === "approve"}
                    disabled={!!actionLoading}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                    Approve & Send
                  </Button>
                  <Button
                    variant="danger"
                    className="w-full"
                    onClick={handleReject}
                    isLoading={actionLoading === "reject"}
                    disabled={!!actionLoading}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    Reject
                  </Button>
                  <Button
                    variant="secondary"
                    className="w-full"
                    onClick={handleRegenerate}
                    isLoading={actionLoading === "regenerate"}
                    disabled={!!actionLoading}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                    </svg>
                    Regenerate Draft
                  </Button>
                </>
              )}
              {isFailed && (
                <Button
                  variant="primary"
                  className="w-full"
                  onClick={handleRetry}
                  isLoading={actionLoading === "retry"}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                  </svg>
                  Retry Sending
                </Button>
              )}
              {isProcessing && (
                <div className="flex items-center gap-3 p-3 bg-indigo-500/10 rounded-lg border border-indigo-500/20">
                  <svg className="animate-spin w-5 h-5 text-indigo-400" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span className="text-sm text-indigo-400">
                    Processing email delivery...
                  </span>
                </div>
              )}
              {item.status === "sent" && (
                <div className="flex items-center gap-3 p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                  <span className="text-lg">✅</span>
                  <span className="text-sm text-emerald-400">
                    Email sent successfully
                  </span>
                </div>
              )}
              {item.status === "rejected" && (
                <>
                  <div className="flex items-center gap-3 p-3 bg-red-500/10 rounded-lg border border-red-500/20">
                    <span className="text-lg">❌</span>
                    <span className="text-sm text-red-400">
                      Draft was rejected
                    </span>
                  </div>
                  <Button
                    variant="secondary"
                    className="w-full"
                    onClick={handleRegenerate}
                    isLoading={actionLoading === "regenerate"}
                    disabled={!!actionLoading}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                    </svg>
                    Regenerate Draft
                  </Button>
                </>
              )}
            </div>

            {item.reviewer_note && (
              <div className="mt-4 pt-4 border-t border-[var(--color-border-subtle)]">
                <p className="text-xs font-medium text-[var(--color-text-muted)] mb-1">
                  Reviewer Note
                </p>
                <p className="text-sm text-[var(--color-text-secondary)]">
                  {item.reviewer_note}
                </p>
              </div>
            )}
          </Card>

          {/* Activity Timeline */}
          <Card className="p-5">
            <h2 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider mb-4">
              Activity Timeline
            </h2>
            {auditLogs.length === 0 ? (
              <p className="text-xs text-[var(--color-text-muted)]">
                No activity recorded yet.
              </p>
            ) : (
              <div className="space-y-0">
                {auditLogs.map((log, index) => {
                  const config = ACTION_LABELS[log.action] || {
                    label: log.action,
                    icon: "📝",
                    color: "text-[var(--color-text-muted)]",
                  };
                  return (
                    <div
                      key={log.id}
                      className="flex gap-3 pb-4 relative"
                    >
                      {/* Timeline line */}
                      {index < auditLogs.length - 1 && (
                        <div className="absolute left-[11px] top-6 bottom-0 w-px bg-[var(--color-border-subtle)]" />
                      )}
                      <span className="text-sm flex-shrink-0 mt-0.5">
                        {config.icon}
                      </span>
                      <div className="min-w-0">
                        <p
                          className={cn(
                            "text-xs font-medium",
                            config.color
                          )}
                        >
                          {config.label}
                        </p>
                        <p className="text-[10px] text-[var(--color-text-muted)] mt-0.5">
                          {log.actor_name || "System"} ·{" "}
                          {formatDateTime(log.created_at)}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Item Details */}
          <Card className="p-5">
            <h2 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider mb-3">
              Details
            </h2>
            <dl className="space-y-2.5">
              <div>
                <dt className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">
                  Assigned Reviewer
                </dt>
                <dd className="text-sm text-[var(--color-text-primary)]">
                  {item.assigned_reviewer_name || "Unassigned"}
                </dd>
              </div>
              <div>
                <dt className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">
                  Created
                </dt>
                <dd className="text-sm text-[var(--color-text-primary)]">
                  {formatDateTime(item.created_at)}
                </dd>
              </div>
              <div>
                <dt className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">
                  Last Updated
                </dt>
                <dd className="text-sm text-[var(--color-text-primary)]">
                  {formatDateTime(item.updated_at)}
                </dd>
              </div>
              <div>
                <dt className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">
                  Item ID
                </dt>
                <dd className="text-xs text-[var(--color-text-muted)] font-mono truncate">
                  {item.id}
                </dd>
              </div>
            </dl>
          </Card>
        </div>
      </div>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
