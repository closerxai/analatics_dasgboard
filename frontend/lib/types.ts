export interface User {
  id: number;
  username: string;
  email: string;
}

export interface Company {
  id: number;
  name: string;
  logo?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: number;
  name: string;
  external_pipeline_id: string;
  created_at: string;
  updated_at: string;
}

export interface LeadSource {
  id: number;
  name: string;
}

export type LeadStatus =
  | 'uncontacted'
  | 'qualified'
  | 'disqualified'
  | 'not_responding'
  | 'call_back'
  | 'booked_site_visit'
  | 'site_visit_done'
  | 'whatsapp';

export const LEAD_STATUS_LABELS: Record<LeadStatus, string> = {
  uncontacted: 'Uncontacted (Pending Calls)',
  qualified: 'Qualified',
  disqualified: 'Disqualified',
  not_responding: 'Not Responding',
  call_back: 'Call Back',
  booked_site_visit: 'Booked Site Visit',
  site_visit_done: 'Site Visit Done',
  whatsapp: 'WhatsApp',
};

export const ALL_STATUSES = Object.keys(LEAD_STATUS_LABELS) as LeadStatus[];

export interface Lead {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  status: LeadStatus;
  status_display: string;
  source?: number;
  source_name: string;
  project?: number;
  project_name: string;
  assigned_to_name?: string;
  city?: string;
  planning_for_visit?: string;
  follow_up_date?: string;
  whatsapp_status?: string;
  remarks?: string;
  monetary_value?: string;
  ghl_opportunity_id?: string;
  ghl_pipeline_stage_name?: string;
  ghl_opportunity_status?: string;
  external_id?: string;
  created_at: string;
  updated_at: string;
}

export interface CompanyMember {
  id: number;
  username: string;
  email: string;
  role: number;
  role_name: string;
  projects: Project[];
  is_active: boolean;
  joined_at: string;
}

export interface Role {
  id: number;
  name: string;
  is_default: boolean;
}

export interface KPI {
  label: string;
  val: string | number;
  icon: string;
  delta: string;
  up: boolean;
  accent: 'primary' | 'good' | 'bad';
}

export interface SourceRow {
  source: string;
  total: number;
  by_status: Record<LeadStatus, number>;
}

export interface AgentRow {
  agent: string;
  total: number;
  by_status: Record<LeadStatus, number>;
}

export interface PipelineStage {
  stage_id: string;
  stage_name: string;
  pipeline_id: string;
  pipeline_name: string;
  position: number;
  count: number;
  project_id?: number;
  leads: Lead[];
}

export interface SyncLog {
  id: number;
  sync_type: string;
  sync_type_display: string;
  status: string;
  status_display: string;
  started_at: string;
  completed_at?: string;
  leads_synced: number;
  leads_created: number;
  leads_updated: number;
  error_message?: string;
  date_from?: string;
  date_to?: string;
  triggered_by_username?: string;
}

export interface GHLStatus {
  connected: boolean;
  location_id?: string;
  auth_type?: string;
  webhook_registered?: boolean;
}

// Source colors for the UI
export const SOURCE_COLORS: Record<string, string> = {
  'Facebook': 'oklch(62% 0.14 245)',
  'Facebook Ads': 'oklch(62% 0.14 245)',
  'Instagram': 'oklch(62% 0.16 300)',
  'Google': 'oklch(62% 0.14 195)',
  'Google Ads': 'oklch(62% 0.14 195)',
  'LinkedIn': 'oklch(74% 0.08 195)',
  'Website': 'oklch(72% 0.12 75)',
  'Property Portal': 'oklch(62% 0.14 150)',
  'Property Portals': 'oklch(62% 0.14 150)',
  'Referrals': 'oklch(62% 0.14 230)',
  'PR / Event': 'oklch(62% 0.16 25)',
  'Direct Calls': 'oklch(62% 0.16 25)',
  'YouTube': 'oklch(62% 0.16 25)',
};

export function getSourceColor(name: string): string {
  return SOURCE_COLORS[name] || 'oklch(62% 0.02 250)';
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

export function formatCurrency(value?: string | number | null): string {
  if (!value) return '—';
  const n = typeof value === 'string' ? parseFloat(value) : value;
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(1)}Cr`;
  if (n >= 100000) return `₹${(n / 100000).toFixed(0)}L`;
  return `₹${n.toLocaleString('en-IN')}`;
}
