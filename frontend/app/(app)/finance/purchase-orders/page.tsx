'use client';

import { useState, useEffect } from 'react';
import { FileText, Check, X, Package, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { Pagination } from '@/components/shared/pagination';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { formatCurrency, formatDate } from '@/lib/types';
import { apiFetch } from '@/lib/api';
import { toast } from 'sonner';

export default function PurchaseOrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const itemsPerPage = 10;

  const loadData = async (page: number) => {
    setLoading(true);
    try {
      const skip = (page - 1) * itemsPerPage;
      const data = await apiFetch<any>(`/api/v1/finance/purchase-orders?skip=${skip}&limit=${itemsPerPage}`);
      setOrders(data.items);
      setTotalPages(data.pages);
      setCurrentPage(data.page);
    } catch (error) {
      console.error('Failed to load purchase orders:', error);
      toast.error('Failed to load purchase orders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(1);
  }, []);

  const handleApprove = async (id: number) => {
    try {
      await apiFetch(`/api/v1/finance/purchase-orders/${id}/approve`, { method: 'PATCH' });
      toast.success('Purchase order approved');
      loadData(currentPage);
    } catch (error) {
      toast.error('Failed to approve purchase order');
    }
  };

  if (loading && orders.length === 0) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Purchase Orders" description="Review, approve, and track purchase orders" />

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>PO ID</TableHead>
                <TableHead>Vendor</TableHead>
                <TableHead>Material</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Approved By</TableHead>
                <TableHead>Delivered</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-primary mx-auto" />
                  </TableCell>
                </TableRow>
              ) : orders.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                    No purchase orders found.
                  </TableCell>
                </TableRow>
              ) : (
                orders.map((po) => {
                  const poPayments = po.payments || [];
                  return (
                    <TableRow key={po.id}>
                      <TableCell className="font-mono text-xs font-bold">PO-{po.id.toString().padStart(6, '0')}</TableCell>
                      <TableCell className="font-bold">{po.vendor_name}</TableCell>
                      <TableCell className="text-sm">{po.material_name}</TableCell>
                      <TableCell className="font-extrabold text-primary">{formatCurrency(po.amount)}</TableCell>
                      <TableCell><StatusBadge status={po.status} /></TableCell>
                      <TableCell className="text-sm">{po.approved_by_name ?? <span className="text-muted-foreground">Pending</span>}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{po.delivered_at ? formatDate(po.delivered_at) : '-'}</TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {po.status === 'pending_finance' && (
                            <>
                              <Button size="sm" className="gap-1 h-7 px-2" onClick={() => handleApprove(po.id)}>
                                <Check className="h-3 w-3" /> Approve
                              </Button>
                              <Button size="sm" variant="destructive" className="gap-1 h-7 px-2"><X className="h-3 w-3" /></Button>
                            </>
                          )}
                          {po.status === 'approved' && (
                            <Button size="sm" variant="outline" className="gap-1 h-7 px-2"><Package className="h-3 w-3" /> Mark Delivered</Button>
                          )}
                          {po.status === 'delivered' && poPayments.length === 0 && (
                            <Button size="sm" className="gap-1 h-7 px-2"><FileText className="h-3 w-3" /> Release Payment</Button>
                          )}
                          {po.status === 'delivered' && poPayments.length > 0 && poPayments[0].status === 'released' && (
                            <Badge variant="success" className="brutal-badge text-[10px]">PAID</Badge>
                          )}
                          {po.status === 'rejected' && (
                            <Badge variant="destructive" className="brutal-badge text-[10px]">REJECTED</Badge>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
          
          {!loading && totalPages > 1 && (
            <div className="p-4 border-t-2 border-border flex justify-end bg-accent/20">
              <Pagination 
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={loadData}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
