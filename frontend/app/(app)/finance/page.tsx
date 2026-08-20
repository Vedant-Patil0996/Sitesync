'use client';

import { Wallet, TrendingUp, TrendingDown, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { projects, sites, purchaseOrders, payments, alerts, getBudgetVsActual } from '@/lib/mock-data';
import { formatCurrency } from '@/lib/types';

export default function FinanceOverviewPage() {
  const totalBudget = projects.reduce((sum, p) => sum + p.budget_total, 0);
  const totalSpend = purchaseOrders
    .filter((po) => po.status === 'delivered' || po.status === 'approved')
    .reduce((sum, po) => sum + po.amount, 0);
  const pendingPOs = purchaseOrders.filter((po) => po.status === 'pending_finance');
  const scheduledPayments = payments.filter((p) => p.status === 'scheduled');
  const budgetAlerts = alerts.filter((a) => a.type === 'budget' && a.status === 'open');

  return (
    <div>
      <PageHeader title="Finance Overview" description="Budget vs actual spending across all sites" />

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Total Budget</CardTitle>
            <Wallet className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-2xl font-extrabold">{formatCurrency(totalBudget)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Total Spend</CardTitle>
            <TrendingDown className="h-5 w-5 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-2xl font-extrabold text-primary">{formatCurrency(totalSpend)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Pending POs</CardTitle>
            <TrendingUp className="h-5 w-5 text-mahogany" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-2xl font-extrabold">{pendingPOs.length}</div>
            <p className="text-xs text-muted-foreground font-medium">{formatCurrency(pendingPOs.reduce((s, po) => s + po.amount, 0))}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Scheduled Payments</CardTitle>
            <Wallet className="h-5 w-5 text-mahogany" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-2xl font-extrabold">{scheduledPayments.length}</div>
            <p className="text-xs text-muted-foreground font-medium">{formatCurrency(scheduledPayments.reduce((s, p) => s + p.amount, 0))}</p>
          </CardContent>
        </Card>
      </div>

      {/* Budget vs actual per site */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Budget vs Actual by Site</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Site</TableHead>
                <TableHead>Budget</TableHead>
                <TableHead>Spent</TableHead>
                <TableHead>Remaining</TableHead>
                <TableHead>% Used</TableHead>
                <TableHead>Progress</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sites.map((site) => {
                const { budget, spent } = getBudgetVsActual(site.id);
                const pct = budget > 0 ? Math.round((spent / budget) * 100) : 0;
                const remaining = budget - spent;
                return (
                  <TableRow key={site.id}>
                    <TableCell className="font-bold">{site.name}</TableCell>
                    <TableCell>{formatCurrency(budget)}</TableCell>
                    <TableCell className="font-extrabold text-primary">{formatCurrency(spent)}</TableCell>
                    <TableCell className={remaining < 0 ? 'text-destructive font-bold' : ''}>{formatCurrency(remaining)}</TableCell>
                    <TableCell className="font-extrabold">{pct}%</TableCell>
                    <TableCell>
                      <div className="h-4 w-32 border-2 border-border bg-secondary">
                        <div className={`h-full ${pct > 80 ? 'bg-destructive' : 'bg-primary'}`} style={{ width: `${Math.min(pct, 100)}%` }} />
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Budget alerts */}
      {budgetAlerts.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <TrendingUp className="h-5 w-5" /> Budget Drift Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {budgetAlerts.map((alert) => (
              <div key={alert.id} className="border-2 border-border bg-destructive/10 px-3 py-2.5">
                <div className="flex items-center justify-between">
                  <p className="font-bold text-sm">{alert.title}</p>
                  <StatusBadge status={alert.severity} />
                </div>
                <p className="text-xs text-muted-foreground font-medium mt-1">{alert.description}</p>
                <p className="text-xs font-bold mt-1">{alert.site_name}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Quick links */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Link href="/finance/purchase-orders">
          <Card className="transition-all hover:shadow-brutal-lg hover:translate-x-[-2px] hover:translate-y-[-2px]">
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="font-display text-lg font-extrabold">Purchase Orders</p>
                <p className="text-sm text-muted-foreground font-medium">Review and approve pending POs</p>
              </div>
              <ArrowRight className="h-5 w-5 text-primary" />
            </CardContent>
          </Card>
        </Link>
        <Link href="/finance/payments">
          <Card className="transition-all hover:shadow-brutal-lg hover:translate-x-[-2px] hover:translate-y-[-2px]">
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="font-display text-lg font-extrabold">Payments</p>
                <p className="text-sm text-muted-foreground font-medium">Schedule and release payments</p>
              </div>
              <ArrowRight className="h-5 w-5 text-primary" />
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
