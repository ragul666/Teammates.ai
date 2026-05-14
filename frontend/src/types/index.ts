/* ===== TypeScript Types ===== */

export interface User {
  id: string;
  name: string;
  email: string;
  role: "admin" | "reviewer";
  organization_id: string;
  organization_name: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type WorkItemStatus =
  | "pending_review"
  | "approved"
  | "rejected"
  | "regenerating"
  | "processing"
  | "sent"
  | "failed";

export interface WorkItem {
  id: string;
  organization_id: string;
  assigned_reviewer_id: string | null;
  assigned_reviewer_name: string | null;
  lead_name: string;
  company_name: string;
  lead_context: string;
  original_input: string;
  ai_output: string;
  edited_output: string | null;
  status: WorkItemStatus;
  reviewer_note: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkItemListResponse {
  items: WorkItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardStats {
  total_items: number;
  pending_review: number;
  approved: number;
  rejected: number;
  processing: number;
  sent: number;
  failed: number;
}

export type AuditAction =
  | "item_created"
  | "ai_draft_generated"
  | "draft_regenerated"
  | "draft_edited"
  | "item_approved"
  | "item_rejected"
  | "job_started"
  | "job_completed"
  | "job_failed"
  | "user_login";

export interface AuditLog {
  id: string;
  organization_id: string;
  work_item_id: string | null;
  actor_user_id: string | null;
  actor_name: string | null;
  action: AuditAction;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLog[];
  total: number;
  page: number;
  page_size: number;
}
