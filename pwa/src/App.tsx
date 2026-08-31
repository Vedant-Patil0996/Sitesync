import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { SidebarDrawer } from './components/SidebarDrawer';
import { BottomNav } from './components/BottomNav';
import { PWAInstallPrompt } from './components/PWAInstallPrompt';
import { NotificationDrawer } from './components/NotificationDrawer';
import { QuickActionModal } from './components/QuickActionModal';

import { DashboardView } from './views/DashboardView';
import { SitesView } from './views/SitesView';
import { InventoryView } from './views/InventoryView';
import { EquipmentView } from './views/EquipmentView';
import { ProcurementView } from './views/ProcurementView';
import { AIChatView } from './views/AIChatView';

import { 
  Site, InventoryItem, Equipment, PurchaseOrder, AlertNotification, ViewTab 
} from './types';
import { 
  fetchSites, fetchInventory, fetchEquipment, fetchPurchaseOrders, 
  fetchAlerts, updateInventoryQuantity, updateEquipmentStatus 
} from './services/api';
import { CheckCircle2 } from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<ViewTab>('dashboard');
  const [selectedSiteId, setSelectedSiteId] = useState<string>('all');
  
  // Data States
  const [sites, setSites] = useState<Site[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);
  
  // Modal & Drawer Controls
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [quickAction, setQuickAction] = useState<'scan' | 'new_stock' | 'new_po' | null>(null);
  
  // Toast Alert State
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // PWA Install Prompt state
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);

  useEffect(() => {
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstallPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get('tab') as ViewTab;
    const actionParam = params.get('action');

    if (tabParam) setCurrentTab(tabParam);
    if (actionParam === 'scan') setQuickAction('scan');

    return () => window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
  }, []);

  const loadAllData = async () => {
    const [sData, iData, eData, pData, aData] = await Promise.all([
      fetchSites(),
      fetchInventory(),
      fetchEquipment(),
      fetchPurchaseOrders(),
      fetchAlerts()
    ]);
    setSites(sData);
    setInventory(iData);
    setEquipment(eData);
    setOrders(pData);
    setAlerts(aData);
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleTriggerPWAInstall = async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        setShowInstallPrompt(false);
        triggerToast('SiteSync PWA installed on device!');
      }
      setDeferredPrompt(null);
    } else {
      triggerToast('App is ready! On iOS Safari, tap Share -> Add to Home Screen.');
    }
  };

  const triggerToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const handleUpdateQty = (id: string, delta: number) => {
    try {
      const updated = updateInventoryQuantity(id, delta);
      setInventory(prev => prev.map(item => item.id === id ? updated : item));
      triggerToast(`Updated stock count for ${updated.name}`);
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpdateEqStatus = (id: string, status: Equipment['status']) => {
    try {
      const updated = updateEquipmentStatus(id, status);
      setEquipment(prev => prev.map(e => e.id === id ? updated : e));
      triggerToast(`Updated telematics status for ${updated.name}`);
    } catch (e) {
      console.error(e);
    }
  };

  const handleMarkAlertsRead = () => {
    setAlerts(prev => prev.map(a => ({ ...a, read: true })));
    triggerToast('All notifications marked as read.');
  };

  const unreadAlerts = alerts.filter(a => !a.read).length;

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">
      
      {/* Toast Notification Banner */}
      {toastMessage && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 rounded-sm bg-primary text-primary-foreground px-4 py-2.5 shadow-brutal text-xs font-extrabold border-2 border-border animate-in fade-in slide-in-from-top-4">
          <CheckCircle2 className="h-4 w-4" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Top Application Header */}
      <Header
        currentTab={currentTab}
        unreadAlertsCount={unreadAlerts}
        onOpenNotifications={() => setIsNotificationsOpen(true)}
        canInstallPWA={showInstallPrompt || true}
        onInstallPWA={handleTriggerPWAInstall}
        selectedSite={selectedSiteId}
        onSelectSite={setSelectedSiteId}
        onOpenSidebar={() => setIsSidebarOpen(true)}
      />

      {/* Sidebar Drawer Navigation */}
      <SidebarDrawer
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        currentTab={currentTab}
        onTabChange={(tab) => setCurrentTab(tab)}
      />

      {/* Mobile PWA Installation Prompt Banner */}
      {showInstallPrompt && (
        <div className="lg:pl-64">
          <PWAInstallPrompt
            onInstall={handleTriggerPWAInstall}
            onDismiss={() => setShowInstallPrompt(false)}
          />
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 mx-auto w-full max-w-7xl px-4 py-4 sm:px-6">
        {currentTab === 'dashboard' && (
          <DashboardView
            sites={sites}
            inventory={inventory}
            equipment={equipment}
            orders={orders}
            onNavigate={(tab) => setCurrentTab(tab)}
            onOpenAction={(action) => setQuickAction(action)}
          />
        )}

        {currentTab === 'sites' && (
          <div className="lg:pl-64">
            <SitesView
              sites={sites}
              selectedSiteId={selectedSiteId}
              onSelectSite={(id) => setSelectedSiteId(id)}
            />
          </div>
        )}

        {currentTab === 'inventory' && (
          <div className="lg:pl-64">
            <InventoryView
              inventory={inventory}
              onUpdateQty={handleUpdateQty}
              onOpenScanModal={() => setQuickAction('scan')}
              onOpenAddStockModal={() => setQuickAction('new_stock')}
            />
          </div>
        )}

        {currentTab === 'equipment' && (
          <div className="lg:pl-64">
            <EquipmentView
              equipment={equipment}
              onUpdateStatus={handleUpdateEqStatus}
            />
          </div>
        )}

        {currentTab === 'procurement' && (
          <div className="lg:pl-64">
            <ProcurementView
              orders={orders}
              onOpenCreatePOModal={() => setQuickAction('new_po')}
            />
          </div>
        )}

        {currentTab === 'ai' && (
          <div className="lg:pl-64">
            <AIChatView />
          </div>
        )}
      </main>

      {/* Quick Action Modal Dialog */}
      <QuickActionModal
        type={quickAction}
        onClose={() => setQuickAction(null)}
        onSuccess={(msg) => {
          triggerToast(msg);
          loadAllData();
        }}
      />

      {/* Notification Drawer */}
      <NotificationDrawer
        isOpen={isNotificationsOpen}
        onClose={() => setIsNotificationsOpen(false)}
        alerts={alerts}
        onMarkAllRead={handleMarkAlertsRead}
      />

      {/* Mobile Bottom Navigation Bar */}
      <div className="lg:hidden">
        <BottomNav
          currentTab={currentTab}
          onTabChange={(tab) => setCurrentTab(tab)}
        />
      </div>

    </div>
  );
};
