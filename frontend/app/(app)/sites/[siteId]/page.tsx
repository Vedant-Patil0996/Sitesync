'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  Building2, MapPin, ArrowLeft, Package, Wrench, FolderKanban,
  AlertTriangle, Wallet, Users, MinusCircle, Loader2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { formatCurrency, formatDate } from '@/lib/types';
import { apiFetch } from '@/lib/api';
import { useAuth } from '@/providers/auth-provider';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export default function SiteDetailPage() {
  const params = useParams();
  const siteId = params.siteId as string;
  const { role } = useAuth();
  const [siteData, setSiteData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Consumption Modal State
  const [consumeOpen, setConsumeOpen] = useState(false);
  const [consumeMaterialId, setConsumeMaterialId] = useState('');
  const [consumeQty, setConsumeQty] = useState('');
  const [consumeRef, setConsumeRef] = useState('');
  const [consuming, setConsuming] = useState(false);

  const fetchSite = async () => {
    try {
      const data = await apiFetch<any>(`/api/v1/sites/${siteId}`);
      setSiteData(data);
    } catch (error) {
      console.error('Failed to load site details', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSite();
  }, [siteId]);

  const handleConsumeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!consumeMaterialId || !consumeQty || parseFloat(consumeQty) <= 0) {
      toast.error('Please enter a valid material and quantity');
      return;
    }

    setConsuming(true);
    try {
      await apiFetch('/api/v1/inventory/transactions', {
        method: 'POST',
        body: JSON.stringify({
          site_id: Number(siteId),
          material_id: Number(consumeMaterialId),
          type: 'OUT',
          quantity: parseFloat(consumeQty),
          reference: consumeRef.trim() || 'Site work consumption',
        }),
      });
      toast.success('Material consumption recorded');
      setConsumeOpen(false);
      setConsumeMaterialId('');
      setConsumeQty('');
      setConsumeRef('');
      await fetchSite();
    } catch (error: any) {
      console.error('Failed to record consumption', error);
      toast.error(error.message || 'Failed to record consumption');
    } finally {
      setConsuming(false);
    }
  };

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
        description={siteData.location || 'No location set'}
        action={<StatusBadge status={siteData.status} />}
      />

      {/* Summary stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Active Projects</CardTitle>
            <FolderKanban className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="font-display text-2xl font-extrabold">{projects.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Materials in Stock</CardTitle>
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

        {/* Location Map Card */}
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
                <p className="text-sm font-bold">{siteData.location || 'Site Location'}</p>
                <p className="text-xs text-muted-foreground font-medium">
                  {siteData.latitude ? `${siteData.latitude.toFixed(4)}, ${siteData.longitude?.toFixed(4)}` : 'Coordinates not specified'}
                </p>
              </div>
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
            {projects.length === 0 && (
              <p className="text-sm text-muted-foreground font-medium py-2">No projects assigned to this site</p>
            )}
          </CardContent>
        </Card>

        {/* Inventory & Stock Consumption */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2"><Package className="h-5 w-5" /> Site Inventory</CardTitle>
            {(role === 'contractor' || role === 'pm' || role === 'admin') && (
              <Dialog open={consumeOpen} onOpenChange={setConsumeOpen}>
                <DialogTrigger asChild>
                  <Button size="sm" variant="outline" className="h-7 text-xs gap-1">
                    <MinusCircle className="h-3.5 w-3.5" /> Log Consumption
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Record Material Consumption</DialogTitle>
                    <DialogDescription>
                      Log materials used for construction work at this site.
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleConsumeSubmit} className="space-y-4 pt-2">
                    <div className="space-y-2">
                      <Label htmlFor="matSelect">Select Material</Label>
                      <Select value={consumeMaterialId} onValueChange={setConsumeMaterialId} required>
                        <SelectTrigger id="matSelect">
                          <SelectValue placeholder="Choose material" />
                        </SelectTrigger>
                        <SelectContent>
                          {inventory.map((item: any) => (
                            <SelectItem key={item.material_id} value={String(item.material_id)}>
                              {item.material_name} (In Stock: {item.quantity} {item.unit})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="qtyInput">Quantity Consumed</Label>
                      <Input
                        id="qtyInput"
                        type="number"
                        min="0.01"
                        step="any"
                        placeholder="0.00"
                        value={consumeQty}
                        onChange={(e) => setConsumeQty(e.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="noteInput">Work Reference / Task</Label>
                      <Input
                        id="noteInput"
                        placeholder="e.g. Foundation slab casting work"
                        value={consumeRef}
                        onChange={(e) => setConsumeRef(e.target.value)}
                      />
                    </div>
                    <div className="flex justify-end gap-2 pt-2">
                      <Button type="button" variant="outline" onClick={() => setConsumeOpen(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" disabled={consuming}>
                        {consuming && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Record Usage
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            )}
          </CardHeader>
          <CardContent className="space-y-2">
            {inventory.map((item: any) => {
              const isLow = item.quantity <= item.reorder_level;
              return (
                <div key={item.id} className="flex items-center justify-between border-2 border-border bg-secondary px-3 py-2">
                  <div>
                    <p className="font-bold text-sm">{item.material_name}</p>
                    <p className="text-xs text-muted-foreground font-medium">Reorder threshold: {item.reorder_level} {item.unit}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-extrabold text-sm">{item.quantity} {item.unit}</p>
                    {isLow && <Badge variant="destructive" className="brutal-badge text-[10px]">LOW</Badge>}
                  </div>
                </div>
              );
            })}
            {inventory.length === 0 && (
              <p className="text-sm text-muted-foreground font-medium py-2">No inventory stocked at this site yet</p>
            )}
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
            {equipment.length === 0 && (
              <p className="text-sm text-muted-foreground font-medium py-2">No equipment assigned</p>
            )}
          </CardContent>
        </Card>

        {/* Contractors */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Users className="h-5 w-5" /> Assigned Contractors</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {contractors.map((c: any) => (
              <div key={c.id} className="flex items-center justify-between border-2 border-border bg-secondary px-3 py-2">
                <div>
                  <p className="font-bold text-sm">{c.name}</p>
                  <p className="text-xs text-muted-foreground font-medium">{c.specialty}</p>
                </div>
                <span className="text-xs font-medium text-muted-foreground">{c.phone || 'No phone'}</span>
              </div>
            ))}
            {contractors.length === 0 && (
              <p className="text-sm text-muted-foreground font-medium py-2">No contractors assigned to this site</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
