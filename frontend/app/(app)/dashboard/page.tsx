'use client';

import Link from 'next/link';
import {
  Building2, Package, Wrench, Wallet, AlertTriangle,
  ArrowRight, Clock, Users,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { useRole } from '@/components/providers/role-provider';
import {
  sites, projects, alerts, materialRequests, purchaseOrders,
  payments, inventory, equipment, users,
} from '@/lib/mock-data';
import { formatCurrency, formatDate, ROLE_LABELS } from '@/lib/types';

export default function DashboardPage() {
  const { user, role } = useRole();

  const activeSites = sites.filter((s) => s.status === 'active');
  const openAlerts = alerts.filter((a) => a.status === 'open');
  const criticalAlerts = openAlerts.filter((a) => a.severity === 'critical');
  const pendingRequests = materialRequests.filter((mr) => mr.pm_status === 'pending');
  const pendingPOs = purchaseOrders.filter((po) => po.status === 'pending_finance');
  const scheduledPayments = payments.filter((p) => p.status === 'scheduled');
  const lowStockItems = inventory.filter((i) => i.current_stock <= i.reorder_level);
  const totalBudget = projects.reduce((sum, p) => sum + p.budget_total, 0);
  const totalSpend = purchaseOrders
    .filter((po) => po.status === 'delivered' || po.status === 'approved')
    .reduce((sum, po) => sum + po.amount, 0);

  return (
    <div>
      <PageHeader
        title={`Welcome, ${user.full_name.split(' ')[0]}`}
        description={`You're signed in as ${ROLE_LABELS[role]}. Here's what's happening across your sites.`}
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Active Sites</CardTitle>
            <Building2 className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-3xl font-extrabold">{activeSites.length}</div>
            <p className="mt-1 text-xs text-muted-foreground font-medium">{sites.length} total sites</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Open Alerts</CardTitle>
            <AlertTriangle className="h-5 w-5 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-3xl font-extrabold">{openAlerts.length}</div>
            <p className="mt-1 text-xs text-muted-foreground font-medium">{criticalAlerts.length} critical</p>
          </CardContent>
        </Card>

        {(role === 'pm' || role === 'admin') && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-semibold text-muted-foreground">Pending Approvals</CardTitle>
              <Clock className="h-5 w-5 text-mahogany" />
            </CardHeader>
            <CardContent>
              <div className="font-display text-3xl font-extrabold">{pendingRequests.length}</div>
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
              <div className="font-display text-3xl font-extrabold">{pendingPOs.length}</div>
              <p className="mt-1 text-xs text-muted-foreground font-medium">{formatCurrency(pendingPOs.reduce((s, po) => s + po.amount, 0))}</p>
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
              <div className="font-display text-3xl font-extrabold">{materialRequests.length}</div>
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
              <div className="font-display text-3xl font-extrabold">{lowStockItems.length}</div>
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
              <div className="font-display text-3xl font-extrabold">{users.filter((u) => u.is_active).length}</div>
              <p className="mt-1 text-xs text-muted-foreground font-medium">{users.length} total registered</p>
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
            {openAlerts.slice(0, 5).map((alert) => (
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
            {openAlerts.length === 0 && (
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
                <div className="font-display text-xl font-extrabold">{formatCurrency(totalBudget)}</div>
              </div>
              <div className="border-2 border-border bg-secondary px-3 py-2.5">
                <div className="text-xs font-semibold text-muted-foreground">Total spend</div>
                <div className="font-display text-xl font-extrabold text-primary">{formatCurrency(totalSpend)}</div>
              </div>
              <div className="border-2 border-border bg-secondary px-3 py-2.5">
                <div className="text-xs font-semibold text-muted-foreground">Scheduled payments</div>
                <div className="font-display text-xl font-extrabold">{formatCurrency(scheduledPayments.reduce((s, p) => s + p.amount, 0))}</div>
              </div>
              <Link href="/finance">
                <Button variant="outline" className="w-full gap-1">
                  Finance Details <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}

        {(role === 'pm' || role === 'admin') && pendingRequests.length > 0 && (
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
              {pendingRequests.slice(0, 4).map((req) => (
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

        {(role === 'finance' || role === 'admin') && pendingPOs.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Pending PO Approvals</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {pendingPOs.slice(0, 3).map((po) => (
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
                  <div className="font-display text-xl font-extrabold text-green-800 dark:text-green-200">{equipment.filter((e) => e.status === 'active').length}</div>
                  <div className="text-[10px] font-semibold text-muted-foreground">Active</div>
                </div>
                <div className="border-2 border-border bg-gray-100 dark:bg-gray-800 px-2 py-2 text-center">
                  <div className="font-display text-xl font-extrabold">{equipment.filter((e) => e.status === 'idle').length}</div>
                  <div className="text-[10px] font-semibold text-muted-foreground">Idle</div>
                </div>
                <div className="border-2 border-border bg-soft-sand/30 dark:bg-soft-sand/10 px-2 py-2 text-center">
                  <div className="font-display text-xl font-extrabold text-dark-espresso dark:text-soft-sand">{equipment.filter((e) => e.status === 'maintenance').length}</div>
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
