/* ===== API Client ===== */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = "An error occurred";
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // ignore parse errors
    }

    if (response.status === 401) {
      // Clear token and redirect to login
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
      }
    }

    throw new ApiError(message, response.status);
  }

  return response.json();
}

/* ===== Auth API ===== */

export const authApi = {
  login: (email: string, password: string) =>
    request<import("@/types").LoginResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<import("@/types").User>("/api/v1/auth/me"),
};

/* ===== Work Items API ===== */

export const workItemsApi = {
  list: (params?: { status?: string; page?: number; page_size?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.page_size) searchParams.set("page_size", String(params.page_size));
    const query = searchParams.toString();
    return request<import("@/types").WorkItemListResponse>(
      `/api/v1/work-items${query ? `?${query}` : ""}`
    );
  },

  get: (id: string) =>
    request<import("@/types").WorkItem>(`/api/v1/work-items/${id}`),

  update: (id: string, editedOutput: string) =>
    request<import("@/types").WorkItem>(`/api/v1/work-items/${id}`, {
      method: "PUT",
      body: JSON.stringify({ edited_output: editedOutput }),
    }),

  approve: (id: string, note?: string, editedOutput?: string) =>
    request<import("@/types").WorkItem>(`/api/v1/work-items/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ note, edited_output: editedOutput }),
    }),

  reject: (id: string, note?: string) =>
    request<import("@/types").WorkItem>(`/api/v1/work-items/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ note }),
    }),

  regenerate: (id: string) =>
    request<import("@/types").WorkItem>(`/api/v1/work-items/${id}/regenerate`, {
      method: "POST",
    }),

  retry: (id: string) =>
    request<import("@/types").WorkItem>(`/api/v1/work-items/${id}/retry`, {
      method: "POST",
    }),

  // SSE connection for real-time status updates
  subscribeToEvents: (id: string, onEvent: (data: { status?: string; done?: boolean }) => void) => {
    const token = getToken();
    const eventSource = new EventSource(
      `${API_BASE_URL}/api/v1/work-items/${id}/events`,
      // Note: EventSource doesn't support custom headers natively.
      // We'll use polling as fallback if SSE auth is needed.
    );

    // Since EventSource doesn't support auth headers, we'll use polling instead
    let active = true;
    const poll = async () => {
      while (active) {
        try {
          const item = await workItemsApi.get(id);
          onEvent({ status: item.status });
          if (["sent", "failed", "rejected"].includes(item.status)) {
            active = false;
            break;
          }
        } catch {
          // ignore errors during polling
        }
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
    };
    poll();

    return () => {
      active = false;
    };
  },
};

/* ===== Audit Logs API ===== */

export const auditApi = {
  list: (params?: { page?: number; page_size?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.page_size) searchParams.set("page_size", String(params.page_size));
    const query = searchParams.toString();
    return request<import("@/types").AuditLogListResponse>(
      `/api/v1/audit-logs${query ? `?${query}` : ""}`
    );
  },

  byWorkItem: (workItemId: string) =>
    request<import("@/types").AuditLog[]>(
      `/api/v1/audit-logs/work-item/${workItemId}`
    ),
};

/* ===== Admin API ===== */

export const adminApi = {
  dashboard: () =>
    request<import("@/types").DashboardStats>("/api/v1/admin/dashboard"),

  users: () => request<import("@/types").User[]>("/api/v1/admin/users"),
};

export { ApiError };
