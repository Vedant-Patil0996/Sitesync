'use client';

import { useState, useEffect } from 'react';
import { Wallet, TrendingUp, TrendingDown, ArrowRight, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { formatCurrency } from '@/lib/types';
import { apiFetch } from '@/lib/api';

export default function FinanceOverviewPage() {
  const [summary, setSummary] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [summaryData, alertsData] = await Promise.all([
          apiFetch<any>('/api/v1/finance/summary'),
          apiFetch<any>('/api/v1/alerts?limit=5')
        ]);
        setSummary(summaryData);
        setAlerts(alertsData.items || []);
      } catch (error) {
        console.error('Failed to load finance data:', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const budgetAlerts = alerts.filter((a) => a.type === 'budget' && (a.status === 'open' || a.status === 'new'));

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
            <div className="font-display text-2xl font-extrabold">{formatCurrency(summary?.total_budget || 0)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Total Spend</CardTitle>
            <TrendingDown className="h-5 w-5 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-2xl font-extrabold text-primary">{formatCurrency(summary?.total_spent || 0)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Pending Payments</CardTitle>
            <TrendingUp className="h-5 w-5 text-mahogany" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-2xl font-extrabold">{formatCurrency(summary?.pending_payments || 0)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Recent Transactions</CardTitle>
            <Wallet className="h-5 w-5 text-mahogany" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-2xl font-extrabold">{summary?.recent_transactions?.length || 0}</div>
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
              {summary?.sites_budget?.map((site: any) => {
                const { budget, spent } = site;
                const pct = budget > 0 ? Math.round((spent / budget) * 100) : 0;
                const remaining = budget - spent;
                return (
                  <TableRow key={site.site_id}>
                    <TableCell className="font-bold">{site.site_name}</TableCell>
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
              {(!summary?.sites_budget || summary.sites_budget.length === 0) && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">No sites found.</TableCell>
                </TableRow>
              )}
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
