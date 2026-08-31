import React from 'react';
import { X, AlertTriangle, AlertCircle, Info, CheckCircle2, BellOff } from 'lucide-react';
import { AlertNotification } from '../types';

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  alerts: AlertNotification[];
  onMarkAllRead: () => void;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({
  isOpen,
  onClose,
  alerts,
  onMarkAllRead
}) => {
  if (!isOpen) return null;

  const getAlertIcon = (type: AlertNotification['type']) => {
    switch (type) {
      case 'critical': return <AlertTriangle className="h-4 w-4 text-red-400" />;
      case 'warning': return <AlertCircle className="h-4 w-4 text-amber-400" />;
      case 'success': return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
      default: return <Info className="h-4 w-4 text-brand-accent" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-opacity">
      <div className="w-full max-w-sm h-full glass-panel border-l border-slate-800 p-5 flex flex-col justify-between shadow-2xl animate-in slide-in-from-right">
        
        {/* Drawer Header */}
        <div>
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-100">Site Notifications</h2>
              <span className="rounded-full bg-brand-500/20 px-2 py-0.5 text-xs font-semibold text-brand-accent">
                {alerts.length}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {alerts.length > 0 && (
                <button
                  onClick={onMarkAllRead}
                  className="text-xs text-brand-accent hover:underline font-medium"
                >
                  Mark read
                </button>
              )}
              <button
                onClick={onClose}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Notifications List */}
          <div className="mt-4 space-y-3 overflow-y-auto max-h-[calc(100vh-140px)] pr-1">
            {alerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <BellOff className="h-10 w-10 text-slate-600 mb-2" />
                <p className="text-sm text-slate-400">No active alerts for your construction sites.</p>
              </div>
            ) : (
              alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`glass-card p-3.5 rounded-xl border transition-all ${
                    alert.read ? 'opacity-60 border-slate-800' : 'border-brand-500/30 shadow-sm'
                  }`}
                >
                  <div className="flex items-start gap-2.5">
                    <div className="mt-0.5 shrink-0">{getAlertIcon(alert.type)}</div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-slate-200">{alert.title}</h4>
                        <span className="text-[10px] text-slate-500">{alert.timestamp}</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed">{alert.message}</p>
                      {alert.siteName && (
                        <div className="mt-2 inline-block rounded bg-slate-800/80 px-2 py-0.5 text-[10px] font-medium text-slate-300">
                          📍 {alert.siteName}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 pt-3 text-center">
          <p className="text-[11px] text-slate-500">SiteSync Realtime Notification Engine</p>
        </div>

      </div>
    </div>
  );
};
