const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// ─── Token helpers ───────────────────────────────

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
  // Also set as cookie for middleware
  document.cookie = `access_token=${access}; path=/; max-age=${7 * 86400}`;
}

export function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  document.cookie = 'access_token=; path=/; max-age=0';
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

// ─── Core fetch wrapper ──────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  withAuth = true,
): Promise<T> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (withAuth) {
    const token = getToken();
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearTokens();
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail || err.message || JSON.stringify(err);
    } catch {}
    throw new Error(detail);
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

// ─── Auth ────────────────────────────────────────

export async function login(username: string, password: string) {
  const data = await apiFetch<{ access: string; refresh: string }>(
    '/login/',
    { method: 'POST', body: JSON.stringify({ username, password }) },
    false,
  );
  setTokens(data.access, data.refresh);
  return data;
}

export async function signup(username: string, email: string, password: string) {
  return apiFetch('/signup/', {
    method: 'POST',
    body: JSON.stringify({ username, email, password }),
  }, false);
}

export async function logout() {
  clearTokens();
  window.location.href = '/login';
}

// ─── User / Company ──────────────────────────────

export const getMe = () => apiFetch<{ id: number; username: string; email: string }>('/me/');
export const getMyCompany = () => apiFetch<{ id: number; name: string; logo?: string }>('/my-company/');
export const updateMyCompany = (data: Partial<{ name: string; agni_api_key: string; is_active: boolean }>) =>
  apiFetch('/my-company/', { method: 'PATCH', body: JSON.stringify(data) });
export const createCompany = (data: { name: string; agni_api_key: string }) =>
  apiFetch('/companies/create/', { method: 'POST', body: JSON.stringify(data) });

// ── RBAC ───────────────────────────────────────────────────────────────
export const getRBACScan = () =>
  apiFetch<{
    company: { id: number; name: string };
    viewer: { id: number; username: string; is_admin: boolean; membership_id: number };
    roles: any[];
    members: any[];
  }>('/rbac/scan/');

export const listPermissions = () => apiFetch<any[]>('/permissions/');
export const createRole = (data: { name: string; is_default?: boolean; permission_ids?: number[] }) =>
  apiFetch('/roles/', { method: 'POST', body: JSON.stringify(data) });
export const updateRole = (roleId: number, data: { name: string; is_default?: boolean; permission_ids?: number[] }) =>
  apiFetch(`/roles/${roleId}/`, { method: 'PATCH', body: JSON.stringify(data) });

export const listInvitations = () => apiFetch<any[]>('/invitations/');
export const createInvitation = (data: { email: string; role_id?: number | null }) =>
  apiFetch('/invitations/', { method: 'POST', body: JSON.stringify(data) });
export const acceptInvitation = (token: string) =>
  apiFetch('/invitations/accept/', { method: 'POST', body: JSON.stringify({ token }) });

export const listJoinRequests = () => apiFetch<any[]>('/join-requests/list/');
export const approveJoinRequest = (id: number, roleId?: number | null) =>
  apiFetch(`/join-requests/${id}/approve/`, { method: 'POST', body: JSON.stringify({ role_id: roleId ?? null }) });
export const rejectJoinRequest = (id: number) =>
  apiFetch(`/join-requests/${id}/reject/`, { method: 'POST' });

// ─── Projects ────────────────────────────────────

export const getProjects = () => apiFetch<{ id: number; name: string; external_pipeline_id: string }[]>('/projects/');
export const createProject = (data: { name: string; external_pipeline_id?: string }) =>
  apiFetch('/projects/', { method: 'POST', body: JSON.stringify(data) });

// ─── Members / Roles ─────────────────────────────

export const getMembers = () => apiFetch<any[]>('/company-members/');
export const createMember = (data: any) =>
  apiFetch('/company-members/create/', { method: 'POST', body: JSON.stringify(data) });
export const getRoles = () => apiFetch<{ id: number; name: string; is_default: boolean }[]>('/roles/');
export const assignProjects = (memberId: number, projectIds: number[]) =>
  apiFetch(`/company-members/${memberId}/assign-projects/`, {
    method: 'POST',
    body: JSON.stringify({ project_ids: projectIds }),
  });

// ─── Leads ───────────────────────────────────────

export const getLeads = (params: Record<string, string> = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch<any[]>(`/leads/${qs ? `?${qs}` : ''}`);
};

// ─── Analytics ───────────────────────────────────

export const getKPIs = (days = 30, projectId?: string) => {
  const qs = new URLSearchParams({ days: String(days), ...(projectId ? { project: projectId } : {}) }).toString();
  return apiFetch<{ kpis: any[]; total: number; period_days: number }>(`/analytics/kpis/?${qs}`);
};

export const getSources = (days = 30, projectId?: string) => {
  const qs = new URLSearchParams({ days: String(days), ...(projectId ? { project: projectId } : {}) }).toString();
  return apiFetch<{ sources: any[] }>(`/analytics/sources/?${qs}`);
};

export const getAgents = (days = 30, projectId?: string) => {
  const qs = new URLSearchParams({ days: String(days), ...(projectId ? { project: projectId } : {}) }).toString();
  return apiFetch<{ agents: any[]; statuses: string[] }>(`/analytics/agents/?${qs}`);
};

export const getPipeline = (projectId?: string) => {
  const qs = projectId ? `?project=${projectId}` : '';
  return apiFetch<{ stages: any[] }>(`/analytics/pipeline/${qs}`);
};

export const getSourceWise = (days = 30, projectId?: string) => {
  const qs = new URLSearchParams({ days: String(days), ...(projectId ? { project: projectId } : {}) }).toString();
  return apiFetch<{ rows: any[]; statuses: string[]; total: number }>(`/analytics/source-wise/?${qs}`);
};

// ─── GHL Integration ─────────────────────────────

export const getGHLStatus = () => apiFetch<any>('/integrations/ghl/');
export const connectGHL = (data: { api_key?: string; access_token?: string; location_id: string }) =>
  apiFetch('/integrations/ghl/', { method: 'POST', body: JSON.stringify(data) });
export const registerGHLWebhook = (webhookBaseUrl: string) =>
  apiFetch('/integrations/ghl/webhook/register/', {
    method: 'POST',
    body: JSON.stringify({ webhook_base_url: webhookBaseUrl }),
  });

// ─── Sync ────────────────────────────────────────

export const triggerAutoSync = () => apiFetch<any>('/sync/auto/', { method: 'POST' });
export const triggerManualSync = (dateFrom: string, dateTo: string) =>
  apiFetch<any>('/sync/manual/', {
    method: 'POST',
    body: JSON.stringify({ date_from: dateFrom, date_to: dateTo }),
  });
export const getSyncLogs = () => apiFetch<any[]>('/sync/logs/');
