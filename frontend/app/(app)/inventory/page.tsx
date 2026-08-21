'use client';

import * as React from 'react';
import {
  Package, Plus, ArrowRightLeft, Search, QrCode, Download,
  AlertTriangle, Clock, CheckCircle, ChevronRight, RefreshCw, Loader2
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/page-header';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { Pagination } from '@/components/shared/pagination';
import { apiFetch } from '@/lib/api';
import { formatDate } from '@/lib/types';
import { toast } from 'sonner';
import { QRCodeGenerator } from '@/components/inventory/qr-code-generator';
import { QRScannerModal } from '@/components/inventory/qr-scanner-modal';
import { useSearchParams, useRouter } from 'next/navigation';

const STATUS_STYLES: Record<string, string> = {
  IN_STOCK: 'bg-green-100 text-green-800 border-green-300',
  RECEIVED: 'bg-blue-100 text-blue-800 border-blue-300',
  PARTIALLY_CONSUMED: 'bg-amber-100 text-amber-800 border-amber-300',
  DEPLETED: 'bg-red-100 text-red-800 border-red-300',
  TRANSFER_PENDING: 'bg-purple-100 text-purple-800 border-purple-300',
  TRANSFERRED: 'bg-gray-100 text-gray-600 border-gray-300',
  DAMAGED: 'bg-red-200 text-red-900 border-red-400',
  RETURNED: 'bg-gray-100 text-gray-500 border-gray-300',
};

type TabType = 'inventory' | 'batches' | 'discrepancies';

export default function InventoryPage() {
  const [activeTab, setActiveTab] = React.useState<TabType>('inventory');
  const [search, setSearch] = React.useState('');
  const [siteFilter, setSiteFilter] = React.useState('all');
  const [showTxForm, setShowTxForm] = React.useState(false);
  const [showQRScanner, setShowQRScanner] = React.useState(false);
  const [selectedBatchForQR, setSelectedBatchForQR] = React.useState<any>(null);
  const [statusFilter, setStatusFilter] = React.useState('all');

  const searchParams = useSearchParams();
  const router = useRouter();
  const initialScan = searchParams.get('scan');
  
  // State for scanner modal
  const [scannerInitialCode, setScannerInitialCode] = React.useState('');

  const [inventory, setInventory] = React.useState<any[]>([]);
  const [batches, setBatches] = React.useState<any[]>([]);
  const [discrepancies, setDiscrepancies] = React.useState<any[]>([]);
  const [sites, setSites] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [batchesLoading, setBatchesLoading] = React.useState(false);
  const [page, setPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const limit = 10;

  const [txType, setTxType] = React.useState('stock_in');
  const [txInventoryId, setTxInventoryId] = React.useState('');
  const [txQuantity, setTxQuantity] = React.useState('');
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const loadInventory = React.useCallback(async () => {
    setLoading(true);
    try {
      const skip = (page - 1) * limit;
      const [invRes, sitesRes] = await Promise.all([
        apiFetch<any>(`/api/v1/inventory?skip=${skip}&limit=${limit}`),
        apiFetch<any>(`/api/v1/sites?skip=0&limit=100`)
      ]);
      setInventory(invRes.items);
      setTotalPages(invRes.pages);
      setSites(sitesRes.items || []);
    } catch (error) {
      toast.error('Failed to load inventory data');
    } finally {
      setLoading(false);
    }
  }, [page]);

  const loadBatches = React.useCallback(async () => {
    setBatchesLoading(true);
    try {
      const data = await apiFetch<any[]>('/api/v1/inventory/batches');
      setBatches(data);
    } catch (error) {
      toast.error('Failed to load batches');
    } finally {
      setBatchesLoading(false);
    }
  }, []);

  const loadDiscrepancies = React.useCallback(async () => {
    try {
      const data = await apiFetch<any[]>('/api/v1/inventory/discrepancies');
      setDiscrepancies(data);
    } catch (error) {
      // May not have permission — silently ignore for contractor role
    }
  }, []);

  React.useEffect(() => { loadInventory(); }, [loadInventory]);
  React.useEffect(() => {
    if (activeTab === 'batches') loadBatches();
    if (activeTab === 'discrepancies') loadDiscrepancies();
  }, [activeTab, loadBatches, loadDiscrepancies]);

  // Auto-open scanner if URL has ?scan=...
  React.useEffect(() => {
    if (initialScan) {
      setScannerInitialCode(initialScan);
      setShowQRScanner(true);
      // Clean up URL so it doesn't keep opening on refresh
      router.replace('/inventory');
    }
  }, [initialScan, router]);

  const handleSaveTransaction = async () => {
    if (!txInventoryId || !txQuantity) {
      toast.error('Please select a material and enter quantity'); return;
    }
    const selectedInv = inventory.find(i => String(i.id) === txInventoryId);
    if (!selectedInv) { toast.error('Invalid material selection'); return; }
    setIsSubmitting(true);
    try {
      await apiFetch<any>('/api/v1/inventory/transactions', {
        method: 'POST',
        body: JSON.stringify({
          site_id: selectedInv.site_id,
          material_id: selectedInv.material_id,
          type: txType,
          quantity: parseFloat(txQuantity),
          reference: ''
        }),
      });
      toast.success('Transaction saved');
      setShowTxForm(false);
      setTxInventoryId('');
      setTxQuantity('');
      loadInventory();
    } catch (error: any) {
      toast.error(error.message || 'Failed to save transaction');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleExport = async () => {
    try {
      const token = localStorage.getItem('siteSyncToken');
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_BASE}/api/v1/inventory/batches/export`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'batches.csv';
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Export downloaded');
    } catch {
      toast.error('Export failed');
    }
  };

  const filteredInventory = inventory.filter(item => {
    const matchesSearch = item.material_name.toLowerCase().includes(search.toLowerCase());
    const matchesSite = siteFilter === 'all' || String(item.site_id) === siteFilter;
    return matchesSearch && matchesSite;
  });

  const filteredBatches = batches.filter(b => {
    const matchesSearch = b.material_name.toLowerCase().includes(search.toLowerCase()) ||
      b.batch_code.toLowerCase().includes(search.toLowerCase());
    const matchesSite = siteFilter === 'all' || String(b.site_id) === siteFilter;
    const matchesStatus = statusFilter === 'all' || b.status === statusFilter;
    return matchesSearch && matchesSite && matchesStatus;
  });

  const batchStats = React.useMemo(() => ({
    total: batches.length,
    in_stock: batches.filter(b => b.status === 'IN_STOCK').length,
    low: batches.filter(b => b.pct_remaining < 20 && b.pct_remaining > 0).length,
    depleted: batches.filter(b => b.status === 'DEPLETED').length,
    pending: batches.filter(b => b.status === 'TRANSFER_PENDING').length,
  }), [batches]);

  return (
    <div>
      <PageHeader
        title="Inventory"
        description="Track stock levels and material batch lifecycle"
        action={
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="gap-2 border-2 border-primary text-primary hover:bg-primary hover:text-primary-foreground font-bold"
              onClick={() => setShowQRScanner(true)}
            >
              <QrCode className="h-4 w-4" /> 📷 Scan Material
            </Button>
            <Button className="gap-2" onClick={() => setShowTxForm(!showTxForm)}>
              <Plus className="h-4 w-4" /> Log Transaction
            </Button>
          </div>
        }
      />

      {/* Transaction form */}
      {showTxForm && (
        <Card className="mb-6">
          <CardHeader><CardTitle className="text-lg">Log Stock Transaction</CardTitle></CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <label className="text-sm font-bold">Type</label>
                <Select value={txType} onValueChange={setTxType}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="stock_in">Stock In</SelectItem>
                    <SelectItem value="stock_out">Stock Out</SelectItem>
                    <SelectItem value="transfer_out">Transfer Out</SelectItem>
                    <SelectItem value="transfer_in">Transfer In</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-bold">Material</label>
                <Select value={txInventoryId} onValueChange={setTxInventoryId}>
                  <SelectTrigger><SelectValue placeholder="Select material" /></SelectTrigger>
                  <SelectContent>
                    {inventory.map(item => (
                      <SelectItem key={item.id} value={String(item.id)}>
                        {item.material_name} ({item.site_name})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-bold">Quantity</label>
                <Input type="number" placeholder="0" value={txQuantity} onChange={e => setTxQuantity(e.target.value)} />
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <Button onClick={handleSaveTransaction} disabled={isSubmitting}>
                {isSubmitting ? 'Saving...' : 'Save Transaction'}
              </Button>
              <Button variant="outline" onClick={() => setShowTxForm(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <div className="mb-4 flex gap-1 border-b-2 border-border">
        {(['inventory', 'batches', 'discrepancies'] as TabType[]).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-bold capitalize transition-colors border-b-2 -mb-0.5 ${
              activeTab === tab
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab === 'discrepancies' ? `⚠️ Discrepancies ${discrepancies.length > 0 ? `(${discrepancies.length})` : ''}` : tab === 'batches' ? `📦 Batches ${batches.length > 0 ? `(${batches.length})` : ''}` : '📊 Stock Levels'}
          </button>
        ))}
      </div>

      {/* Filters row */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={activeTab === 'batches' ? 'Search batches or batch code...' : 'Search materials...'}
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={siteFilter} onValueChange={setSiteFilter}>
          <SelectTrigger className="w-full sm:w-[200px]">
            <SelectValue placeholder="Filter by site" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Sites</SelectItem>
            {sites.map(site => (
              <SelectItem key={site.id} value={String(site.id)}>{site.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        {activeTab === 'batches' && (
          <>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                {['RECEIVED', 'IN_STOCK', 'PARTIALLY_CONSUMED', 'TRANSFER_PENDING', 'DEPLETED', 'DAMAGED', 'RETURNED'].map(s => (
                  <SelectItem key={s} value={s}>{s.replace(/_/g, ' ')}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" className="gap-2" onClick={handleExport}>
              <Download className="h-4 w-4" /> Export CSV
            </Button>
          </>
        )}
      </div>

      {/* TAB: INVENTORY (Stock Levels) */}
      {activeTab === 'inventory' && (
        loading ? (
          <div className="flex h-32 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <>
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Material</TableHead>
                      <TableHead>Site</TableHead>
                      <TableHead>Current Stock</TableHead>
                      <TableHead>Reorder Level</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Updated</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredInventory.map(item => {
                      const isLow = item.quantity <= item.reorder_level;
                      return (
                        <TableRow key={item.id}>
                          <TableCell className="font-bold">{item.material_name}</TableCell>
                          <TableCell className="text-muted-foreground">{item.site_name}</TableCell>
                          <TableCell className="font-extrabold">{item.quantity} {item.unit}</TableCell>
                          <TableCell>{item.reorder_level} {item.unit}</TableCell>
                          <TableCell>
                            {isLow
                              ? <Badge variant="destructive" className="brutal-badge">LOW STOCK</Badge>
                              : <Badge variant="success" className="brutal-badge">OK</Badge>}
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">{formatDate(item.updated_at)}</TableCell>
                        </TableRow>
                      );
                    })}
                    {filteredInventory.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                          No inventory items found.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
            <div className="mt-4">
              <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
            </div>
          </>
        )
      )}

      {/* TAB: BATCHES */}
      {activeTab === 'batches' && (
        <>
          {/* Stats row */}
          <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-5">
            {[
              { label: 'Total Batches', value: batchStats.total, color: 'text-foreground' },
              { label: 'In Stock', value: batchStats.in_stock, color: 'text-green-600' },
              { label: 'Low Stock (<20%)', value: batchStats.low, color: 'text-amber-600' },
              { label: 'Depleted', value: batchStats.depleted, color: 'text-destructive' },
              { label: 'Pending Transfer', value: batchStats.pending, color: 'text-purple-600' },
            ].map(stat => (
              <Card key={stat.label} className="p-3">
                <div className="text-xs text-muted-foreground font-medium">{stat.label}</div>
                <div className={`text-2xl font-black ${stat.color}`}>{stat.value}</div>
              </Card>
            ))}
          </div>

          {batchesLoading ? (
            <div className="flex h-32 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="space-y-3">
              {filteredBatches.map(batch => {
                const pct = batch.pct_remaining;
                return (
                  <Card key={batch.id} className="overflow-hidden">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-4">
                        {/* Left: info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <span className="font-black text-base">{batch.material_name}</span>
                            <span className={`text-[10px] font-bold px-1.5 py-0.5 border rounded ${STATUS_STYLES[batch.status] || ''}`}>
                              {batch.status.replace(/_/g, ' ')}
                            </span>
                            {pct < 20 && pct > 0 && (
                              <span className="text-[10px] font-bold px-1.5 py-0.5 border rounded bg-red-100 text-red-800 border-red-300 flex items-center gap-1">
                                <AlertTriangle className="h-3 w-3" /> LOW
                              </span>
                            )}
                          </div>
                          <p className="text-xs font-mono text-muted-foreground mb-2">{batch.batch_code}</p>

                          {/* Progress bar */}
                          <div className="mb-2">
                            <div className="h-2 bg-muted border border-border rounded-sm overflow-hidden">
                              <div
                                className={`h-full transition-all ${pct < 20 ? 'bg-destructive' : pct < 50 ? 'bg-amber-500' : 'bg-green-500'}`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <div className="flex justify-between text-xs text-muted-foreground mt-0.5">
                              <span>{batch.current_qty} {batch.unit} remaining</span>
                              <span>{pct}% of {batch.original_qty}</span>
                            </div>
                          </div>

                          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                            <span>📍 {batch.site_name}</span>
                            {batch.received_at && <span>📅 {new Date(batch.received_at).toLocaleDateString()}</span>}
                          </div>
                        </div>

                        {/* Right: actions */}
                        <div className="flex flex-col gap-1.5 shrink-0">
                          <Button
                            size="sm"
                            variant="outline"
                            className="gap-1.5 text-xs"
                            onClick={() => setSelectedBatchForQR(batch)}
                          >
                            <QrCode className="h-3.5 w-3.5" /> QR Label
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="gap-1.5 text-xs"
                            onClick={() => {
                              setShowQRScanner(true);
                            }}
                          >
                            <Package className="h-3.5 w-3.5" /> Take Action
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
              {filteredBatches.length === 0 && (
                <div className="border-2 border-dashed border-border rounded-lg p-12 text-center">
                  <Package className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
                  <p className="font-bold text-muted-foreground">No batches found</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Create batches via the QR scanner or API
                  </p>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* TAB: DISCREPANCIES */}
      {activeTab === 'discrepancies' && (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Batch</TableHead>
                  <TableHead>Material</TableHead>
                  <TableHead>Site</TableHead>
                  <TableHead>Expected</TableHead>
                  <TableHead>Actual</TableHead>
                  <TableHead>Difference</TableHead>
                  <TableHead>Reported By</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {discrepancies.map(d => (
                  <TableRow key={d.id}>
                    <TableCell className="font-mono text-xs">{d.batch_code}</TableCell>
                    <TableCell className="font-bold">{d.material_name}</TableCell>
                    <TableCell className="text-muted-foreground">{d.site_name}</TableCell>
                    <TableCell>{d.expected_qty}</TableCell>
                    <TableCell>{d.actual_qty}</TableCell>
                    <TableCell>
                      <span className={`font-bold ${d.difference < 0 ? 'text-destructive' : 'text-green-600'}`}>
                        {d.difference > 0 ? '+' : ''}{d.difference}
                      </span>
                    </TableCell>
                    <TableCell className="text-xs">{d.reported_by}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {d.created_at ? new Date(d.created_at).toLocaleDateString() : '—'}
                    </TableCell>
                  </TableRow>
                ))}
                {discrepancies.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                      <CheckCircle className="h-6 w-6 mx-auto mb-2 text-green-500" />
                      No delivery discrepancies recorded.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Modals */}
      <QRCodeGenerator
        open={!!selectedBatchForQR}
        onClose={() => setSelectedBatchForQR(null)}
        batch={selectedBatchForQR}
      />
      <QRScannerModal
        open={showQRScanner}
        onClose={() => { setShowQRScanner(false); setScannerInitialCode(''); }}
        onActionComplete={() => {
          loadInventory();
          if (activeTab === 'batches') loadBatches();
        }}
        sites={sites}
        initialCode={scannerInitialCode}
      />
    </div>
  );
}
