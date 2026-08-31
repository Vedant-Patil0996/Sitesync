export interface Site {
  id: string;
  name: string;
  code: string;
  location: string;
  status: 'active' | 'planning' | 'completed' | 'delayed';
  progress: number;
  budget: number;
  spent: number;
  activeEquipment: number;
  workersOnSite: number;
  alertsCount: number;
  manager: string;
  updatedAt: string;
}

export interface InventoryItem {
  id: string;
  siteId: string;
  name: string;
  sku: string;
  category: 'Cement & Concrete' | 'Steel & Metals' | 'Aggregates' | 'Electrical' | 'Plumbing' | 'Safety';
  quantity: number;
  unit: string;
  minThreshold: number;
  unitCost: number;
  lastUpdated: string;
  status: 'in_stock' | 'low_stock' | 'out_of_stock';
}

export interface Equipment {
  id: string;
  siteId: string;
  siteName: string;
  name: string;
  type: string;
  serialNo: string;
  status: 'operational' | 'in_use' | 'maintenance' | 'idle';
  operator?: string;
  fuelLevelPercent: number;
  hoursUsed: number;
  nextServiceDate: string;
}

export interface PurchaseOrder {
  id: string;
  poNumber: string;
  siteName: string;
  vendorName: string;
  totalAmount: number;
  status: 'draft' | 'pending_approval' | 'approved' | 'in_transit' | 'delivered' | 'rejected';
  createdAt: string;
  itemsCount: number;
  urgent: boolean;
}

export interface AlertNotification {
  id: string;
  title: string;
  message: string;
  type: 'critical' | 'warning' | 'info' | 'success';
  timestamp: string;
  read: boolean;
  siteName?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent' | 'system';
  content: string;
  timestamp: string;
  agentNode?: string;
  toolDetails?: {
    toolName: string;
    outputSummary: string;
  };
}

export type ViewTab = 'dashboard' | 'sites' | 'inventory' | 'equipment' | 'procurement' | 'ai';
