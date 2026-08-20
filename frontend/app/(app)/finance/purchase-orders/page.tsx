'use client';

import { FileText, Check, X, Package } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { purchaseOrders, materialRequests, payments } from '@/lib/mock-data';
import { formatCurrency, formatDate } from '@/lib/types';

export default function PurchaseOrdersPage() {
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
              {purchaseOrders.map((po) => {
                const req = materialRequests.find((mr) => mr.id === po.material_request_id);
                const poPayments = payments.filter((p) => p.purchase_order_id === po.id);
                return (
                  <TableRow key={po.id}>
                    <TableCell className="font-mono text-xs font-bold">PO-{po.id.slice(-6).toUpperCase()}</TableCell>
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
                            <Button size="sm" className="gap-1 h-7 px-2"><Check className="h-3 w-3" /> Approve</Button>
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
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
