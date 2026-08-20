import {
  User,
  Site,
  Project,
  Task,
  Milestone,
  InventoryItem,
  InventoryTransaction,
  Equipment,
  AlertItem,
  Contractor,
  MaterialRequest,
  VendorQuote,
  Vendor,
  PurchaseOrder,
  Payment,
  Notification,
} from './types';

export const currentUser: User = {
  id: 'u1',
  email: 'admin@sitesync.in',
  full_name: 'Rajesh Sharma',
  role: 'admin',
  is_active: true,
};

export const users: User[] = [
  currentUser,
  {
    id: 'u2',
    email: 'pm@sitesync.in',
    full_name: 'Ananya Verma',
    role: 'pm',
    is_active: true,
  },
  {
    id: 'u3',
    email: 'contractor@sitesync.in',
    full_name: 'Vikram Singh',
    role: 'contractor',
    is_active: true,
  },
  {
    id: 'u4',
    email: 'finance@sitesync.in',
    full_name: 'Priya Patel',
    role: 'finance',
    is_active: true,
  },
];

export const notifications: Notification[] = [
  {
    id: 'n1',
    title: 'Low Stock Alert',
    message: 'Cement inventory on Metro Heights is below threshold (45 bags remaining).',
    is_read: false,
    created_at: '2026-08-19T10:30:00Z',
  },
  {
    id: 'n2',
    title: 'Material Request Approved',
    message: 'PO #PO-8820 for Steel Rebars approved by Finance.',
    is_read: false,
    created_at: '2026-08-19T14:15:00Z',
  },
  {
    id: 'n3',
    title: 'Milestone Completed',
    message: 'Foundation pouring completed for Grand Commercial Complex.',
    is_read: true,
    created_at: '2026-08-18T17:00:00Z',
  },
];

export const sites: Site[] = [
  {
    id: 'site-1',
    name: 'Metro Heights Tower',
    location: 'Bandra Kurla Complex, Mumbai',
    location_text: 'Bandra Kurla Complex, Mumbai',
    latitude: 19.0657,
    longitude: 72.8687,
    status: 'active',
    created_at: '2026-01-15T00:00:00Z',
  },
  {
    id: 'site-2',
    name: 'Grand Commercial Plaza',
    location: 'Cyber City, Gurugram',
    location_text: 'Cyber City, Gurugram',
    latitude: 28.495,
    longitude: 77.0895,
    status: 'active',
    created_at: '2026-02-10T00:00:00Z',
  },
  {
    id: 'site-3',
    name: 'Greenfield Residential Park',
    location: 'Whitefield, Bengaluru',
    location_text: 'Whitefield, Bengaluru',
    latitude: 12.9698,
    longitude: 77.75,
    status: 'active',
    created_at: '2026-03-01T00:00:00Z',
  },
];

export const projects: Project[] = [
  {
    id: 'proj-1',
    site_id: 'site-1',
    name: 'Tower A Substructure & Podium',
    status: 'in_progress',
    budget: 85000000,
    budget_total: 85000000,
    progress_percent: 65,
    start_date: '2026-02-01',
    end_date: '2026-11-30',
  },
  {
    id: 'proj-2',
    site_id: 'site-1',
    name: 'HVAC & MEP Systems',
    status: 'in_progress',
    budget: 32000000,
    budget_total: 32000000,
    progress_percent: 40,
    start_date: '2026-04-15',
    end_date: '2026-12-15',
  },
  {
    id: 'proj-3',
    site_id: 'site-2',
    name: 'Retail Block Framing',
    status: 'in_progress',
    budget: 64000000,
    budget_total: 64000000,
    progress_percent: 50,
    start_date: '2026-03-01',
    end_date: '2026-10-31',
  },
];

export const tasks: Task[] = [
  {
    id: 'task-1',
    project_id: 'proj-1',
    title: 'Excavation & Shoring Work',
    name: 'Excavation & Shoring Work',
    description: 'Deep excavation for basement B1 and B2',
    status: 'completed',
    start_date: '2026-02-01',
    end_date: '2026-03-15',
    due_date: '2026-03-15',
  },
  {
    id: 'task-2',
    project_id: 'proj-1',
    title: 'Raft Foundation Rebar Tying',
    name: 'Raft Foundation Rebar Tying',
    description: 'Rebar placement for main raft slab',
    status: 'completed',
    start_date: '2026-03-16',
    end_date: '2026-05-10',
    due_date: '2026-05-10',
    depends_on_task_id: 'task-1',
  },
  {
    id: 'task-3',
    project_id: 'proj-1',
    title: 'Concrete Pouring B2 Basement',
    name: 'Concrete Pouring B2 Basement',
    description: 'M35 Grade concrete pour',
    status: 'in_progress',
    start_date: '2026-05-11',
    end_date: '2026-08-25',
    due_date: '2026-08-25',
    depends_on_task_id: 'task-2',
  },
];

export const milestones: Milestone[] = [
  {
    id: 'ms-1',
    project_id: 'proj-1',
    title: 'Basement Structure Completion',
    name: 'Basement Structure Completion',
    due_date: '2026-09-15',
    status: 'in_progress',
  },
  {
    id: 'ms-2',
    project_id: 'proj-1',
    title: 'Podium Level Slab Pour',
    name: 'Podium Level Slab Pour',
    due_date: '2026-11-15',
    status: 'pending',
  },
  {
    id: 'ms-3',
    project_id: 'proj-3',
    title: 'Superstructure Framing Handover',
    name: 'Superstructure Framing Handover',
    due_date: '2026-10-15',
    status: 'in_progress',
  },
];

export const inventory: InventoryItem[] = [
  {
    id: 'inv-1',
    site_id: 'site-1',
    material_name: 'PPC Cement (50kg bags)',
    quantity: 45,
    current_stock: 45,
    unit: 'bags',
    min_stock: 100,
    reorder_level: 100,
    unit_price: 370,
    consumption_rate_per_day: 15,
    updated_at: '2026-08-19T10:00:00Z',
  },
  {
    id: 'inv-2',
    site_id: 'site-1',
    material_name: 'Fe550 TMT Steel Rebars (16mm)',
    quantity: 18.5,
    current_stock: 18.5,
    unit: 'tons',
    min_stock: 5,
    reorder_level: 5,
    unit_price: 62000,
    consumption_rate_per_day: 1.2,
    updated_at: '2026-08-18T14:30:00Z',
  },
  {
    id: 'inv-3',
    site_id: 'site-2',
    material_name: 'Fly Ash Red Bricks',
    quantity: 12000,
    current_stock: 12000,
    unit: 'pcs',
    min_stock: 3000,
    reorder_level: 3000,
    unit_price: 9,
    consumption_rate_per_day: 500,
    updated_at: '2026-08-17T11:00:00Z',
  },
];

export const inventoryTransactions: InventoryTransaction[] = [
  {
    id: 'tx-1',
    item_id: 'inv-1',
    inventory_id: 'inv-1',
    type: 'out',
    quantity: 50,
    created_at: '2026-08-18T09:00:00Z',
    note: 'Used for B2 floor slab pour',
    performed_by_name: 'Vikram Singh',
  },
  {
    id: 'tx-2',
    item_id: 'inv-2',
    inventory_id: 'inv-2',
    type: 'in',
    quantity: 10,
    created_at: '2026-08-17T14:30:00Z',
    note: 'Received shipment PO-8820',
    performed_by_name: 'Vikram Singh',
  },
];

export const equipment: Equipment[] = [
  {
    id: 'eq-1',
    site_id: 'site-1',
    name: 'CAT 320 Hydraulic Excavator',
    type: 'Excavator',
    hours_used: 420,
    status: 'Operational',
  },
  {
    id: 'eq-2',
    site_id: 'site-1',
    name: 'Potain Tower Crane (50m Reach)',
    type: 'Crane',
    hours_used: 850,
    status: 'Operational',
  },
];

export const alerts: AlertItem[] = [
  {
    id: 'alt-1',
    site_id: 'site-1',
    site_name: 'Metro Heights Tower',
    title: 'Low Cement Supply Risk',
    description: 'Stock is below 50 bags. Reorder required immediately.',
    severity: 'high',
    type: 'Inventory',
    message: 'Stock is below 50 bags. Reorder required immediately.',
    status: 'open',
    created_at: '2026-08-19T08:00:00Z',
  },
  {
    id: 'alt-2',
    site_id: 'site-2',
    site_name: 'Grand Commercial Plaza',
    title: 'Heavy Rain Advisory',
    description: 'Monsoon weather alert issued for region. Secure open excavation.',
    severity: 'medium',
    type: 'Weather',
    message: 'Monsoon weather alert issued for region. Secure open excavation.',
    status: 'open',
    created_at: '2026-08-20T06:30:00Z',
  },
];

export const contractors: Contractor[] = [
  {
    id: 'c-1',
    site_id: 'site-1',
    name: 'Apex Concrete Solutions Ltd.',
    trade: 'RCC Civil Structure',
    specialty: 'RCC Civil Structure',
    phone: '+91 98111 22334',
  },
  {
    id: 'c-2',
    site_id: 'site-2',
    name: 'ElectroTech Infra Services',
    trade: 'Electrical & MEP',
    specialty: 'Electrical & MEP',
    phone: '+91 98222 33445',
  },
];

export const materialRequests: MaterialRequest[] = [
  {
    id: 'mr-101',
    site_id: 'site-1',
    site_name: 'Metro Heights Tower',
    requester_name: 'Vikram Singh',
    requested_by_name: 'Vikram Singh',
    pm_reviewed_by_name: 'Ananya Verma',
    finance_reviewed_by_name: 'Priya Patel',
    material_name: 'PPC Cement (50kg bags)',
    quantity: 500,
    unit: 'bags',
    pm_status: 'approved',
    finance_status: 'approved',
    created_at: '2026-08-16T10:00:00Z',
  },
  {
    id: 'mr-102',
    site_id: 'site-2',
    site_name: 'Grand Commercial Plaza',
    requester_name: 'Suresh Kumar',
    requested_by_name: 'Suresh Kumar',
    pm_reviewed_by_name: 'Ananya Verma',
    material_name: 'M-Sand Fine Aggregate',
    quantity: 40,
    unit: 'tons',
    pm_status: 'approved',
    finance_status: 'pending',
    created_at: '2026-08-18T11:30:00Z',
  },
];

export const vendors: Vendor[] = [
  {
    id: 'v-1',
    name: 'UltraTech Cement Distributors',
    category: 'Cement & Concrete',
    contact: '+91 98200 11223',
    contact_phone: '+91 98200 11223',
    contact_email: 'sales@ultratechdist.in',
  },
  {
    id: 'v-2',
    name: 'Tata Steel Buildmate',
    category: 'Steel & Metals',
    contact: '+91 98765 43210',
    contact_phone: '+91 98765 43210',
    contact_email: 'orders@tatabuildmate.com',
  },
];

export const vendorQuotes: VendorQuote[] = [
  {
    id: 'vq-1',
    request_id: 'mr-101',
    material_request_id: 'mr-101',
    vendor_id: 'v-1',
    vendor_name: 'UltraTech Cement Distributors',
    unit_price: 370,
    total_price: 185000,
    delivery_days: 2,
    amount: 185000,
    is_selected: true,
  },
  {
    id: 'vq-2',
    request_id: 'mr-101',
    material_request_id: 'mr-101',
    vendor_id: 'v-2',
    vendor_name: 'Ambuja Cements Direct',
    unit_price: 384,
    total_price: 192000,
    delivery_days: 3,
    amount: 192000,
    is_selected: false,
  },
];

export const purchaseOrders: PurchaseOrder[] = [
  {
    id: 'PO-8820',
    request_id: 'mr-101',
    material_request_id: 'mr-101',
    vendor_quote_id: 'vq-1',
    vendor_name: 'UltraTech Cement Distributors',
    material_name: 'PPC Cement (50kg bags)',
    approved_by_name: 'Priya Patel',
    delivered_at: '2026-08-18T14:30:00Z',
    total_amount: 185000,
    amount: 185000,
    status: 'approved',
    created_at: '2026-08-17T15:00:00Z',
  },
];

export const payments: Payment[] = [
  {
    id: 'pay-1',
    po_id: 'PO-8820',
    purchase_order_id: 'PO-8820',
    po_vendor_name: 'UltraTech Cement Distributors',
    released_by_name: 'Priya Patel',
    released_at: '2026-08-19T11:00:00Z',
    created_at: '2026-08-18T10:00:00Z',
    amount: 185000,
    status: 'scheduled',
    date: '2026-08-28',
  },
];

export function getTasksByProject(projectId: string): Task[] {
  return tasks.filter((t) => t.project_id === projectId);
}

export function getMilestonesByProject(projectId: string): Milestone[] {
  return milestones.filter((m) => m.project_id === projectId);
}

export function getQuotesForRequest(requestId: string): VendorQuote[] {
  return vendorQuotes.filter((q) => q.request_id === requestId || q.material_request_id === requestId);
}

export function getBudgetVsActual(siteId: string) {
  const siteProjects = projects.filter((p) => p.site_id === siteId);
  const totalBudget = siteProjects.reduce((sum, p) => sum + (p.budget || p.budget_total || 0), 0);
  const totalActual = totalBudget * 0.62;
  return { totalBudget, totalActual, budget: totalBudget, spent: totalActual };
}
