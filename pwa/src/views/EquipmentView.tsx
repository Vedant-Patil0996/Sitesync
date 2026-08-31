import React from 'react';
import { Truck, Wrench, ShieldCheck, Fuel, UserCheck, Clock, AlertTriangle } from 'lucide-react';
import { Equipment } from '../types';

interface EquipmentViewProps {
  equipment: Equipment[];
  onUpdateStatus: (id: string, status: Equipment['status']) => void;
}

export const EquipmentView: React.FC<EquipmentViewProps> = ({ equipment, onUpdateStatus }) => {
  const getStatusBadge = (status: Equipment['status']) => {
    switch (status) {
      case 'operational':
      case 'in_use':
        return <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-bold text-emerald-400 border border-emerald-500/20">Operational</span>;
      case 'maintenance':
        return <span className="rounded-full bg-red-500/10 px-2.5 py-0.5 text-xs font-bold text-red-400 border border-red-500/20">Maintenance</span>;
      case 'idle':
        return <span className="rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-bold text-amber-400 border border-amber-500/20">Idle Standby</span>;
    }
  };

  return (
    <div className="space-y-4 pb-24">
      
      {/* Fleet Summary Header */}
      <div className="glass-card p-4 rounded-2xl border border-slate-800 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Truck className="h-4 w-4 text-brand-accent" /> Machinery Fleet Telematics
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">Realtime heavy machinery operational tracker</p>
        </div>
        <div className="text-right">
          <span className="text-lg font-extrabold text-brand-accent">{equipment.length}</span>
          <span className="text-xs text-slate-400 block">Total Vehicles</span>
        </div>
      </div>

      {/* Machinery List */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {equipment.map((eq) => (
          <div key={eq.id} className="glass-card p-4 rounded-2xl border border-slate-800 space-y-3">
            
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-300">
                    {eq.serialNo}
                  </span>
                  {getStatusBadge(eq.status)}
                </div>
                <h4 className="text-base font-bold text-slate-100">{eq.name}</h4>
                <p className="text-xs text-slate-400">📍 {eq.siteName}</p>
              </div>
            </div>

            {/* Telematics Info */}
            <div className="grid grid-cols-2 gap-2 text-xs bg-slate-950 p-2.5 rounded-xl border border-slate-900">
              <div className="flex items-center gap-2">
                <UserCheck className="h-3.5 w-3.5 text-brand-accent shrink-0" />
                <span className="text-slate-300 truncate">{eq.operator || 'No Operator'}</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                <span className="text-slate-300">{eq.hoursUsed} Hours</span>
              </div>
            </div>

            {/* Fuel Bar */}
            <div>
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="text-slate-400 flex items-center gap-1">
                  <Fuel className="h-3 w-3 text-amber-400" /> Fuel Telemetry
                </span>
                <span className="font-bold text-slate-200">{eq.fuelLevelPercent}%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-slate-900 overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    eq.fuelLevelPercent < 35 ? 'bg-red-500' : 'bg-gradient-to-r from-amber-500 to-emerald-400'
                  }`}
                  style={{ width: `${eq.fuelLevelPercent}%` }}
                />
              </div>
            </div>

            {/* Status Change Buttons */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs">
              <span className="text-[11px] text-slate-500">Service: {eq.nextServiceDate}</span>
              
              <div className="flex items-center gap-1.5">
                {eq.status !== 'in_use' && (
                  <button
                    onClick={() => onUpdateStatus(eq.id, 'in_use')}
                    className="active-tap rounded-lg bg-emerald-500/20 px-2 py-1 text-[11px] font-bold text-emerald-400 hover:bg-emerald-500/30"
                  >
                    Set Active
                  </button>
                )}
                {eq.status !== 'maintenance' && (
                  <button
                    onClick={() => onUpdateStatus(eq.id, 'maintenance')}
                    className="active-tap rounded-lg bg-red-500/20 px-2 py-1 text-[11px] font-bold text-red-400 hover:bg-red-500/30"
                  >
                    Flag Repair
                  </button>
                )}
              </div>
            </div>

          </div>
        ))}
      </div>

    </div>
  );
};
