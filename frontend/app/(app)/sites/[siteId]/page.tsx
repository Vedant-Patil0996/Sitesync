'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  Building2, MapPin, ArrowLeft, Package, Wrench, FolderKanban,
  AlertTriangle, Wallet, Users,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { formatCurrency, formatDate } from '@/lib/types';
import { apiFetch } from '@/lib/api';

export default function SiteDetailPage() {
  const params = useParams();
  const siteId = params.siteId as string;
  const [siteData, setSiteData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchSite() {
      try {
        const data = await apiFetch<any>(`/api/v1/sites/${siteId}`);
        setSiteData(data);
      } catch (error) {
        console.error('Failed to load site details', error);
      } finally {
        setLoading(false);
      }
    }
    fetchSite();
  }, [siteId]);

  if (loading) {
    return <div className="p-8">Loading site details...</div>;
  }

  if (!siteData) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <p className="text-lg font-bold">Site not found</p>
        <Link href="/sites"><Button variant="outline">Back to Sites</Button></Link>
      </div>
    );
  }

  const { projects, inventory, equipment, alerts, contractors, budget, spent, budget_pct } = siteData;

  return (
    <div>
      <Link href="/sites" className="mb-4 flex items-center gap-2 text-sm font-bold text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to Sites
      </Link>

      <PageHeader
        title={siteData.name}
        description={siteData.location_text}
        action={<StatusBadge status={siteData.status} />}
      />

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Projects</CardTitle>
            <FolderKanban className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-2xl font-extrabold">{projects.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Materials</CardTitle>
            <Package className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-2xl font-extrabold">{inventory.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Equipment</CardTitle>
            <Wrench className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-2xl font-extrabold">{equipment.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Open Alerts</CardTitle>
            <AlertTriangle className="h-5 w-5 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-2xl font-extrabold">{alerts.length}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Budget */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Wallet className="h-5 w-5" /> Budget vs Actual</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm font-bold">
              <span>Spent: {formatCurrency(spent)}</span>
              <span>Budget: {formatCurrency(budget)}</span>
            </div>
            <div className="h-6 border-2 border-border bg-secondary">
              <div className="h-full bg-primary transition-all" style={{ width: `${Math.min(budget_pct, 100)}%` }} />
            </div>
            <p className="text-center font-display text-2xl font-extrabold">{budget_pct}% used</p>
          </CardContent>
        </Card>

        {/* Map placeholder */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><MapPin className="h-5 w-5" /> Location</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative h-48 border-2 border-border bg-secondary overflow-hidden">
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
                <div className="flex h-12 w-12 items-center justify-center border-2 border-border bg-primary shadow-brutal">
                  <Building2 className="h-6 w-6 text-primary-foreground" />
                </div>
                <p className="text-sm font-bold">{siteData.location_text}</p>
                <p className="text-xs text-muted-foreground font-medium">{siteData.latitude?.toFixed(4) || 'N/A'}, {siteData.longitude?.toFixed(4) || 'N/A'}</p>
              </div>
              <div className="absolute inset-0" style={{
                backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 20px, hsl(var(--border) / 0.1) 20px, hsl(var(--border) / 0.1) 21px), repeating-linear-gradient(90deg, transparent, transparent 20px, hsl(var(--border) / 0.1) 20px, hsl(var(--border) / 0.1) 21px)'
              }} />
            </div>
          </CardContent>
        </Card>

        {/* Projects */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><FolderKanban className="h-5 w-5" /> Projects</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {projects.map((project: any) => (
              <Link key={project.id} href={`/projects/${project.id}`}>
                <div className="border-2 border-border bg-secondary px-3 py-2.5 hover:bg-accent transition-colors">
                  <div className="flex items-center justify-between">
                    <p className="font-bold text-sm">{project.name}</p>
                    <StatusBadge status={project.status} />
                  </div>
                  <div className="mt-1.5 flex items-center justify-between text-xs text-muted-foreground font-medium">
                    <span>{formatDate(project.start_date)} - {formatDate(project.end_date)}</span>
                    <span>{project.progress_percent}% complete</span>
                  </div>
                  <div className="mt-1 h-2 border border-border bg-muted">
                    <div className="h-full bg-primary" style={{ width: `${project.progress_percent}%` }} />
                  </div>
                </div>
              </Link>
            ))}
          </CardContent>
        </Card>

        {/* Inventory */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Package className="h-5 w-5" /> Inventory</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {inventory.map((item: any) => {
              const isLow = item.quantity <= item.reorder_level;
              return (
                <div key={item.id} className="flex items-center justify-between border-2 border-border bg-secondary px-3 py-2">
                  <div>
                    <p className="font-bold text-sm">{item.material_name}</p>
                    <p className="text-xs text-muted-foreground font-medium">Reorder at {item.reorder_level} {item.unit}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-extrabold text-sm">{item.quantity} {item.unit}</p>
                    {isLow && <Badge variant="destructive" className="brutal-badge text-[10px]">LOW</Badge>}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Equipment */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Wrench className="h-5 w-5" /> Equipment</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {equipment.map((eq: any) => (
              <div key={eq.id} className="flex items-center justify-between border-2 border-border bg-secondary px-3 py-2">
                <div>
                  <p className="font-bold text-sm">{eq.name}</p>
                  <p className="text-xs text-muted-foreground font-medium">{eq.type} - {eq.hours_used}h used</p>
                </div>
                <StatusBadge status={eq.status} />
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Contractors */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Users className="h-5 w-5" /> Contractors</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {contractors.map((c: any) => (
              <div key={c.id} className="flex items-center justify-between border-2 border-border bg-secondary px-3 py-2">
                <div>
                  <p className="font-bold text-sm">{c.name}</p>
                  <p className="text-xs text-muted-foreground font-medium">{c.specialty}</p>
                </div>
                <span className="text-xs font-medium text-muted-foreground">{c.phone}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Alerts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5" /> Active Alerts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {alerts.slice(0, 5).map((alert: any) => (
              <div key={alert.id} className="border-2 border-border bg-secondary px-3 py-2">
                <div className="flex items-center justify-between">
                  <p className="font-bold text-sm">{alert.title}</p>
                  <StatusBadge status={alert.severity} />
                </div>
                <p className="text-xs text-muted-foreground font-medium mt-1">{alert.description}</p>
              </div>
            ))}
            {alerts.length === 0 && (
              <p className="text-sm text-muted-foreground font-medium text-center py-2">No active alerts</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
