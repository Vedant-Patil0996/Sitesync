'use client';

import Link from 'next/link';
import { Building2, MapPin, ArrowRight, Plus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { useRole } from '@/components/providers/role-provider';
import { sites, projects, alerts, getBudgetVsActual } from '@/lib/mock-data';
import { formatCurrency } from '@/lib/types';

export default function SitesListPage() {
  const { role } = useRole();

  return (
    <div>
      <PageHeader
        title="Sites"
        description="All construction sites in your organization"
        action={role === 'admin' && (
          <Link href="/admin/sites/new">
            <Button className="gap-2"><Plus className="h-4 w-4" /> Add Site</Button>
          </Link>
        )}
      />

      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {sites.map((site) => {
          const siteProjects = projects.filter((p) => p.site_id === site.id);
          const siteAlerts = alerts.filter((a) => a.site_id === site.id && a.status === 'open');
          const { budget, spent } = getBudgetVsActual(site.id);
          const budgetPct = budget > 0 ? Math.round((spent / budget) * 100) : 0;

          return (
            <Link key={site.id} href={`/sites/${site.id}`}>
              <Card className="h-full transition-all hover:shadow-brutal-lg hover:translate-x-[-2px] hover:translate-y-[-2px]">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div className="flex h-10 w-10 items-center justify-center border-2 border-border bg-primary shadow-brutal-sm">
                        <Building2 className="h-5 w-5 text-primary-foreground" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{site.name}</CardTitle>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground font-medium">
                          <MapPin className="h-3 w-3" />
                          {site.location_text}
                        </div>
                      </div>
                    </div>
                    <StatusBadge status={site.status} />
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="border-2 border-border bg-secondary px-2 py-1.5">
                      <div className="text-[10px] font-semibold text-muted-foreground">Projects</div>
                      <div className="font-display text-lg font-extrabold">{siteProjects.length}</div>
                    </div>
                    <div className="border-2 border-border bg-secondary px-2 py-1.5">
                      <div className="text-[10px] font-semibold text-muted-foreground">Alerts</div>
                      <div className="font-display text-lg font-extrabold">{siteAlerts.length}</div>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-muted-foreground">Budget Used</span>
                      <span className="text-xs font-extrabold">{budgetPct}%</span>
                    </div>
                    <div className="h-4 border-2 border-border bg-secondary">
                      <div className="h-full bg-primary transition-all" style={{ width: `${Math.min(budgetPct, 100)}%` }} />
                    </div>
                    <div className="mt-1 flex justify-between text-xs font-medium text-muted-foreground">
                      <span>{formatCurrency(spent)} spent</span>
                      <span>{formatCurrency(budget)} budget</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-end gap-1 pt-1 text-sm font-bold text-primary">
                    View Details <ArrowRight className="h-3 w-3" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
