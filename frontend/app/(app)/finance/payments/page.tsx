'use client';

import { useState, useEffect } from 'react';
import { Wallet, Check, Clock, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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

export default function PaymentsPage() {
  const [payments, setPayments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [summary, setSummary] = useState<any>(null);
  const itemsPerPage = 10;

  const loadData = async (page: number) => {
    setLoading(true);
    try {
      const skip = (page - 1) * itemsPerPage;
      const [paymentsData, summaryData] = await Promise.all([
        apiFetch(`/api/v1/finance/payments?skip=${skip}&limit=${itemsPerPage}`),
        apiFetch('/api/v1/finance/summary')
      ]);
      setPayments(paymentsData.items);
      setTotalPages(paymentsData.pages);
      setCurrentPage(paymentsData.page);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to load payments:', error);
      toast.error('Failed to load payments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(1);
  }, []);

  const handleRelease = async (id: number) => {
    try {
      await apiFetch(`/api/v1/finance/payments/${id}/release`, { method: 'PATCH' });
      toast.success('Payment released');
      loadData(currentPage);
    } catch (error) {
      toast.error('Failed to release payment');
    }
  };

  const totalScheduled = summary?.pending_payments || 0;
  // Approximation, since we can't get just total released easily without calculating it in summary
  const totalReleased = (summary?.total_spent || 0) - (summary?.pending_payments || 0);

  if (loading && payments.length === 0) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

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
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-primary mx-auto" />
                  </TableCell>
                </TableRow>
              ) : payments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                    No payments found.
                  </TableCell>
                </TableRow>
              ) : (
                payments.map((pay) => (
                  <TableRow key={pay.id}>
                    <TableCell className="font-mono text-xs font-bold">PAY-{pay.id.toString().padStart(6, '0')}</TableCell>
                    <TableCell className="font-bold">{pay.vendor_name}</TableCell>
                    <TableCell className="font-extrabold text-primary">{formatCurrency(pay.amount)}</TableCell>
                    <TableCell><StatusBadge status={pay.status} /></TableCell>
                    <TableCell className="text-sm">{pay.released_by_name ?? <span className="text-muted-foreground">Pending</span>}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{pay.released_at ? formatDate(pay.released_at) : formatDate(pay.created_at)}</TableCell>
                    <TableCell>
                      {pay.status === 'scheduled' && (
                        <Button size="sm" className="gap-1 h-7 px-2" onClick={() => handleRelease(pay.id)}>
                          <Check className="h-3 w-3" /> Release
                        </Button>
                      )}
                      {pay.status === 'released' && (
                        <Badge variant="success" className="brutal-badge text-[10px]">RELEASED</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))
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
