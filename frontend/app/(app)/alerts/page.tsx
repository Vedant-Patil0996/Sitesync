'use client';

import * as React from 'react';
import { AlertTriangle, Check, X, Clock, Search, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { EmptyState } from '@/components/shared/empty-state';
import { Pagination } from '@/components/shared/pagination';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { formatDateTime } from '@/lib/types';
import { apiFetch } from '@/lib/api';
import { toast } from 'sonner';

const ALERT_TYPE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  stock: AlertTriangle,
  equipment: AlertTriangle,
  budget: AlertTriangle,
  task: Clock,
  fraud: AlertTriangle,
};

export default function AlertsPage() {
  const [alerts, setAlerts] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [currentPage, setCurrentPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const itemsPerPage = 10;
  
  const [search, setSearch] = React.useState('');
  const [typeFilter, setTypeFilter] = React.useState('all');
  const [severityFilter, setSeverityFilter] = React.useState('all');
  const [statusFilter, setStatusFilter] = React.useState('all');

  const loadData = async (page: number) => {
    setLoading(true);
    try {
      const skip = (page - 1) * itemsPerPage;
      const data = await apiFetch(`/api/v1/alerts?skip=${skip}&limit=${itemsPerPage}`);
      setAlerts(data.items);
      setTotalPages(data.pages);
      setCurrentPage(data.page);
    } catch (error) {
      console.error('Failed to load alerts:', error);
      toast.error('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    loadData(1);
  }, []);

  const handleAction = async (id: number, action: 'resolve' | 'snooze' | 'dismiss') => {
    try {
      await apiFetch(`/api/v1/alerts/${id}/${action}`, { method: 'PATCH' });
      toast.success(`Alert ${action}d`);
      loadData(currentPage);
    } catch (error) {
      toast.error(`Failed to ${action} alert`);
    }
  };

  const filtered = alerts.filter((a) => {
    const matchesSearch = a.title.toLowerCase().includes(search.toLowerCase()) ||
                          (a.description || '').toLowerCase().includes(search.toLowerCase()) ||
                          a.site_name.toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === 'all' || a.type === typeFilter;
    const matchesSeverity = severityFilter === 'all' || a.severity === severityFilter;
    const matchesStatus = statusFilter === 'all' || a.status === statusFilter;
    return matchesSearch && matchesType && matchesSeverity && matchesStatus;
  });

  return (
    <div>
      <PageHeader title="Alerts" description="Stock, equipment, budget, task, and fraud alerts across all sites" />

      {/* Summary */}
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <Card className="p-4">
          <div className="text-xs font-semibold text-muted-foreground">Critical</div>
          <div className="font-display text-2xl font-extrabold text-destructive">
            {alerts.filter((a) => a.severity === 'critical' && a.status === 'open').length}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-xs font-semibold text-muted-foreground">Warning</div>
          <div className="font-display text-2xl font-extrabold text-mahogany">
            {alerts.filter((a) => a.severity === 'warning' && a.status === 'open').length}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-xs font-semibold text-muted-foreground">Info</div>
          <div className="font-display text-2xl font-extrabold text-blue-600">
            {alerts.filter((a) => a.severity === 'info' && a.status === 'open').length}
          </div>
        </Card>
      </div>

      {/* Filters */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search alerts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-full sm:w-[150px]"><SelectValue placeholder="Type" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="stock">Stock</SelectItem>
            <SelectItem value="equipment">Equipment</SelectItem>
            <SelectItem value="budget">Budget</SelectItem>
            <SelectItem value="task">Task</SelectItem>
            <SelectItem value="fraud">Fraud</SelectItem>
          </SelectContent>
        </Select>
        <Select value={severityFilter} onValueChange={setSeverityFilter}>
          <SelectTrigger className="w-full sm:w-[150px]"><SelectValue placeholder="Severity" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Severity</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="warning">Warning</SelectItem>
            <SelectItem value="info">Info</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="snoozed">Snoozed</SelectItem>
            <SelectItem value="dismissed">Dismissed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Alert list */}
      {loading ? (
        <div className="flex h-32 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState icon={AlertTriangle} title="No alerts found" description="No alerts match your current filters." />
      ) : (
        <div className="space-y-3">
          {filtered.map((alert) => {
            const Icon = ALERT_TYPE_ICONS[alert.type] ?? AlertTriangle;
            return (
              <Card key={alert.id}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className={`flex h-10 w-10 shrink-0 items-center justify-center border-2 border-border ${
                      alert.severity === 'critical' ? 'bg-destructive text-destructive-foreground' :
                      alert.severity === 'warning' ? 'bg-soft-sand text-dark-espresso' :
                      'bg-blue-500 text-white'
                    }`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-bold">{alert.title}</p>
                        <StatusBadge status={alert.severity} />
                        <Badge variant="outline" className="brutal-badge text-[10px]">{alert.type}</Badge>
                        <StatusBadge status={alert.status} />
                      </div>
                      <p className="text-sm text-muted-foreground font-medium mt-1">{alert.description}</p>
                      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted-foreground font-medium">
                        <span>{alert.site_name}</span>
                        <span>Created {formatDateTime(alert.created_at)}</span>
                        {alert.resolved_by_name && <span>Resolved by {alert.resolved_by_name}</span>}
                      </div>
                    </div>
                    {alert.status === 'open' && (
                      <div className="flex flex-col gap-1 sm:flex-row">
                        <Button size="sm" className="gap-1 h-8" onClick={() => handleAction(alert.id, 'resolve')}><Check className="h-3 w-3" /> Resolve</Button>
                        <Button size="sm" variant="outline" className="gap-1 h-8" onClick={() => handleAction(alert.id, 'snooze')}><Clock className="h-3 w-3" /> Snooze</Button>
                        <Button size="sm" variant="destructive" className="gap-1 h-8" onClick={() => handleAction(alert.id, 'dismiss')}><X className="h-3 w-3" /> Dismiss</Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
      
      {!loading && totalPages > 1 && (
        <div className="mt-4 flex justify-end">
          <Pagination 
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={loadData}
          />
        </div>
      )}
    </div>
  );
}
