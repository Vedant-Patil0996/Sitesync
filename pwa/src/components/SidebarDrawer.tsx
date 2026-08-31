import React from 'react';
import { 
  LayoutDashboard, Building2, FolderKanban, Package, Wrench, 
  ShoppingCart, Wallet, AlertTriangle, Users, FileText, HardHat, X, Phone, Activity, Bot 
} from 'lucide-react';
import { ViewTab } from '../types';

interface SidebarDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  currentTab: ViewTab;
  onTabChange: (tab: ViewTab) => void;
}

export const SidebarDrawer: React.FC<SidebarDrawerProps> = ({
  isOpen,
  onClose,
  currentTab,
  onTabChange
}) => {
  const navItems = [
    { id: 'dashboard' as ViewTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'sites' as ViewTab, label: 'Sites', icon: Building2 },
    { id: 'inventory' as ViewTab, label: 'Inventory', icon: Package },
    { id: 'equipment' as ViewTab, label: 'Equipment', icon: Wrench },
    { id: 'procurement' as ViewTab, label: 'Material Requests', icon: ShoppingCart },
    { id: 'ai' as ViewTab, label: 'Live AI Activity', icon: Activity, highlight: true }
  ];

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Drawer Sidebar */}
      <aside
        className={`fixed left-0 top-0 z-50 h-full w-64 border-r-2 border-border bg-card transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex h-16 items-center justify-between border-b-2 border-border px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center border-2 border-border bg-primary text-primary-foreground shadow-brutal-sm">
              <HardHat className="h-5 w-5" />
            </div>
            <span className="font-display text-xl font-extrabold tracking-tight text-foreground">SiteSync</span>
          </div>
          <button onClick={onClose} className="lg:hidden brutal-btn p-1 bg-card">
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex flex-col gap-1.5 p-3 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 4rem)' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => {
                  onTabChange(item.id);
                  onClose();
                }}
                className={`flex items-center gap-3 rounded-sm border-2 px-3 py-2.5 text-sm font-bold transition-all text-left ${
                  isActive
                    ? 'border-border bg-primary text-primary-foreground shadow-brutal-sm'
                    : 'border-transparent text-foreground hover:border-border hover:bg-secondary hover:shadow-brutal-sm'
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.label}</span>
                {item.highlight && !isActive && (
                  <span className="ml-auto flex h-2 w-2 rounded-full bg-primary animate-pulse" />
                )}
              </button>
            );
          })}
        </nav>
      </aside>
    </>
  );
};
