import React, { useState } from 'react';
import { ShoppingCart, Plus, CheckCircle, Clock, Truck, AlertCircle, FileText } from 'lucide-react';
import { PurchaseOrder } from '../types';

interface ProcurementViewProps {
  orders: PurchaseOrder[];
  onOpenCreatePOModal: () => void;
}

export const ProcurementView: React.FC<ProcurementViewProps> = ({ orders, onOpenCreatePOModal }) => {
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const filteredOrders = orders.filter(o => filterStatus === 'all' || o.status === filterStatus);

  const getStatusBadge = (status: PurchaseOrder['status']) => {
    switch (status) {
      case 'approved':
        return <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-bold text-emerald-400 border border-emerald-500/20">Approved</span>;
      case 'pending_approval':
        return <span className="rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-bold text-amber-400 border border-amber-500/20">Pending Approval</span>;
      case 'in_transit':
        return <span className="rounded-full bg-brand-500/10 px-2.5 py-0.5 text-xs font-bold text-brand-accent border border-brand-500/20">In Transit</span>;
      default:
        return <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-bold text-slate-300">Delivered</span>;
    }
  };

  return (
    <div className="space-y-4 pb-24">
      
      {/* Top Bar */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 overflow-x-auto">
          {['all', 'pending_approval', 'approved', 'in_transit'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`active-tap shrink-0 rounded-xl px-3 py-1.5 text-xs font-semibold capitalize transition-all ${
                filterStatus === st
                  ? 'bg-brand-orange text-white shadow-glow-orange'
                  : 'glass-card text-slate-400 hover:text-slate-200'
              }`}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>

        <button
          onClick={onOpenCreatePOModal}
          className="active-tap flex shrink-0 items-center gap-1.5 rounded-xl bg-brand-orange px-3.5 py-1.5 text-xs font-bold text-white shadow-glow-orange hover:brightness-110 transition-all"
        >
          <Plus className="h-4 w-4" /> New PO
        </button>
      </div>

      {/* Orders List */}
      <div className="grid grid-cols-1 gap-3">
        {filteredOrders.map((po) => (
          <div key={po.id} className="glass-card p-4 rounded-2xl border border-slate-800 space-y-3">
            
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-brand-orange">
                    {po.poNumber}
                  </span>
                  {getStatusBadge(po.status)}
                  {po.urgent && (
                    <span className="rounded bg-red-500/20 px-1.5 py-0.5 text-[10px] font-bold text-red-400 animate-pulse">
                      Urgent
                    </span>
                  )}
                </div>
                <h4 className="text-base font-bold text-slate-100">{po.vendorName}</h4>
                <p className="text-xs text-slate-400 mt-0.5">📍 {po.siteName}</p>
              </div>

              <div className="text-right">
                <div className="text-base font-extrabold text-slate-100">
                  ₹{po.totalAmount.toLocaleString()}
                </div>
                <div className="text-[10px] text-slate-500">{po.createdAt}</div>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-2.5">
              <span className="flex items-center gap-1 text-slate-300">
                <FileText className="h-3.5 w-3.5 text-brand-accent" /> {po.itemsCount} Material Items
              </span>
              <span className="text-[11px] text-brand-accent font-medium hover:underline cursor-pointer">
                View Requisition Details →
              </span>
            </div>

          </div>
        ))}
      </div>

    </div>
  );
};
