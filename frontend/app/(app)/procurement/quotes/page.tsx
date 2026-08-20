'use client';

import { FileText, Check, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { vendorQuotes, materialRequests, vendors, purchaseOrders } from '@/lib/mock-data';
import { formatCurrency, formatDate } from '@/lib/types';

export default function VendorQuotesPage() {
  return (
    <div>
      <PageHeader
        title="Vendor Quotes"
        description="Compare and select vendor quotes for approved material requests"
      />

      {/* Vendors list */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Registered Vendors</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Vendor</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Email</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {vendors.map((v) => (
                <TableRow key={v.id}>
                  <TableCell className="font-bold">{v.name}</TableCell>
                  <TableCell><Badge variant="outline" className="brutal-badge">{v.category}</Badge></TableCell>
                  <TableCell className="text-sm">{v.contact_phone}</TableCell>
                  <TableCell className="text-sm">{v.contact_email}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Quote comparison */}
      <div className="space-y-4">
        <h2 className="font-display text-xl font-extrabold">Quote Comparisons</h2>
        {materialRequests.filter((mr) => mr.pm_status === 'approved').map((req) => {
          const quotes = vendorQuotes.filter((vq) => vq.material_request_id === req.id);
          const pos = purchaseOrders.filter((po) => po.material_request_id === req.id);
          if (quotes.length === 0) return null;

          return (
            <Card key={req.id}>
              <CardHeader>
                <CardTitle className="text-lg">{req.material_name} - {req.quantity} {req.unit}</CardTitle>
                <p className="text-sm text-muted-foreground font-medium">{req.site_name} - Requested by {req.requested_by_name}</p>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                  {quotes.map((q) => {
                    const vendor = vendors.find((v) => v.id === q.vendor_id);
                    const po = pos.find((p) => p.vendor_quote_id === q.id);
                    return (
                      <div key={q.id} className={`border-2 border-border p-3 ${q.is_selected ? 'bg-primary/10 border-primary shadow-brutal-sm' : 'bg-secondary'}`}>
                        <div className="flex items-center justify-between mb-2">
                          <p className="font-bold text-sm">{vendor?.name}</p>
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
                        {po && (
                          <div className="mt-3 border-t-2 border-border pt-2">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold uppercase text-muted-foreground">PO Status</span>
                              <StatusBadge status={po.status} />
                            </div>
                          </div>
                        )}
                        {!q.is_selected && !po && (
                          <Button size="sm" className="w-full mt-2 gap-1">
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
      </div>
    </div>
  );
}
