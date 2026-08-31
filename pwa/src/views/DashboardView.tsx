import React from 'react';
import { 
  Building2, Package, Wrench, ShoppingCart, Activity, QrCode, PlusCircle, 
  TrendingUp, AlertTriangle, ArrowUpRight, ShieldCheck, Zap, HardHat
} from 'lucide-react';
import { Site, InventoryItem, Equipment, PurchaseOrder, ViewTab } from '../types';

interface DashboardViewProps {
  sites: Site[];
  inventory: InventoryItem[];
  equipment: Equipment[];
  orders: PurchaseOrder[];
  onNavigate: (tab: ViewTab) => void;
  onOpenAction: (action: 'scan' | 'new_stock' | 'new_po') => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  sites,
  inventory,
  equipment,
  orders,
  onNavigate,
  onOpenAction
}) => {
  const lowStockCount = inventory.filter(i => i.status !== 'in_stock').length;
  const maintenanceEqCount = equipment.filter(e => e.status === 'maintenance').length;
  const pendingOrdersCount = orders.filter(o => o.status === 'pending_approval' || o.status === 'in_transit').length;
  
  const totalBudget = sites.reduce((sum, s) => sum + s.budget, 0);
  const totalSpent = sites.reduce((sum, s) => sum + s.spent, 0);
  const budgetUtilization = Math.round((totalSpent / (totalBudget || 1)) * 100);

  return (
    <div className="space-y-5 pb-24 lg:pl-64">
      
      {/* Quick Action FAB Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
        <button
          onClick={() => onOpenAction('scan')}
          className="active-tap brutal-btn brutal-btn-hover flex shrink-0 items-center gap-2 bg-primary text-primary-foreground px-4 py-2.5 text-xs font-extrabold"
        >
          <QrCode className="h-4 w-4" />
          <span>Scan Stock QR</span>
        </button>

        <button
          onClick={() => onOpenAction('new_stock')}
          className="active-tap brutal-btn brutal-btn-hover flex shrink-0 items-center gap-2 bg-card text-foreground px-4 py-2.5 text-xs font-bold"
        >
          <PlusCircle className="h-4 w-4 text-primary" />
          <span>Add Material</span>
        </button>

        <button
          onClick={() => onOpenAction('new_po')}
          className="active-tap brutal-btn brutal-btn-hover flex shrink-0 items-center gap-2 bg-card text-foreground px-4 py-2.5 text-xs font-bold"
        >
          <ShoppingCart className="h-4 w-4 text-primary" />
          <span>New PO Requisition</span>
        </button>

        <button
          onClick={() => onNavigate('ai')}
          className="active-tap brutal-btn brutal-btn-hover flex shrink-0 items-center gap-2 bg-secondary text-secondary-foreground px-4 py-2.5 text-xs font-bold"
        >
          <Activity className="h-4 w-4" />
          <span>Live AI Telemetry</span>
        </button>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-4">
        
        {/* Sites KPI */}
        <div 
          onClick={() => onNavigate('sites')}
          className="brutal-card cursor-pointer p-4 rounded-sm hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all"
        >
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Active Sites</span>
            <div className="flex h-8 w-8 items-center justify-center border-2 border-border bg-secondary text-foreground font-bold">
              <Building2 className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-foreground">{sites.length}</div>
          <div className="mt-1 flex items-center gap-1 text-[11px] text-primary font-bold">
            <TrendingUp className="h-3 w-3" /> All on schedule
          </div>
        </div>

        {/* Inventory KPI */}
        <div 
          onClick={() => onNavigate('inventory')}
          className="brutal-card cursor-pointer p-4 rounded-sm hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all"
        >
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Low Stock Items</span>
            <div className="flex h-8 w-8 items-center justify-center border-2 border-border bg-primary text-primary-foreground font-bold">
              <Package className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-foreground">{lowStockCount}</div>
          <div className="mt-1 flex items-center gap-1 text-[11px] text-primary font-bold">
            <AlertTriangle className="h-3 w-3" /> Needs reorder
          </div>
        </div>

        {/* Equipment KPI */}
        <div 
          onClick={() => onNavigate('equipment')}
          className="brutal-card cursor-pointer p-4 rounded-sm hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all"
        >
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Maintenance</span>
            <div className="flex h-8 w-8 items-center justify-center border-2 border-border bg-secondary text-foreground font-bold">
              <Wrench className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-foreground">{maintenanceEqCount}</div>
          <div className="mt-1 text-[11px] text-muted-foreground font-bold">
            {equipment.length - maintenanceEqCount} Active Fleet
          </div>
        </div>

        {/* Orders KPI */}
        <div 
          onClick={() => onNavigate('procurement')}
          className="brutal-card cursor-pointer p-4 rounded-sm hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all"
        >
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Pending POs</span>
            <div className="flex h-8 w-8 items-center justify-center border-2 border-border bg-card text-foreground font-bold">
              <ShoppingCart className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-foreground">{pendingOrdersCount}</div>
          <div className="mt-1 text-[11px] text-primary font-bold">
            ₹{(orders.reduce((sum, o) => sum + o.totalAmount, 0) / 100000).toFixed(1)}L Total Value
          </div>
        </div>

      </div>

      {/* Financial Burn Section */}
      <div className="brutal-card p-5 rounded-sm">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-display text-lg font-extrabold text-foreground">Financial Resource Allocation</h3>
            <p className="text-xs text-muted-foreground font-medium">Multi-site budget vs actual expenditure</p>
          </div>
          <div className="text-right">
            <div className="text-sm font-extrabold text-primary">₹{(totalSpent / 100000).toFixed(1)}L / ₹{(totalBudget / 100000).toFixed(1)}L</div>
            <div className="text-[10px] font-mono text-muted-foreground">{budgetUtilization}% Utilized</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="h-4 w-full brutal-border bg-secondary overflow-hidden p-0.5">
          <div 
            className="h-full bg-primary transition-all duration-1000"
            style={{ width: `${budgetUtilization}%` }}
          />
        </div>

        <div className="mt-4 grid grid-cols-3 gap-3 text-center text-xs">
          <div className="brutal-border bg-card p-2">
            <span className="text-muted-foreground block text-[10px] font-bold uppercase">Workers On Site</span>
            <span className="font-extrabold text-foreground">577 Active</span>
          </div>
          <div className="brutal-border bg-card p-2">
            <span className="text-muted-foreground block text-[10px] font-bold uppercase">Heavy Machinery</span>
            <span className="font-extrabold text-foreground">37 Vehicles</span>
          </div>
          <div className="brutal-border bg-card p-2">
            <span className="text-muted-foreground block text-[10px] font-bold uppercase">Safety Compliance</span>
            <span className="font-extrabold text-primary flex items-center justify-center gap-1">
              <ShieldCheck className="h-3.5 w-3.5" /> 100% Passed
            </span>
          </div>
        </div>
      </div>

      {/* Active Construction Sites */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-display text-lg font-extrabold text-foreground flex items-center gap-2">
            <Building2 className="h-5 w-5 text-primary" /> Active Sites
          </h3>
          <button 
            onClick={() => onNavigate('sites')}
            className="text-xs text-primary hover:underline flex items-center gap-0.5 font-bold"
          >
            View All Sites →
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {sites.slice(0, 2).map((site) => (
            <div key={site.id} className="brutal-card p-4 rounded-sm space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <span className="brutal-badge rounded bg-secondary px-2 py-0.5 text-[10px] text-secondary-foreground font-mono mb-1 inline-block">
                    {site.code}
                  </span>
                  <h4 className="text-base font-extrabold text-foreground">{site.name}</h4>
                  <p className="text-xs text-muted-foreground mt-0.5 font-medium">📍 {site.location}</p>
                </div>
                <span className="brutal-badge rounded bg-primary text-primary-foreground px-2.5 py-1 text-[10px] font-bold">
                  {site.progress}% Complete
                </span>
              </div>

              <div className="flex items-center justify-between text-xs text-foreground font-bold border-t-2 border-border pt-3">
                <span>Manager: <span className="text-primary">{site.manager}</span></span>
                <span>Equipment: <span className="text-primary">{site.activeEquipment} Units</span></span>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
