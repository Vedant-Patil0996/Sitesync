'use client';

import * as React from 'react';
import { Wrench, Search } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { apiFetch } from '@/lib/api';
import { Pagination } from '@/components/shared/pagination';

export default function EquipmentPage() {
  const [search, setSearch] = React.useState('');
  const [siteFilter, setSiteFilter] = React.useState('all');

  const [equipment, setEquipment] = React.useState<any[]>([]);
  const [sites, setSites] = React.useState<any[]>([]);
  const [summary, setSummary] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [page, setPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const limit = 10;

  React.useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const skip = (page - 1) * limit;
        const [eqRes, sitesRes, summaryRes] = await Promise.all([
          apiFetch<any>(`/api/v1/equipment?skip=${skip}&limit=${limit}`),
          apiFetch<any>(`/api/v1/sites?skip=0&limit=100`),
          apiFetch<any>(`/api/v1/dashboard/summary`)
        ]);
        setEquipment(eqRes.items);
        setTotalPages(eqRes.pages);
        setSites(sitesRes.items);
        setSummary(summaryRes);
      } catch (error) {
        console.error('Failed to load equipment data', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [page]);

  const filtered = equipment.filter((item) => {
    const matchesSearch = item.name.toLowerCase().includes(search.toLowerCase()) ||
                          item.type.toLowerCase().includes(search.toLowerCase());
    const matchesSite = siteFilter === 'all' || String(item.site_id) === siteFilter;
    return matchesSearch && matchesSite;
  });

  return (
    <div>
      <PageHeader
        title="Equipment"
        description="Track equipment status and allocation across sites"
      />

      {/* Summary */}
      {!loading && summary && (
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-muted-foreground">Active</div>
                <div className="font-display text-2xl font-extrabold text-green-600">{summary.equipment_status?.active || 0}</div>
              </div>
              <div className="flex h-10 w-10 items-center justify-center border-2 border-border bg-green-500 shadow-brutal-sm">
                <Wrench className="h-5 w-5 text-white" />
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-muted-foreground">Idle</div>
                <div className="font-display text-2xl font-extrabold">{summary.equipment_status?.idle || 0}</div>
              </div>
              <div className="flex h-10 w-10 items-center justify-center border-2 border-border bg-secondary shadow-brutal-sm">
                <Wrench className="h-5 w-5 text-muted-foreground" />
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-muted-foreground">Maintenance</div>
                <div className="font-display text-2xl font-extrabold text-mahogany">{summary.equipment_status?.maintenance || 0}</div>
              </div>
              <div className="flex h-10 w-10 items-center justify-center border-2 border-border bg-soft-sand shadow-brutal-sm">
                <Wrench className="h-5 w-5 text-dark-espresso" />
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search equipment..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={siteFilter} onValueChange={setSiteFilter}>
          <SelectTrigger className="w-full sm:w-[200px]">
            <SelectValue placeholder="Filter by site" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Sites</SelectItem>
            {sites.map((site) => (
              <SelectItem key={site.id} value={String(site.id)}>{site.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="p-8">Loading equipment...</div>
      ) : (
        <>
          {/* Table */}
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Equipment</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Site</TableHead>
                    <TableHead>Allocated To</TableHead>
                    <TableHead>Hours Used</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((eq) => (
                    <TableRow key={eq.id}>
                      <TableCell className="font-bold">{eq.name}</TableCell>
                      <TableCell className="text-muted-foreground">{eq.type}</TableCell>
                      <TableCell className="text-sm">{eq.site_name}</TableCell>
                      <TableCell className="text-sm">{eq.task_name ?? <span className="text-muted-foreground">Not allocated</span>}</TableCell>
                      <TableCell className="font-extrabold">{eq.hours_used}h</TableCell>
                      <TableCell><StatusBadge status={eq.status} /></TableCell>
                    </TableRow>
                  ))}
                  {filtered.length === 0 && (
                     <TableRow>
                        <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                           No equipment found.
                        </TableCell>
                     </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <div className="mt-4">
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          </div>
        </>
      )}
    </div>
  );
}
