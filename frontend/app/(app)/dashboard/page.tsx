'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Building2, Package, Wrench, Wallet, AlertTriangle,
  ArrowRight, Clock, Users,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { useAuth } from '@/providers/auth-provider';
import { apiFetch } from '@/lib/api';
import { formatCurrency, formatDate, ROLE_LABELS } from '@/lib/types';

export default function DashboardPage() {
  const { user, role } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await apiFetch<any>('/api/v1/dashboard/summary');
        setData(result);
      } catch (loadError: any) {
        console.error('Failed to load dashboard', loadError);
        setError(loadError?.message || 'Unable to load dashboard data');
      } finally {
        setLoading(false);
      }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  if (!user || loading) return <div className="p-8">Loading dashboard...</div>;

  if (error || !data) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 p-8 text-center">
        <p className="font-bold">Dashboard data could not be loaded.</p>
        <p className="text-sm text-muted-foreground">{error || 'The dashboard returned no data.'}</p>
        <Button variant="outline" onClick={loadDashboard}>Retry</Button>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={`Welcome, ${(user.name || 'User').split(' ')[0]}`}
        description={`You're signed in as ${role ? ROLE_LABELS[role as keyof typeof ROLE_LABELS] : ''}. Here's what's happening across your sites.`}
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Active Sites</CardTitle>
            <Building2 className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-3xl font-extrabold">{data.active_sites}</div>
            <p className="mt-1 text-xs text-muted-foreground font-medium">{data.total_sites} total sites</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Open Alerts</CardTitle>
            <AlertTriangle className="h-5 w-5 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-3xl font-extrabold">{data.open_alerts}</div>
            <p className="mt-1 text-xs text-muted-foreground font-medium">{data.critical_alerts} critical</p>
          </CardContent>
        </Card>

        {(role === 'pm' || role === 'admin') && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-semibold text-muted-foreground">Pending Approvals</CardTitle>
              <Clock className="h-5 w-5 text-mahogany" />
            </CardHeader>
            <CardContent>
              <div className="font-display text-3xl font-extrabold">{data.pending_requests}</div>
              <p className="mt-1 text-xs text-muted-foreground font-medium">Material requests</p>
            </CardContent>
          </Card>
        )}

        {(role === 'finance' || role === 'admin') && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-semibold text-muted-foreground">Pending POs</CardTitle>
              <Wallet className="h-5 w-5 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="font-display text-3xl font-extrabold">{data.pending_pos}</div>
              <p className="mt-1 text-xs text-muted-foreground font-medium">{formatCurrency(data.pending_po_amount)}</p>
            </CardContent>
          </Card>
        )}

        {role === 'contractor' && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-semibold text-muted-foreground">My Requests</CardTitle>
              <Clock className="h-5 w-5 text-mahogany" />
            </CardHeader>
            <CardContent>
              <div className="font-display text-3xl font-extrabold">{data.pending_requests}</div>
              <p className="mt-1 text-xs text-muted-foreground font-medium">Submitted by you</p>
            </CardContent>
          </Card>
        )}

        {(role === 'pm' || role === 'admin') && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-semibold text-muted-foreground">Low Stock Items</CardTitle>
              <Package className="h-5 w-5 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="font-display text-3xl font-extrabold">{data.low_stock_items}</div>
              <p className="mt-1 text-xs text-muted-foreground font-medium">Below reorder level</p>
            </CardContent>
          </Card>
        )}

        {role === 'admin' && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-semibold text-muted-foreground">Total Users</CardTitle>
              <Users className="h-5 w-5 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="font-display text-3xl font-extrabold">{data.active_users}</div>
              <p className="mt-1 text-xs text-muted-foreground font-medium">{data.total_users} total registered</p>
            </CardContent>
          </Card>
        )}
      </div>


      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Alerts</CardTitle>
            <Link href="/alerts">
              <Button variant="outline" size="sm" className="gap-1">
                View All <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.recent_alerts?.slice(0, 5).map((alert: any) => (
              <div key={alert.id} className="flex items-start gap-3 border-2 border-border bg-secondary px-3 py-2.5">
                <div className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center border-2 border-border ${
                  alert.severity === 'critical' ? 'bg-destructive text-destructive-foreground' :
                  alert.severity === 'warning' ? 'bg-soft-sand text-dark-espresso' :
                  'bg-blue-500 text-white'
                }`}>
                  <AlertTriangle className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-bold text-sm truncate">{alert.title}</p>
                    <StatusBadge status={alert.severity} />
                  </div>
                  <p className="text-xs text-muted-foreground font-medium mt-0.5 truncate">{alert.site_name}</p>
                </div>
              </div>
            ))}
            {(!data.recent_alerts || data.recent_alerts.length === 0) && (
              <p className="text-sm text-muted-foreground font-medium text-center py-4">No open alerts. All clear!</p>
            )}
          </CardContent>
        </Card>

        {(role === 'finance' || role === 'pm' || role === 'admin') && (
          <Card>
            <CardHeader>
              <CardTitle>Budget Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="border-2 border-border bg-secondary px-3 py-2.5">
                <div className="text-xs font-semibold text-muted-foreground">Total budget</div>
                <div className="font-display text-xl font-extrabold">{formatCurrency(data.total_budget)}</div>
              </div>
              <div className="border-2 border-border bg-secondary px-3 py-2.5">
                <div className="text-xs font-semibold text-muted-foreground">Total spend</div>
                <div className="font-display text-xl font-extrabold text-primary">{formatCurrency(data.total_spend)}</div>
              </div>
              <div className="border-2 border-border bg-secondary px-3 py-2.5">
                <div className="text-xs font-semibold text-muted-foreground">Scheduled payments</div>
                <div className="font-display text-xl font-extrabold">{formatCurrency(data.scheduled_payments)}</div>
              </div>
              <Link href="/finance">
                <Button variant="outline" className="w-full gap-1">
                  Finance Details <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}

        {(role === 'pm' || role === 'admin') && data.pending_requests_list?.length > 0 && (
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Pending Material Requests</CardTitle>
              <Link href="/procurement/requests">
                <Button variant="outline" size="sm" className="gap-1">
                  Review All <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-2">
              {data.pending_requests_list.slice(0, 4).map((req: any) => (
                <Link key={req.id} href="/procurement/requests">
                  <div className="flex items-center justify-between border-2 border-border bg-secondary px-3 py-2.5 hover:bg-accent transition-colors">
                    <div>
                      <p className="font-bold text-sm">{req.material_name}</p>
                      <p className="text-xs text-muted-foreground font-medium">{req.quantity} {req.unit} - {req.site_name}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-muted-foreground">{formatDate(req.created_at)}</span>
                      <StatusBadge status={req.pm_status} />
                    </div>
                  </div>
                </Link>
              ))}
            </CardContent>
          </Card>
        )}

        {(role === 'finance' || role === 'admin') && data.pending_pos_list?.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Pending PO Approvals</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {data.pending_pos_list.slice(0, 3).map((po: any) => (
                <Link key={po.id} href="/finance/purchase-orders">
                  <div className="border-2 border-border bg-secondary px-3 py-2.5 hover:bg-accent transition-colors">
                    <p className="font-bold text-sm">{po.vendor_name}</p>
                    <p className="text-xs text-muted-foreground font-medium">{po.material_name}</p>
                    <p className="text-sm font-extrabold text-primary mt-1">{formatCurrency(po.amount)}</p>
                  </div>
                </Link>
              ))}
            </CardContent>
          </Card>
        )}

        {(role === 'pm' || role === 'admin') && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Equipment Status</CardTitle>
              <Link href="/equipment">
                <Button variant="outline" size="sm" className="gap-1">
                  View All <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="grid grid-cols-3 gap-2">
                <div className="border-2 border-border bg-green-100 dark:bg-green-900 px-2 py-2 text-center">
                  <div className="font-display text-xl font-extrabold text-green-800 dark:text-green-200">{data.equipment_status?.active || 0}</div>
                  <div className="text-[10px] font-semibold text-muted-foreground">Active</div>
                </div>
                <div className="border-2 border-border bg-gray-100 dark:bg-gray-800 px-2 py-2 text-center">
                  <div className="font-display text-xl font-extrabold">{data.equipment_status?.idle || 0}</div>
                  <div className="text-[10px] font-semibold text-muted-foreground">Idle</div>
                </div>
                <div className="border-2 border-border bg-soft-sand/30 dark:bg-soft-sand/10 px-2 py-2 text-center">
                  <div className="font-display text-xl font-extrabold text-dark-espresso dark:text-soft-sand">{data.equipment_status?.maintenance || 0}</div>
                  <div className="text-[10px] font-semibold text-muted-foreground">Maint.</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
