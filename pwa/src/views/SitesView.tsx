import React, { useState } from 'react';
import { Building2, MapPin, Users, Truck, AlertCircle, Plus, ChevronRight, CheckCircle2 } from 'lucide-react';
import { Site } from '../types';

interface SitesViewProps {
  sites: Site[];
  selectedSiteId: string;
  onSelectSite: (id: string) => void;
}

export const SitesView: React.FC<SitesViewProps> = ({ sites, selectedSiteId, onSelectSite }) => {
  const [showAddSiteModal, setShowAddSiteModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const filteredSites = sites.filter(s => filterStatus === 'all' || s.status === filterStatus);

  const getStatusBadge = (status: Site['status']) => {
    switch (status) {
      case 'active':
        return <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">Active Site</span>;
      case 'planning':
        return <span className="rounded-full bg-brand-500/10 px-2.5 py-0.5 text-xs font-semibold text-brand-accent border border-brand-500/20">Planning</span>;
      case 'delayed':
        return <span className="rounded-full bg-red-500/10 px-2.5 py-0.5 text-xs font-semibold text-red-400 border border-red-500/20">Delayed</span>;
      default:
        return <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-semibold text-slate-300">Completed</span>;
    }
  };

  return (
    <div className="space-y-4 pb-24">
      
      {/* Header & Filter Controls */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 overflow-x-auto">
          {['all', 'active', 'planning', 'delayed'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`active-tap rounded-xl px-3 py-1.5 text-xs font-semibold capitalize transition-all ${
                filterStatus === st
                  ? 'bg-brand-500 text-white shadow-glow'
                  : 'glass-card text-slate-400 hover:text-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <button
          onClick={() => setShowAddSiteModal(true)}
          className="active-tap flex shrink-0 items-center gap-1.5 rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 px-3.5 py-1.5 text-xs font-bold text-white shadow-glow hover:brightness-110 transition-all"
        >
          <Plus className="h-4 w-4" /> Add Site
        </button>
      </div>

      {/* Sites List Grid */}
      <div className="grid grid-cols-1 gap-4">
        {filteredSites.map((site) => (
          <div
            key={site.id}
            onClick={() => onSelectSite(site.id)}
            className={`glass-card glass-card-hover cursor-pointer rounded-2xl p-5 border transition-all ${
              selectedSiteId === site.id ? 'border-brand-accent shadow-glow' : 'border-slate-800'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="rounded-md bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-brand-accent">
                    {site.code}
                  </span>
                  {getStatusBadge(site.status)}
                </div>
                <h3 className="text-base font-bold text-slate-100">{site.name}</h3>
                <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5 text-slate-500 shrink-0" /> {site.location}
                </p>
              </div>
              <ChevronRight className="h-5 w-5 text-slate-600 shrink-0 mt-1" />
            </div>

            {/* Progress Bar */}
            <div className="mt-4">
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-slate-400">Construction Completion</span>
                <span className="font-bold text-brand-accent">{site.progress}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-900 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-brand-600 to-brand-accent"
                  style={{ width: `${site.progress}%` }}
                />
              </div>
            </div>

            {/* Site Stats Footer */}
            <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs border-t border-slate-800/80 pt-3">
              <div className="flex items-center justify-center gap-1.5 text-slate-300">
                <Users className="h-3.5 w-3.5 text-brand-accent" />
                <span>{site.workersOnSite} Workers</span>
              </div>
              <div className="flex items-center justify-center gap-1.5 text-slate-300">
                <Truck className="h-3.5 w-3.5 text-emerald-400" />
                <span>{site.activeEquipment} Machinery</span>
              </div>
              <div className="flex items-center justify-center gap-1.5 text-slate-300">
                <AlertCircle className="h-3.5 w-3.5 text-amber-400" />
                <span>{site.alertsCount} Alerts</span>
              </div>
            </div>

          </div>
        ))}
      </div>

      {/* Add Site Modal Simulation */}
      {showAddSiteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
          <div className="w-full max-w-md glass-panel rounded-2xl p-6 border border-slate-700">
            <h3 className="text-base font-bold text-slate-100 mb-3">Register New Construction Site</h3>
            <p className="text-xs text-slate-400 mb-4">Add site location, supervisor details, and budget allocations.</p>
            <div className="space-y-3 text-xs">
              <input type="text" placeholder="Site Name" className="w-full glass-input rounded-lg px-3 py-2 text-slate-100" />
              <input type="text" placeholder="Location / Address" className="w-full glass-input rounded-lg px-3 py-2 text-slate-100" />
              <input type="number" placeholder="Budget Allocation (₹)" className="w-full glass-input rounded-lg px-3 py-2 text-slate-100" />
            </div>
            <div className="mt-5 flex gap-2">
              <button
                onClick={() => setShowAddSiteModal(false)}
                className="w-1/2 rounded-xl glass-card py-2 text-xs text-slate-400 font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowAddSiteModal(false)}
                className="w-1/2 rounded-xl bg-brand-500 py-2 text-xs text-white font-bold shadow-glow"
              >
                Save Site
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
