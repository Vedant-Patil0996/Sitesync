'use client';

import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { apiFetch } from '@/lib/api';
import { toast } from 'sonner';
import {
  Package, QrCode, ArrowDownToLine, Flame, ArrowRightLeft,
  RotateCcw, ChevronRight, Loader2, AlertTriangle, CheckCircle2,
  Clock, Minus, TrendingDown
} from 'lucide-react';

interface PassportData {
  batch_code: string;
  material_name: string;
  material_id: number;
  unit: string;
  site_name: string;
  site_id: number;
  supplier: string | null;
  original_qty: number;
  current_qty: number;
  pct_used: number;
  status: string;
  received_by: string | null;
  received_at: string | null;
  timeline: Array<{
    action: string;
    quantity: number;
    performed_by: string;
    role: string;
    date: string | null;
    reason: string | null;
  }>;
  discrepancies: Array<{
    expected: number;
    actual: number;
    diff: number;
    date: string | null;
  }>;
}

type ActionType = 'receive' | 'consume' | 'transfer' | 'damage' | 'return' | null;

const STATUS_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  IN_STOCK: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300' },
  RECEIVED: { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-300' },
  PARTIALLY_CONSUMED: { bg: 'bg-amber-100', text: 'text-amber-800', border: 'border-amber-300' },
  DEPLETED: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300' },
  TRANSFER_PENDING: { bg: 'bg-purple-100', text: 'text-purple-800', border: 'border-purple-300' },
  DAMAGED: { bg: 'bg-red-200', text: 'text-red-900', border: 'border-red-400' },
  RETURNED: { bg: 'bg-gray-100', text: 'text-gray-600', border: 'border-gray-300' },
};

const ACTION_ICONS: Record<string, React.ReactNode> = {
  RECEIVE: <ArrowDownToLine className="h-3.5 w-3.5 text-green-600" />,
  CONSUME: <Minus className="h-3.5 w-3.5 text-orange-500" />,
  TRANSFER: <ArrowRightLeft className="h-3.5 w-3.5 text-blue-500" />,
  DAMAGE: <Flame className="h-3.5 w-3.5 text-red-500" />,
  RETURN: <RotateCcw className="h-3.5 w-3.5 text-gray-500" />,
};

interface QRScannerModalProps {
  open: boolean;
  onClose: () => void;
  onActionComplete?: () => void;
  sites?: Array<{ id: number; name: string }>;
  initialCode?: string;
}

export function QRScannerModal({ open, onClose, onActionComplete, sites = [], initialCode = '' }: QRScannerModalProps) {
  const [step, setStep] = useState<'scan' | 'passport' | 'action' | 'confirm' | 'done'>('scan');
  const [manualCode, setManualCode] = useState(initialCode);
  const [passport, setPassport] = useState<PassportData | null>(null);
  const [selectedAction, setSelectedAction] = useState<ActionType>(null);
  const [loading, setLoading] = useState(false);

  // Action form state
  const [qty, setQty] = useState('');
  const [expectedQty, setExpectedQty] = useState('');
  const [activity, setActivity] = useState('');
  const [reason, setReason] = useState('');
  const [destSiteId, setDestSiteId] = useState('');
  const [actionResult, setActionResult] = useState<any>(null);

  const reset = () => {
    setStep('scan');
    setManualCode('');
    setPassport(null);
    setSelectedAction(null);
    setLoading(false);
    setQty('');
    setExpectedQty('');
    setActivity('');
    setReason('');
    setDestSiteId('');
    setActionResult(null);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  React.useEffect(() => {
    if (open && initialCode) {
      setManualCode(initialCode);
      // We can't auto-scan immediately here because handleScan uses the state `manualCode` which might not have updated yet,
      // but we can pass it directly.
      const runScan = async (codeStr: string) => {
        let code = codeStr.trim();
        if (!code) return;
        if (code.startsWith('{')) {
          try {
            const obj = JSON.parse(code);
            code = obj.batch_id || obj.batch_code || code;
          } catch {}
        } else if (code.includes('batch=')) {
          const match = code.match(/batch=([^&]+)/);
          if (match) code = match[1];
        }
        setLoading(true);
        try {
          const data = await apiFetch<PassportData>('/api/v1/inventory/scan', {
            method: 'POST',
            body: JSON.stringify({ batch_id: code }),
          });
          setPassport(data);
          setStep('passport');
        } catch (e: any) {
          toast.error(e.message || 'Batch not found');
        } finally {
          setLoading(false);
        }
      };
      runScan(initialCode);
    }
  }, [open, initialCode]);

  const handleScan = async () => {
    let code = manualCode.trim();
    if (!code) { toast.error('Enter a batch code'); return; }

    // Smart payload parser for JSON, URL params, or raw code
    if (code.startsWith('{')) {
      try {
        const obj = JSON.parse(code);
        code = obj.batch_id || obj.batch_code || code;
      } catch {}
    } else if (code.includes('batch=')) {
      const match = code.match(/batch=([^&]+)/);
      if (match) code = match[1];
    }

    setLoading(true);
    try {
      const data = await apiFetch<PassportData>('/api/v1/inventory/scan', {
        method: 'POST',
        body: JSON.stringify({ batch_id: code }),
      });
      setPassport(data);
      setStep('passport');
    } catch (e: any) {
      toast.error(e.message || 'Batch not found');
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async () => {
    if (!passport) return;
    setLoading(true);
    try {
      let endpoint = '';
      let body: any = { batch_code: passport.batch_code, qty: parseFloat(qty), reason, activity };

      if (selectedAction === 'receive') {
        endpoint = '/api/v1/inventory/receive';
        body = { batch_code: passport.batch_code, actual_qty: parseFloat(qty), expected_qty: parseFloat(expectedQty) };
      } else if (selectedAction === 'consume') {
        endpoint = '/api/v1/inventory/consume';
        body = { batch_code: passport.batch_code, qty: parseFloat(qty), activity, reason };
      } else if (selectedAction === 'transfer') {
        endpoint = '/api/v1/inventory/transfer-batch';
        body = { batch_code: passport.batch_code, qty: parseFloat(qty), dest_site_id: parseInt(destSiteId) };
      } else if (selectedAction === 'damage') {
        endpoint = '/api/v1/inventory/damage';
        body = { batch_code: passport.batch_code, qty: parseFloat(qty), reason };
      } else if (selectedAction === 'return') {
        endpoint = '/api/v1/inventory/return-batch';
        body = { batch_code: passport.batch_code, qty: parseFloat(qty), reason };
      }

      const result = await apiFetch<any>(endpoint, {
        method: 'POST',
        body: JSON.stringify(body),
      });
      setActionResult(result);
      setStep('done');
      toast.success(`${selectedAction?.charAt(0).toUpperCase()}${selectedAction?.slice(1)} recorded successfully`);
      onActionComplete?.();
    } catch (e: any) {
      toast.error(e.message || 'Action failed');
    } finally {
      setLoading(false);
    }
  };

  const pctRemaining = passport ? Math.max(0, 100 - (passport.pct_used || 0)) : 0;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <QrCode className="h-5 w-5 text-primary" />
            {step === 'scan' && 'Scan Material'}
            {step === 'passport' && 'Material Passport'}
            {step === 'action' && `${selectedAction?.charAt(0).toUpperCase()}${selectedAction?.slice(1)} — ${passport?.batch_code}`}
            {step === 'confirm' && 'Confirm Action'}
            {step === 'done' && 'Done'}
          </DialogTitle>
        </DialogHeader>

        {/* STEP 1: Scan */}
        {step === 'scan' && (
          <div className="space-y-4">
            <div className="border-2 border-dashed border-border rounded-lg p-8 text-center bg-muted/30">
              <QrCode className="h-12 w-12 mx-auto mb-3 text-muted-foreground" />
              <p className="text-sm font-medium text-muted-foreground mb-1">Camera scanner</p>
              <p className="text-xs text-muted-foreground">
                Enter batch code manually below (camera scanner requires HTTPS)
              </p>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-bold">Batch Code</label>
              <Input
                placeholder="e.g. BAT-2026-64047"
                value={manualCode}
                onChange={e => setManualCode(e.target.value.toUpperCase())}
                onKeyDown={e => e.key === 'Enter' && handleScan()}
                className="font-mono"
              />
            </div>
            <Button className="w-full gap-2" onClick={handleScan} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ChevronRight className="h-4 w-4" />}
              Look Up Batch
            </Button>
          </div>
        )}

        {/* STEP 2: Material Passport */}
        {step === 'passport' && passport && (
          <div className="space-y-4">
            {/* Header */}
            <div className="border-2 border-border p-4 bg-card">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="font-black text-lg leading-tight">{passport.material_name}</h3>
                  <p className="text-sm text-muted-foreground font-mono">{passport.batch_code}</p>
                </div>
                <span className={`text-xs font-bold px-2 py-1 border rounded ${STATUS_COLORS[passport.status]?.bg} ${STATUS_COLORS[passport.status]?.text} ${STATUS_COLORS[passport.status]?.border}`}>
                  {passport.status.replace(/_/g, ' ')}
                </span>
              </div>
              {/* Progress bar */}
              <div className="mb-3">
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span>Remaining: <strong>{passport.current_qty} {passport.unit}</strong></span>
                  <span>{pctRemaining.toFixed(0)}% of {passport.original_qty} {passport.unit}</span>
                </div>
                <div className="h-2.5 bg-muted border border-border rounded-sm overflow-hidden">
                  <div
                    className={`h-full transition-all ${pctRemaining < 20 ? 'bg-destructive' : pctRemaining < 50 ? 'bg-amber-500' : 'bg-green-500'}`}
                    style={{ width: `${pctRemaining}%` }}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div><span className="text-muted-foreground">Site: </span><strong>{passport.site_name}</strong></div>
                <div><span className="text-muted-foreground">Supplier: </span><strong>{passport.supplier || '—'}</strong></div>
                <div><span className="text-muted-foreground">Received by: </span><strong>{passport.received_by || '—'}</strong></div>
                <div><span className="text-muted-foreground">Received: </span><strong>{passport.received_at ? new Date(passport.received_at).toLocaleDateString() : '—'}</strong></div>
              </div>
            </div>

            {/* Discrepancies warning */}
            {passport.discrepancies?.length > 0 && (
              <div className="border-2 border-amber-400 bg-amber-50 dark:bg-amber-950/20 p-3 flex gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                <div className="text-xs">
                  <p className="font-bold text-amber-800 dark:text-amber-300">Delivery Discrepancy Recorded</p>
                  {passport.discrepancies.map((d, i) => (
                    <p key={i} className="text-amber-700 dark:text-amber-400">
                      Expected {d.expected}, received {d.actual} ({d.diff > 0 ? '+' : ''}{d.diff} {passport.unit})
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Timeline */}
            {passport.timeline.length > 0 && (
              <div>
                <h4 className="text-xs font-black uppercase tracking-wide text-muted-foreground mb-2">Lifecycle</h4>
                <div className="space-y-1.5">
                  {passport.timeline.map((tx, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs border border-border px-3 py-2 bg-card">
                      {ACTION_ICONS[tx.action] || <Package className="h-3.5 w-3.5" />}
                      <span className="font-bold w-20">{tx.action}</span>
                      <span className="font-mono">{tx.quantity} {passport.unit}</span>
                      <span className="text-muted-foreground flex-1 truncate">— {tx.performed_by}</span>
                      {tx.date && <span className="text-muted-foreground">{new Date(tx.date).toLocaleDateString()}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action buttons */}
            <div className="grid grid-cols-2 gap-2 pt-2">
              {[
                { action: 'receive' as ActionType, icon: <ArrowDownToLine className="h-4 w-4" />, label: 'Receive', color: 'border-green-400' },
                { action: 'consume' as ActionType, icon: <Minus className="h-4 w-4" />, label: 'Consume', color: 'border-orange-400' },
                { action: 'transfer' as ActionType, icon: <ArrowRightLeft className="h-4 w-4" />, label: 'Transfer', color: 'border-blue-400' },
                { action: 'damage' as ActionType, icon: <Flame className="h-4 w-4" />, label: 'Damage', color: 'border-red-400' },
                { action: 'return' as ActionType, icon: <RotateCcw className="h-4 w-4" />, label: 'Return', color: 'border-gray-400' },
              ].map(({ action, icon, label, color }) => (
                <Button
                  key={action}
                  variant="outline"
                  className={`gap-2 justify-start border-2 ${color} hover:border-primary`}
                  onClick={() => { setSelectedAction(action); setStep('action'); }}
                >
                  {icon} {label}
                </Button>
              ))}
            </div>
            <Button variant="ghost" size="sm" className="w-full" onClick={() => setStep('scan')}>
              ← Scan different batch
            </Button>
          </div>
        )}

        {/* STEP 3: Action Form */}
        {step === 'action' && passport && selectedAction && (
          <div className="space-y-4">
            <div className="border-2 border-border p-3 bg-muted/30 text-sm">
              <span className="font-bold">{passport.material_name}</span>
              <span className="text-muted-foreground"> · {passport.batch_code} · </span>
              <span className="font-bold">{passport.current_qty} {passport.unit} available</span>
            </div>

            {selectedAction === 'receive' && (
              <>
                <div className="space-y-1">
                  <label className="text-sm font-bold">Expected Quantity</label>
                  <Input type="number" placeholder="Expected qty" value={expectedQty} onChange={e => setExpectedQty(e.target.value)} />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-bold">Actually Received</label>
                  <Input type="number" placeholder="Actual qty" value={qty} onChange={e => setQty(e.target.value)} />
                  {qty && expectedQty && parseFloat(qty) !== parseFloat(expectedQty) && (
                    <p className="text-xs text-amber-600 font-medium flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3" />
                      Discrepancy: {(parseFloat(qty) - parseFloat(expectedQty)).toFixed(0)} {passport.unit}
                    </p>
                  )}
                </div>
              </>
            )}

            {(selectedAction === 'consume' || selectedAction === 'damage' || selectedAction === 'return') && (
              <div className="space-y-1">
                <label className="text-sm font-bold">Quantity ({passport.unit})</label>
                <Input type="number" placeholder="0" max={passport.current_qty} value={qty} onChange={e => setQty(e.target.value)} />
              </div>
            )}

            {selectedAction === 'consume' && (
              <div className="space-y-1">
                <label className="text-sm font-bold">Activity / Work Area</label>
                <Input placeholder="e.g. Foundation, Column Work" value={activity} onChange={e => setActivity(e.target.value)} />
              </div>
            )}

            {selectedAction === 'transfer' && (
              <>
                <div className="space-y-1">
                  <label className="text-sm font-bold">Quantity ({passport.unit})</label>
                  <Input type="number" placeholder="0" max={passport.current_qty} value={qty} onChange={e => setQty(e.target.value)} />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-bold">Destination Site</label>
                  <select
                    value={destSiteId}
                    onChange={e => setDestSiteId(e.target.value)}
                    className="w-full border-2 border-border rounded-md px-3 py-2 text-sm bg-background"
                  >
                    <option value="">Select site...</option>
                    {sites.filter(s => s.id !== passport.site_id).map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
              </>
            )}

            {(selectedAction === 'damage' || selectedAction === 'return') && (
              <div className="space-y-1">
                <label className="text-sm font-bold">Reason</label>
                <Input placeholder="Reason (optional)" value={reason} onChange={e => setReason(e.target.value)} />
              </div>
            )}

            {/* Confirmation box */}
            <div className="border-2 border-border p-3 bg-muted/30 text-sm space-y-1">
              <p className="font-black">Confirm {selectedAction?.toUpperCase()}</p>
              <p className="text-muted-foreground">
                You are about to {selectedAction}{' '}
                <strong>{qty || '?'} {passport.unit}</strong> of{' '}
                <strong>{passport.material_name}</strong> (Batch {passport.batch_code}) at{' '}
                <strong>{passport.site_name}</strong>.
              </p>
            </div>

            <div className="flex gap-2">
              <Button
                className="flex-1 gap-2"
                onClick={handleAction}
                disabled={loading || !qty}
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                Confirm
              </Button>
              <Button variant="outline" onClick={() => setStep('passport')}>Cancel</Button>
            </div>
          </div>
        )}

        {/* STEP 4: Done */}
        {step === 'done' && actionResult && (
          <div className="text-center space-y-4 py-4">
            <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto" />
            <h3 className="font-black text-xl">
              {selectedAction?.charAt(0).toUpperCase()}{selectedAction?.slice(1)} Recorded
            </h3>
            <div className="border-2 border-border p-4 text-left text-sm space-y-1">
              <p><span className="text-muted-foreground">Batch:</span> <strong className="font-mono">{actionResult.batch_code}</strong></p>
              {actionResult.remaining !== undefined && (
                <p><span className="text-muted-foreground">Remaining:</span> <strong>{actionResult.remaining} {passport?.unit}</strong></p>
              )}
              {actionResult.discrepancy && (
                <p className="text-amber-600 font-medium">
                  ⚠️ Discrepancy recorded: {actionResult.discrepancy.diff > 0 ? '+' : ''}{actionResult.discrepancy.diff} {passport?.unit}
                </p>
              )}
              {actionResult.status && (
                <p><span className="text-muted-foreground">Status:</span> <strong>{actionResult.status.replace(/_/g, ' ')}</strong></p>
              )}
            </div>
            <div className="flex gap-2">
              <Button className="flex-1" onClick={() => { reset(); setStep('scan'); }}>
                Scan Another
              </Button>
              <Button variant="outline" onClick={handleClose}>Done</Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
