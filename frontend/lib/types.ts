export type Role = 'admin' | 'pm' | 'contractor' | 'finance';

export const ROLE_LABELS: Record<Role, string> = {
  admin: 'Admin',
  pm: 'Project Manager',
  contractor: 'Contractor',
  finance: 'Finance',
};

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
}

export interface ChatMessage {
  id: string;
  user_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface Site {
  id: string;
  name: string;
  location?: string;
  location_text?: string;
  latitude: number;
  longitude: number;
  status: string;
  created_at?: string;
}

export interface Project {
  id: string;
  site_id: string;
  name: string;
  status: string;
  budget: number;
  budget_total: number;
  progress_percent: number;
  start_date: string;
  end_date?: string;
}

export interface Task {
  id: string;
  project_id: string;
  title?: string;
  name?: string;
  description?: string;
  status: 'completed' | 'in_progress' | 'pending' | string;
  start_date?: string;
  end_date?: string;
  due_date?: string;
  depends_on_task_id?: string;
}

export interface Milestone {
  id: string;
  project_id: string;
  title?: string;
  name?: string;
  due_date: string;
  status: string;
}

export interface InventoryItem {
  id: string;
  site_id: string;
  material_name: string;
  quantity?: number;
  current_stock: number;
  unit: string;
  min_stock?: number;
  reorder_level: number;
  unit_price?: number;
  consumption_rate_per_day: number;
  updated_at?: string;
}

export interface InventoryTransaction {
  id: string;
  item_id?: string;
  inventory_id?: string;
  type: 'in' | 'out' | 'stock_in' | 'transfer_in' | 'stock_out' | 'transfer_out' | string;
  quantity: number;
  created_at: string;
  note?: string;
  performed_by_name?: string;
}

export interface Equipment {
  id: string;
  site_id: string;
  name: string;
  type: string;
  hours_used?: number;
  status: string;
  allocated_to_task_id?: string;
}

export interface AlertItem {
  id: string;
  site_id: string;
  site_name: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical' | string;
  type: string;
  message?: string;
  status: string;
  resolved_by_name?: string;
  created_at: string;
}

export interface Contractor {
  id: string;
  site_id: string;
  name: string;
  trade?: string;
  specialty?: string;
  phone?: string;
}

export interface MaterialRequest {
  id: string;
  site_id: string;
  site_name?: string;
  requester_name?: string;
  requested_by_name?: string;
  pm_reviewed_by_name?: string;
  finance_reviewed_by_name?: string;
  material_name: string;
  quantity: number;
  unit: string;
  pm_status: string;
  finance_status: string;
  created_at: string;
}

export interface VendorQuote {
  id: string;
  request_id?: string;
  material_request_id?: string;
  vendor_id?: string;
  vendor_name: string;
  unit_price: number;
  total_price: number;
  delivery_days: number;
  amount?: number;
  is_selected: boolean;
}

export interface Vendor {
  id: string;
  name: string;
  category?: string;
  contact?: string;
  contact_phone?: string;
  contact_email?: string;
}

export interface PurchaseOrder {
  id: string;
  request_id?: string;
  material_request_id?: string;
  vendor_quote_id?: string;
  vendor_name: string;
  total_amount: number;
  amount: number;
  material_name?: string;
  approved_by_name?: string;
  delivered_at?: string;
  status: string;
  created_at: string;
}

export interface Payment {
  id: string;
  po_id: string;
  purchase_order_id?: string;
  amount: number;
  status: 'scheduled' | 'released' | string;
  date: string;
  po_vendor_name?: string;
  released_by_name?: string;
  released_at?: string;
  created_at?: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount || 0);
}

export function formatDate(dateStr?: string): string {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export function formatDateTime(dateStr?: string): string {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
