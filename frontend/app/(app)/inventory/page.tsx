'use client';

import * as React from 'react';
import { Package, Plus, ArrowRightLeft, Search } from 'lucide-react';
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
import { apiFetch } from '@/lib/api';
import { formatDate } from '@/lib/types';
import { Pagination } from '@/components/shared/pagination';
import { toast } from 'sonner';

export default function InventoryPage() {
  const [search, setSearch] = React.useState('');
  const [siteFilter, setSiteFilter] = React.useState('all');
  const [showTxForm, setShowTxForm] = React.useState(false);

  const [inventory, setInventory] = React.useState<any[]>([]);
  const [sites, setSites] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [page, setPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const limit = 10;

  const [txType, setTxType] = React.useState('stock_in');
  const [txInventoryId, setTxInventoryId] = React.useState('');
  const [txQuantity, setTxQuantity] = React.useState('');
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const loadData = React.useCallback(async () => {
    setLoading(true);
    try {
      const skip = (page - 1) * limit;
      const [invRes, sitesRes] = await Promise.all([
        apiFetch<any>(`/api/v1/inventory?skip=${skip}&limit=${limit}`),
        apiFetch<any>(`/api/v1/sites?skip=0&limit=100`) // Assuming up to 100 sites
      ]);
      setInventory(invRes.items);
      setTotalPages(invRes.pages);
      setSites(sitesRes.items);
    } catch (error) {
      console.error('Failed to load inventory data', error);
      toast.error('Failed to load inventory data');
    } finally {
      setLoading(false);
    }
  }, [page]);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSaveTransaction = async () => {
    if (!txInventoryId || !txQuantity) {
      toast.error('Please select a material and enter quantity');
      return;
    }
    
    const selectedInv = inventory.find(i => String(i.id) === txInventoryId);
    if (!selectedInv) {
      toast.error('Invalid material selection');
      return;
    }

    setIsSubmitting(true);
    try {
      await apiFetch('/api/v1/inventory/transactions', {
        method: 'POST',
        body: JSON.stringify({
          site_id: selectedInv.site_id,
          material_id: selectedInv.material_id,
          type: txType,
          quantity: parseFloat(txQuantity),
          reference: ''
        }),
      });
      toast.success('Transaction saved successfully');
      setShowTxForm(false);
      setTxInventoryId('');
      setTxQuantity('');
      loadData();
    } catch (error: any) {
      toast.error(error.message || 'Failed to save transaction');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filtered = inventory.filter((item) => {
    const matchesSearch = item.material_name.toLowerCase().includes(search.toLowerCase());
    const matchesSite = siteFilter === 'all' || String(item.site_id) === siteFilter;
    return matchesSearch && matchesSite;
  });

  return (
    <div>
      <PageHeader
        title="Inventory"
        description="Track stock levels across all sites"
        action={
          <Button className="gap-2" onClick={() => setShowTxForm(!showTxForm)}>
            <Plus className="h-4 w-4" /> Log Transaction
          </Button>
        }
      />

      {showTxForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Log Stock Transaction</CardTitle>
          </CardHeader>
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
                    {inventory.map((item) => (
                      <SelectItem key={item.id} value={String(item.id)}>
                        {item.material_name} ({item.site_name})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-bold">Quantity</label>
                <Input type="number" placeholder="0" value={txQuantity} onChange={(e) => setTxQuantity(e.target.value)} />
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <Button onClick={handleSaveTransaction} disabled={isSubmitting}>
                {isSubmitting ? 'Saving...' : 'Save Transaction'}
              </Button>
              <Button variant="outline" onClick={() => setShowTxForm(false)} disabled={isSubmitting}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search materials..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={siteFilter} onValueChange={setSiteFilter}>
          <SelectTrigger className="w-full sm:w-[200px]">
            <SelectValue placeholder="Filter by site" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Sites</SelectItem>
            {sites.map((site) => (
              <SelectItem key={site.id} value={String(site.id)}>{site.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="p-8">Loading inventory...</div>
      ) : (
        <>
          {/* Inventory table */}
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
                  {filtered.map((item) => {
                    const isLow = item.quantity <= item.reorder_level;
                    return (
                      <TableRow key={item.id}>
                        <TableCell className="font-bold">{item.material_name}</TableCell>
                        <TableCell className="text-muted-foreground">{item.site_name}</TableCell>
                        <TableCell className="font-extrabold">{item.quantity} {item.unit}</TableCell>
                        <TableCell>{item.reorder_level} {item.unit}</TableCell>
                        <TableCell>
                          {isLow ? (
                            <Badge variant="destructive" className="brutal-badge">LOW STOCK</Badge>
                          ) : (
                            <Badge variant="success" className="brutal-badge">OK</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">{formatDate(item.updated_at)}</TableCell>
                      </TableRow>
                    );
                  })}
                  {filtered.length === 0 && (
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
             <Pagination
               currentPage={page}
               totalPages={totalPages}
               onPageChange={setPage}
             />
          </div>
        </>
      )}
    </div>
  );
}
