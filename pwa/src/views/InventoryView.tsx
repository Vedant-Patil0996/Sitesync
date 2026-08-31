import React, { useState } from 'react';
import { Package, Search, QrCode, Plus, Minus, AlertTriangle, CheckCircle, ShieldAlert } from 'lucide-react';
import { InventoryItem } from '../types';

interface InventoryViewProps {
  inventory: InventoryItem[];
  onUpdateQty: (id: string, delta: number) => void;
  onOpenScanModal: () => void;
  onOpenAddStockModal: () => void;
}

export const InventoryView: React.FC<InventoryViewProps> = ({
  inventory,
  onUpdateQty,
  onOpenScanModal,
  onOpenAddStockModal
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const categories = ['All', 'Cement & Concrete', 'Steel & Metals', 'Aggregates', 'Electrical', 'Plumbing', 'Safety'];

  const filteredInventory = inventory.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase()) || item.sku.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const getStatusBadge = (status: InventoryItem['status']) => {
    switch (status) {
      case 'in_stock':
        return <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/20">In Stock</span>;
      case 'low_stock':
        return <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-bold text-amber-400 border border-amber-500/20">Low Stock</span>;
      case 'out_of_stock':
        return <span className="rounded-full bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-400 border border-red-500/20">Out of Stock</span>;
    }
  };

  return (
    <div className="space-y-4 pb-24">
      
      {/* Top Search & Actions */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center justify-between">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search material SKU or name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full glass-input rounded-xl pl-9 pr-4 py-2 text-xs text-slate-100 placeholder-slate-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onOpenScanModal}
            className="active-tap flex-1 sm:flex-none flex items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 px-3.5 py-2 text-xs font-bold text-white shadow-glow hover:brightness-110 transition-all"
          >
            <QrCode className="h-4 w-4" /> Scan QR
          </button>

          <button
            onClick={onOpenAddStockModal}
            className="active-tap flex-1 sm:flex-none flex items-center justify-center gap-1.5 rounded-xl glass-card px-3.5 py-2 text-xs font-semibold text-slate-200 hover:border-brand-500/40 hover:text-white transition-all"
          >
            <Plus className="h-4 w-4 text-emerald-400" /> Add Item
          </button>
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`active-tap shrink-0 rounded-xl px-3 py-1.5 text-xs font-medium transition-all ${
              selectedCategory === cat
                ? 'bg-brand-500 text-white font-bold shadow-glow'
                : 'glass-card text-slate-400 hover:text-slate-200'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Inventory Items List */}
      <div className="grid grid-cols-1 gap-3">
        {filteredInventory.length === 0 ? (
          <div className="glass-card p-8 rounded-2xl text-center text-slate-400 text-xs">
            No stock items found matching category & search filters.
          </div>
        ) : (
          filteredInventory.map((item) => (
            <div
              key={item.id}
              className="glass-card p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-brand-accent bg-slate-800 px-2 py-0.5 rounded">
                    {item.sku}
                  </span>
                  {getStatusBadge(item.status)}
                  <span className="text-[10px] text-slate-500">Updated {item.lastUpdated}</span>
                </div>
                <h4 className="text-sm font-bold text-slate-100">{item.name}</h4>
                <p className="text-xs text-slate-400">
                  Category: <span className="text-slate-300">{item.category}</span> · Min Threshold: <span className="text-amber-400">{item.minThreshold} {item.unit}</span>
                </p>
              </div>

              {/* Quantity Counter Controls */}
              <div className="flex items-center justify-between sm:justify-end gap-3 pt-2 sm:pt-0 border-t sm:border-0 border-slate-800">
                <div className="text-left sm:text-right">
                  <div className="text-base font-extrabold text-slate-100">
                    {item.quantity} <span className="text-xs font-normal text-slate-400">{item.unit}</span>
                  </div>
                  <div className="text-[10px] text-slate-500">₹{item.unitCost}/{item.unit}</div>
                </div>

                <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
                  <button
                    onClick={() => onUpdateQty(item.id, -10)}
                    className="active-tap h-7 w-7 rounded-lg glass-card flex items-center justify-center text-slate-300 hover:text-red-400"
                    title="Decrease 10"
                  >
                    <Minus className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => onUpdateQty(item.id, 10)}
                    className="active-tap h-7 w-7 rounded-lg glass-card flex items-center justify-center text-slate-300 hover:text-emerald-400"
                    title="Increase 10"
                  >
                    <Plus className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

            </div>
          ))
        )}
      </div>

    </div>
  );
};
