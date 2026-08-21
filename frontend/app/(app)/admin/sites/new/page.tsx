'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Building2, MapPin, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/shared/page-header';
import { apiFetch } from '@/lib/api';
import { useAuth } from '@/providers/auth-provider';
import { toast } from 'sonner';

export default function CreateSitePage() {
  const router = useRouter();
  const { role } = useAuth();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: '',
    location: '',
    latitude: '',
    longitude: '',
    status: 'active',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) {
      toast.error('Site name is required');
      return;
    }

    setLoading(true);
    try {
      const payload: Record<string, any> = {
        name: form.name.trim(),
        location: form.location.trim() || null,
        status: form.status,
      };

      if (form.latitude.trim()) {
        payload.latitude = parseFloat(form.latitude);
      }
      if (form.longitude.trim()) {
        payload.longitude = parseFloat(form.longitude);
      }

      const result = await apiFetch<any>('/api/v1/sites/', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      toast.success('Site created successfully');
      router.push(`/sites/${result.id}`);
    } catch (error: any) {
      console.error('Failed to create site:', error);
      toast.error(error.message || 'Failed to create site');
    } finally {
      setLoading(false);
    }
  };

  if (role && role !== 'admin') {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-lg font-bold text-destructive">Unauthorized</p>
        <p className="text-sm text-muted-foreground mt-1">Only administrators can create new construction sites.</p>
        <Link href="/sites" className="mt-4">
          <Button variant="outline">Back to Sites</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-3xl py-6">
      <Link href="/sites" className="mb-4 flex items-center gap-2 text-sm font-bold text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to Sites
      </Link>

      <PageHeader
        title="Create Construction Site"
        description="Add a new project site location to your organization"
      />

      <Card className="mt-6 border-2 border-border shadow-brutal">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <Building2 className="h-5 w-5 text-primary" /> Site Details
          </CardTitle>
          <CardDescription>
            Enter the site name, location details, and coordinates for GPS/mapping.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">
                Site Name <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Metro Heights Phase 1"
                className="h-10 w-full rounded-sm border-2 border-border bg-card px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">
                Location / Address
              </label>
              <div className="relative">
                <MapPin className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="e.g. 742 Evergreen Terrace, Sector 4"
                  className="h-10 w-full rounded-sm border-2 border-border bg-card pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">
                  Latitude (Optional)
                </label>
                <input
                  type="number"
                  step="any"
                  placeholder="e.g. 28.6139"
                  className="h-10 w-full rounded-sm border-2 border-border bg-card px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  value={form.latitude}
                  onChange={(e) => setForm({ ...form, latitude: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">
                  Longitude (Optional)
                </label>
                <input
                  type="number"
                  step="any"
                  placeholder="e.g. 77.2090"
                  className="h-10 w-full rounded-sm border-2 border-border bg-card px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  value={form.longitude}
                  onChange={(e) => setForm({ ...form, longitude: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">
                Initial Status
              </label>
              <select
                className="h-10 w-full rounded-sm border-2 border-border bg-card px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
              >
                <option value="active">Active</option>
                <option value="on_hold">On Hold</option>
                <option value="completed">Completed</option>
              </select>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t">
              <Link href="/sites">
                <Button type="button" variant="outline">
                  Cancel
                </Button>
              </Link>
              <Button type="submit" disabled={loading || !form.name.trim()}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Create Site
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
