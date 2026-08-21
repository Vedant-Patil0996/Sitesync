'use client';

import * as React from 'react';
import { FileText, Check, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { apiFetch } from '@/lib/api';
import { formatCurrency, formatDate } from '@/lib/types';
import { Pagination } from '@/components/shared/pagination';

export default function VendorQuotesPage() {
  const [requests, setRequests] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [page, setPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const [refreshKey, setRefreshKey] = React.useState(0);
  const limit = 10;

  const selectAndCreatePo = async (requestId: number, quoteId: number) => {
    try {
      await apiFetch(`/api/v1/procurement/quotes/${quoteId}/select`, { method: 'PATCH' });
      await apiFetch('/api/v1/procurement/purchase-orders', {
        method: 'POST',
        body: JSON.stringify({ request_id: requestId, quote_id: quoteId }),
      });
      setRefreshKey((value) => value + 1);
    } catch (error) {
      console.error('Failed to select quote and create purchase order', error);
    }
  };

  React.useEffect(() => {
    async function loadRequests() {
      setLoading(true);
      try {
        const skip = (page - 1) * limit;
        const result = await apiFetch<any>(`/api/v1/procurement/requests?skip=${skip}&limit=${limit}`);
        setRequests(result.items);
        setTotalPages(result.pages);
      } catch (error) {
        console.error('Failed to load material requests', error);
      } finally {
        setLoading(false);
      }
    }
    loadRequests();
  }, [page, refreshKey]);

  return (
    <div>
      <PageHeader
        title="Vendor Quotes"
        description="Compare and select vendor quotes for approved material requests"
      />

      {loading ? (
        <div className="p-8">Loading vendor quotes...</div>
      ) : (
        <>
          {/* Quote comparison */}
          <div className="space-y-4">
            <h2 className="font-display text-xl font-extrabold">Quote Comparisons</h2>
            {requests.filter((mr) => mr.pm_status === 'approved' && mr.finance_status === 'approved').map((req) => {
              const quotes = req.quotes || [];
              if (quotes.length === 0) return null;

              return (
                <Card key={req.id}>
                  <CardHeader>
                    <CardTitle className="text-lg">{req.material_name} - {req.quantity} {req.unit}</CardTitle>
                    <p className="text-sm text-muted-foreground font-medium">{req.site_name} - Requested by {req.requested_by_name}</p>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                      {quotes.map((q: any) => {
                        return (
                          <div key={q.id} className={`border-2 border-border p-3 ${q.is_selected ? 'bg-primary/10 border-primary shadow-brutal-sm' : 'bg-secondary'}`}>
                            <div className="flex items-center justify-between mb-2">
                              <p className="font-bold text-sm">{q.vendor_name}</p>
                              {q.is_selected && <Badge variant="default" className="brutal-badge text-[10px]">SELECTED</Badge>}
                            </div>
                            <div className="space-y-1">
                              <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Unit Price:</span>
                                <span className="font-bold">{formatCurrency(q.unit_price)}</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Total:</span>
                                <span className="font-display text-lg font-extrabold text-primary">{formatCurrency(q.total_price)}</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Delivery:</span>
                                <span className="font-bold">{q.delivery_days} days</span>
                              </div>
                            </div>
                            {req.po_status && q.is_selected && (
                              <div className="mt-3 border-t-2 border-border pt-2">
                                <div className="flex items-center justify-between">
                                  <span className="text-xs font-bold uppercase text-muted-foreground">PO Status</span>
                                  <StatusBadge status={req.po_status} />
                                </div>
                              </div>
                            )}
                            {!q.is_selected && !req.po_status && req.finance_status === 'approved' && (
                              <Button size="sm" className="w-full mt-2 gap-1" onClick={() => selectAndCreatePo(req.id, q.id)}>
                                <Check className="h-3 w-3" /> Select & Create PO
                              </Button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
            {requests.filter((mr) => mr.pm_status === 'approved' && mr.finance_status === 'approved' && mr.quotes?.length > 0).length === 0 && (
              <div className="p-8 text-center text-muted-foreground">No approved requests with quotes found.</div>
            )}
          </div>

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
