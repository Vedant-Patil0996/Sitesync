import React from 'react';
import { HardHat, Bell, Download, Menu, Phone, Activity } from 'lucide-react';
import { ViewTab } from '../types';

interface HeaderProps {
  currentTab: ViewTab;
  unreadAlertsCount: number;
  onOpenNotifications: () => void;
  canInstallPWA: boolean;
  onInstallPWA: () => void;
  selectedSite: string;
  onSelectSite: (siteId: string) => void;
  onOpenSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  unreadAlertsCount,
  onOpenNotifications,
  canInstallPWA,
  onInstallPWA,
  selectedSite,
  onSelectSite,
  onOpenSidebar
}) => {
  const getTabTitle = (tab: ViewTab) => {
    switch (tab) {
      case 'dashboard': return 'Dashboard Overview';
      case 'sites': return 'Sites & Locations';
      case 'inventory': return 'Inventory & Stock';
      case 'equipment': return 'Equipment & Machinery';
      case 'procurement': return 'Material Requests & POs';
      case 'ai': return 'Live AI Agent Telemetry';
      default: return 'SiteSync';
    }
  };

  return (
    <header className="sticky top-0 z-30 w-full border-b-2 border-border bg-card px-4 py-3 sm:px-6">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3">
        
        {/* Brand & Mobile Hamburger Toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenSidebar}
            className="lg:hidden brutal-btn bg-card p-2 rounded-sm"
            aria-label="Toggle menu"
          >
            <Menu className="h-5 w-5 text-foreground" />
          </button>

          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center border-2 border-border bg-primary shadow-brutal-sm text-primary-foreground font-bold">
              <HardHat className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-display text-lg font-extrabold tracking-tight text-foreground">SiteSync</span>
                <span className="brutal-badge rounded bg-secondary px-1.5 py-0.2 text-[10px] text-secondary-foreground font-mono">
                  PWA
                </span>
              </div>
              <h1 className="text-xs font-bold text-muted-foreground uppercase tracking-wide hidden sm:block">
                {getTabTitle(currentTab)}
              </h1>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 sm:gap-3">
          
          {/* Site Selector */}
          <div className="hidden sm:flex items-center gap-2 brutal-border bg-card px-3 py-1.5 text-xs font-bold text-foreground">
            <select
              value={selectedSite}
              onChange={(e) => onSelectSite(e.target.value)}
              className="bg-transparent focus:outline-none cursor-pointer text-foreground"
            >
              <option value="all">All Construction Sites</option>
              <option value="site-1">Skyline Metro Tower Phase 2</option>
              <option value="site-2">Greenfield Highway Extension</option>
              <option value="site-3">Harbor Logistics Hub</option>
              <option value="site-4">TechPark Commercial Complex</option>
            </select>
          </div>

          {/* PWA Mobile Install Button */}
          {canInstallPWA && (
            <button
              onClick={onInstallPWA}
              className="active-tap brutal-btn brutal-btn-hover flex items-center gap-1.5 bg-primary text-primary-foreground px-3 py-1.5 text-xs font-extrabold"
              title="Install SiteSync App on Phone"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Install PWA</span>
            </button>
          )}

          {/* Alert Bell */}
          <button
            onClick={onOpenNotifications}
            className="active-tap relative brutal-btn bg-card p-2 text-foreground"
            aria-label="Open notifications"
          >
            <Bell className="h-4 w-4" />
            {unreadAlertsCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-extrabold text-primary-foreground border-2 border-border shadow-brutal-sm">
                {unreadAlertsCount}
              </span>
            )}
          </button>

        </div>

      </div>
    </header>
  );
};
