'use client';

import * as React from 'react';
import { ShoppingCart, Check, X, Clock, FileText, Phone } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { apiFetch } from '@/lib/api';
import { formatDate, formatCurrency } from '@/lib/types';
import { Pagination } from '@/components/shared/pagination';
import { MaterialRequestDialog } from '@/components/procurement/material-request-dialog';

export default function MaterialRequestsPage() {
  const [statusFilter, setStatusFilter] = React.useState('all');

  const [requests, setRequests] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [page, setPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const [refreshKey, setRefreshKey] = React.useState(0);
  const limit = 10;

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

  const reviewRequest = async (requestId: number, type: 'pm' | 'finance', approved: boolean) => {
    try {
      await apiFetch(`/api/v1/procurement/requests/${requestId}/${type}-review`, {
        method: 'PATCH',
        body: JSON.stringify({ approved, reason: approved ? undefined : 'Rejected from SiteSync review' }),
      });
      setRefreshKey((value) => value + 1);
    } catch (error: any) {
      console.error('Failed to review material request', error);
    }
  };

  const filtered = requests.filter((mr) => {
    if (statusFilter === 'all') return true;
    if (statusFilter === 'pending_pm') return mr.pm_status === 'pending';
    if (statusFilter === 'pending_finance') return mr.pm_status === 'approved' && mr.finance_status === 'pending';
    if (statusFilter === 'approved') return mr.pm_status === 'approved' && mr.finance_status === 'approved';
    if (statusFilter === 'rejected') return mr.pm_status === 'rejected' || mr.finance_status === 'rejected';
    return true;
  });

  return (
    <div>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-6">
        <PageHeader
          title="Material Requests"
          description="Two-step approval workflow: PM approves operationally, then Finance approves financially"
        />
        <div className="mt-4 sm:mt-0">
          <MaterialRequestDialog onSuccess={() => { setPage(1); setRefreshKey(r => r + 1); }} />
        </div>
      </div>

      {/* Workflow steps */}
      <div className="mb-6 flex flex-wrap items-center gap-2 text-xs font-bold">
        <div className="flex items-center gap-1 border-2 border-border bg-secondary px-3 py-1.5">
          <span className="flex h-5 w-5 items-center justify-center border border-border bg-primary text-[10px] text-primary-foreground">1</span>
          Contractor Requests
        </div>
        <span className="text-muted-foreground">→</span>
        <div className="flex items-center gap-1 border-2 border-border bg-secondary px-3 py-1.5">
          <span className="flex h-5 w-5 items-center justify-center border border-border bg-primary text-[10px] text-primary-foreground">2</span>
          PM Approves
        </div>
        <span className="text-muted-foreground">→</span>
        <div className="flex items-center gap-1 border-2 border-border bg-secondary px-3 py-1.5">
          <span className="flex h-5 w-5 items-center justify-center border border-border bg-primary text-[10px] text-primary-foreground">3</span>
          Vendor Quotes
        </div>
        <span className="text-muted-foreground">→</span>
        <div className="flex items-center gap-1 border-2 border-border bg-secondary px-3 py-1.5">
          <span className="flex h-5 w-5 items-center justify-center border border-border bg-primary text-[10px] text-primary-foreground">4</span>
          Finance Approves PO
        </div>
        <span className="text-muted-foreground">→</span>
        <div className="flex items-center gap-1 border-2 border-border bg-secondary px-3 py-1.5">
          <span className="flex h-5 w-5 items-center justify-center border border-border bg-primary text-[10px] text-primary-foreground">5</span>
          Payment Released
        </div>
      </div>

      <div className="mb-4">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[250px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Requests</SelectItem>
            <SelectItem value="pending_pm">Pending PM Review</SelectItem>
            <SelectItem value="pending_finance">Pending Finance Review</SelectItem>
            <SelectItem value="approved">Fully Approved</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="p-8">Loading material requests...</div>
      ) : (
        <>
          {/* Requests */}
          <div className="space-y-4">
            {filtered.map((req) => {
              const quotes = req.quotes || [];
              return (
                <Card key={req.id}>
                  <CardHeader>
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <CardTitle className="text-lg">{req.material_name}</CardTitle>
                          <Badge variant={
                            req.priority === 'urgent' ? 'destructive' :
                            req.priority === 'high' ? 'secondary' :
                            'outline'
                          } className="text-[10px] uppercase font-bold">
                            {req.priority || 'normal'} priority
                          </Badge>
                          {req.justification && (req.justification.toLowerCase().includes('voice') || req.justification.toLowerCase().includes('ivr')) && (
                            <Badge className="bg-[#FFEAA7] text-black border-2 border-black font-bold text-[10px] flex items-center gap-1 shadow-[1px_1px_0px_rgba(0,0,0,1)] hover:bg-[#FFEAA7]">
                              <Phone className="h-3 w-3" /> Voice IVR
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground font-medium mt-1">
                          {req.quantity} {req.unit} • {req.site_name} • Requested by <span className="font-bold text-foreground">{req.requested_by_name}</span> on {formatDate(req.created_at)}
                        </p>
                        {req.required_date && (
                          <p className="text-xs text-primary font-bold mt-0.5">
                            Target Delivery: {formatDate(req.required_date)}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-4">
                        {req.total_estimated_cost && (
                          <div className="text-right">
                            <span className="text-[10px] uppercase font-bold text-muted-foreground block">Est. Cost</span>
                            <span className="font-display text-xl font-extrabold text-primary">
                              {formatCurrency(req.total_estimated_cost)}
                            </span>
                          </div>
                        )}
                        <div className="flex gap-2">
                          <div className="flex flex-col items-end gap-1">
                            <span className="text-[10px] font-semibold text-muted-foreground">PM</span>
                            <StatusBadge status={req.pm_status} />
                          </div>
                          <div className="flex flex-col items-end gap-1">
                            <span className="text-[10px] font-semibold text-muted-foreground">Finance</span>
                            <StatusBadge status={req.finance_status} />
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {/* Justification & Attachments */}
                    {(req.justification || req.attachment_url) && (
                      <div className="mb-4 p-3 border-2 border-border bg-secondary/40 text-xs space-y-2">
                        {req.justification && (
                          <p><span className="font-bold">Justification:</span> {req.justification}</p>
                        )}
                        {req.attachment_url && (
                          <div className="flex items-center gap-2">
                            <span className="font-bold">Attachment:</span>
                            <a
                              href={req.attachment_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary font-bold hover:underline underline-offset-2 flex items-center gap-1"
                            >
                              View Spec Document / Image ↗
                            </a>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Timeline */}
                    <div className="mb-4 flex items-center gap-2 text-xs">
                      <div className={`flex items-center gap-1 border-2 border-border px-2 py-1 ${req.pm_status === 'approved' ? 'bg-green-100 dark:bg-green-900' : req.pm_status === 'rejected' ? 'bg-red-100 dark:bg-red-900' : 'bg-soft-sand/40 dark:bg-soft-sand/10'}`}>
                        {req.pm_status === 'approved' ? <Check className="h-3 w-3" /> : req.pm_status === 'rejected' ? <X className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
                        <span className="font-bold">PM: {req.pm_status.replace(/_/g, ' ')}</span>
                        {req.pm_reviewed_by_name && <span className="text-muted-foreground">by {req.pm_reviewed_by_name}</span>}
                      </div>
                      <span className="text-muted-foreground">→</span>
                      <div className={`flex items-center gap-1 border-2 border-border px-2 py-1 ${req.finance_status === 'approved' ? 'bg-green-100 dark:bg-green-900' : req.finance_status === 'rejected' ? 'bg-red-100 dark:bg-red-900' : req.finance_status === 'pending' ? 'bg-soft-sand/40 dark:bg-soft-sand/10' : 'bg-soft-sand/20 dark:bg-soft-sand/10'}`}>
                        {req.finance_status === 'approved' ? <Check className="h-3 w-3" /> : req.finance_status === 'rejected' ? <X className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
                        <span className="font-bold">Finance: {req.finance_status.replace(/_/g, ' ')}</span>
                        {req.finance_reviewed_by_name && <span className="text-muted-foreground">by {req.finance_reviewed_by_name}</span>}
                      </div>
                    </div>

                    {/* Vendor quotes */}
                    {quotes.length > 0 && (
                      <div className="mb-4">
                        <div className="mb-2 flex items-center gap-2 text-sm font-bold">
                          <FileText className="h-4 w-4" /> Vendor Quotes
                        </div>
                        <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
                          {quotes.map((q: any) => (
                            <div key={q.id} className={`border-2 border-border px-3 py-2 ${q.is_selected ? 'bg-primary/10 border-primary' : 'bg-secondary'}`}>
                              <div className="flex items-center justify-between">
                                <p className="font-bold text-sm">{q.vendor_name}</p>
                                {q.is_selected && <Badge variant="default" className="brutal-badge text-[10px]">SELECTED</Badge>}
                              </div>
                              <p className="font-display text-lg font-extrabold mt-1">{formatCurrency(q.total_price)}</p>
                              <p className="text-xs text-muted-foreground font-medium">{formatCurrency(q.unit_price)}/{req.unit} - {q.delivery_days} days delivery</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Action buttons */}
                    <div className="flex flex-wrap gap-2">
                      {req.pm_status === 'pending' && (
                        <>
                          <Button size="sm" className="gap-1" onClick={() => reviewRequest(req.id, 'pm', true)}><Check className="h-3 w-3" /> Approve (PM)</Button>
                          <Button size="sm" variant="destructive" className="gap-1" onClick={() => reviewRequest(req.id, 'pm', false)}><X className="h-3 w-3" /> Reject</Button>
                        </>
                      )}
                      {req.pm_status === 'approved' && req.finance_status === 'pending' && (
                        <>
                          <Button size="sm" className="gap-1" onClick={() => reviewRequest(req.id, 'finance', true)}><Check className="h-3 w-3" /> Approve (Finance)</Button>
                          <Button size="sm" variant="destructive" className="gap-1" onClick={() => reviewRequest(req.id, 'finance', false)}><X className="h-3 w-3" /> Reject</Button>
                        </>
                      )}
                      {req.pm_status === 'approved' && req.finance_status === 'not_applicable' && (
                        <Button size="sm" variant="outline" className="gap-1"><FileText className="h-3 w-3" /> Add Vendor Quotes</Button>
                      )}
                      {req.pm_status === 'approved' && req.finance_status === 'approved' && (
                        <Badge variant="success" className="brutal-badge">Purchase Order Issued</Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
            {filtered.length === 0 && (
              <div className="p-8 text-center text-muted-foreground">No material requests found.</div>
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
