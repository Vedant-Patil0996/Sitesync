'use client';

import { Wallet, Check, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { payments, purchaseOrders } from '@/lib/mock-data';
import { formatCurrency, formatDate } from '@/lib/types';

export default function PaymentsPage() {
  const totalScheduled = payments.filter((p) => p.status === 'scheduled').reduce((s, p) => s + p.amount, 0);
  const totalReleased = payments.filter((p) => p.status === 'released').reduce((s, p) => s + p.amount, 0);

  return (
    <div>
      <PageHeader title="Payments" description="Schedule and release payments to vendors" />

      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-muted-foreground">Scheduled</div>
              <div className="font-display text-2xl font-extrabold text-crimson">{formatCurrency(totalScheduled)}</div>
            </div>
            <div className="flex h-10 w-10 items-center justify-center border-2 border-border bg-soft-sand shadow-brutal-sm">
              <Clock className="h-5 w-5 text-dark-espresso" />
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-muted-foreground">Released</div>
              <div className="font-display text-2xl font-extrabold text-green-600">{formatCurrency(totalReleased)}</div>
            </div>
            <div className="flex h-10 w-10 items-center justify-center border-2 border-border bg-green-500 shadow-brutal-sm">
              <Check className="h-5 w-5 text-white" />
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Wallet className="h-5 w-5" /> Payment Records</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Payment ID</TableHead>
                <TableHead>Vendor</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Released By</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {payments.map((pay) => {
                const po = purchaseOrders.find((p) => p.id === pay.purchase_order_id);
                return (
                  <TableRow key={pay.id}>
                    <TableCell className="font-mono text-xs font-bold">PAY-{pay.id.slice(-6).toUpperCase()}</TableCell>
                    <TableCell className="font-bold">{pay.po_vendor_name}</TableCell>
                    <TableCell className="font-extrabold text-primary">{formatCurrency(pay.amount)}</TableCell>
                    <TableCell><StatusBadge status={pay.status} /></TableCell>
                    <TableCell className="text-sm">{pay.released_by_name ?? <span className="text-muted-foreground">Pending</span>}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{pay.released_at ? formatDate(pay.released_at) : formatDate(pay.created_at)}</TableCell>
                    <TableCell>
                      {pay.status === 'scheduled' && (
                        <Button size="sm" className="gap-1 h-7 px-2"><Check className="h-3 w-3" /> Release</Button>
                      )}
                      {pay.status === 'released' && (
                        <Badge variant="success" className="brutal-badge text-[10px]">RELEASED</Badge>
                      )}
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
