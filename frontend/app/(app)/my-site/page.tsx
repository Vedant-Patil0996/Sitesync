'use client';

import * as React from 'react';
import { Building2, Package, Wrench, AlertTriangle, CheckSquare, Plus, Clock, Activity } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { apiFetch } from '@/lib/api';
import { formatDate } from '@/lib/types';
import { MaterialRequestDialog } from '@/components/procurement/material-request-dialog';
import { SiteMap } from '@/components/sites/site-map';

export default function MySitePage() {
  const [site, setSite] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadMySite() {
      try {
        const result = await apiFetch<any>('/api/v1/sites/my-site');
        setSite(result);
      } catch (err: any) {
        setError(err.message || 'Failed to load your site');
      } finally {
        setLoading(false);
      }
    }
    loadMySite();
  }, []);

  if (loading) return <div className="p-8">Loading your site data...</div>;

  if (error) {
    return (
      <div className="p-8">
        <div className="border-2 border-destructive bg-destructive/10 p-4 text-destructive">
          <h2 className="font-bold text-lg mb-2">Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!site) return <div className="p-8">No site data available.</div>;

  return (
    <div>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <PageHeader
          title={`My Site: ${site.name}`}
          description={site.location}
        />
        <div className="flex gap-2">
          <MaterialRequestDialog siteId={site.id} siteName={site.name} />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Status</CardTitle>
            <Activity className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-display font-extrabold capitalize">{site.status.replace('_', ' ')}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Active Projects</CardTitle>
            <Building2 className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-display font-extrabold">{site.project_count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Open Alerts</CardTitle>
            <AlertTriangle className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-display font-extrabold">{site.alert_count}</div>
          </CardContent>
        </Card>
      </div>

      <div className="mb-6">
        <SiteMap
          name={site.name}
          location={site.location}
          latitude={site.latitude}
          longitude={site.longitude}
          status={site.status}
        />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Alerts (Read-Only for Contractors usually) */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" /> Active Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            {site.alerts && site.alerts.length > 0 ? (
              <div className="space-y-4">
                {site.alerts.map((alert: any) => (
                  <div key={alert.id} className={`flex items-start gap-3 border-l-4 p-3 ${
                    alert.severity === 'critical' ? 'border-destructive bg-destructive/10' :
                    alert.severity === 'warning' ? 'border-yellow-500 bg-yellow-500/10' :
                    'border-primary bg-primary/10'
                  }`}>
                    <AlertTriangle className={`h-5 w-5 shrink-0 ${
                      alert.severity === 'critical' ? 'text-destructive' :
                      alert.severity === 'warning' ? 'text-yellow-600' :
                      'text-primary'
                    }`} />
                    <div>
                      <h4 className="font-bold text-sm">{alert.title}</h4>
                      <p className="text-xs mt-1 text-muted-foreground">{alert.description}</p>
                      <span className="text-[10px] font-bold uppercase mt-2 block">{formatDate(alert.created_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No active alerts for this site.</p>
            )}
          </CardContent>
        </Card>

        {/* Inventory Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" /> Inventory Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            {site.inventory && site.inventory.length > 0 ? (
              <div className="space-y-3">
                {site.inventory.slice(0, 5).map((inv: any) => {
                  const isLow = inv.quantity <= inv.reorder_level;
                  return (
                    <div key={inv.id} className="flex items-center justify-between border-b-2 border-border pb-2 last:border-0 last:pb-0">
                      <div>
                        <p className="font-bold text-sm">{inv.material_name}</p>
                        <p className="text-xs text-muted-foreground">Reorder at: {inv.reorder_level}</p>
                      </div>
                      <div className="text-right">
                        <div className="font-display font-extrabold text-lg">
                          {inv.quantity} <span className="text-sm text-muted-foreground font-sans font-medium">{inv.unit}</span>
                        </div>
                        {isLow && <span className="text-[10px] font-bold text-destructive">LOW STOCK</span>}
                      </div>
                    </div>
                  );
                })}
                {site.inventory.length > 5 && (
                  <p className="text-xs text-center text-muted-foreground font-bold pt-2">
                    + {site.inventory.length - 5} more items
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No inventory recorded for this site.</p>
            )}
          </CardContent>
        </Card>

        {/* Equipment Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wrench className="h-5 w-5" /> Equipment on Site
            </CardTitle>
          </CardHeader>
          <CardContent>
            {site.equipment && site.equipment.length > 0 ? (
              <div className="space-y-3">
                {site.equipment.map((eq: any) => (
                  <div key={eq.id} className="flex items-center justify-between border-2 border-border p-2">
                    <div>
                      <p className="font-bold text-sm">{eq.name}</p>
                      <p className="text-xs text-muted-foreground">{eq.type}</p>
                    </div>
                    <Badge variant={
                      eq.status === 'active' ? 'success' :
                      eq.status === 'maintenance' ? 'destructive' :
                      'default'
                    } className="text-[10px]">
                      {eq.status.toUpperCase()}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No equipment assigned to this site.</p>
            )}
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
