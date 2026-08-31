import React from 'react';
import { LayoutDashboard, Building2, Package, Wrench, ShoppingCart, Activity } from 'lucide-react';
import { ViewTab } from '../types';

interface BottomNavProps {
  currentTab: ViewTab;
  onTabChange: (tab: ViewTab) => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({ currentTab, onTabChange }) => {
  const tabs = [
    { id: 'dashboard' as ViewTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'sites' as ViewTab, label: 'Sites', icon: Building2 },
    { id: 'inventory' as ViewTab, label: 'Stock', icon: Package },
    { id: 'equipment' as ViewTab, label: 'Equipment', icon: Wrench },
    { id: 'procurement' as ViewTab, label: 'Orders', icon: ShoppingCart },
    { id: 'ai' as ViewTab, label: 'AI Agent', icon: Activity, highlight: true }
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 border-t-2 border-border bg-card pb-[env(safe-area-inset-bottom)] shadow-brutal-xl">
      <div className="mx-auto flex max-w-md items-center justify-around px-2 py-2 sm:max-w-lg">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = currentTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`active-tap relative flex flex-col items-center justify-center rounded-sm border-2 px-3 py-1.5 transition-all duration-150 ${
                isActive
                  ? 'border-border bg-primary text-primary-foreground shadow-brutal-sm font-extrabold'
                  : 'border-transparent text-foreground hover:border-border hover:bg-secondary'
              }`}
            >
              <div className="relative">
                <Icon className={`h-4 w-4 ${isActive ? 'scale-110' : ''}`} />
                {tab.highlight && !isActive && (
                  <span className="absolute -top-1 -right-1 flex h-2 w-2 rounded-full bg-primary animate-ping" />
                )}
              </div>

              <span className="mt-1 text-[10px] tracking-tight font-bold">
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
