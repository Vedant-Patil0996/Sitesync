'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { FolderKanban, ArrowRight, Calendar, Wallet, Plus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { apiFetch } from '@/lib/api';
import { formatCurrency, formatDate } from '@/lib/types';
import { Pagination } from '@/components/shared/pagination';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/providers/auth-provider';

export default function ProjectsListPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const limit = 10;
  const { role } = useAuth();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [siteId, setSiteId] = useState('');
  const [pmId, setPmId] = useState('');
  const [budget, setBudget] = useState('0');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [status, setStatus] = useState('planning');
  const [sites, setSites] = useState<any[]>([]);
  const [pms, setPms] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function loadProjects() {
      setLoading(true);
      try {
        const skip = (page - 1) * limit;
        const [result, siteResult, userResult] = await Promise.all([
          apiFetch<any>(`/api/v1/projects?skip=${skip}&limit=${limit}`),
          apiFetch<any>('/api/v1/sites?skip=0&limit=100'),
          role === 'admin' ? apiFetch<any>('/api/v1/admin/users?skip=0&limit=100') : Promise.resolve({ items: [] }),
        ]);
        setProjects(result.items);
        setTotalPages(result.pages);
        setSites(siteResult.items || []);
        setPms((userResult.items || []).filter((user: any) => user.role === 'pm' && user.is_active));
      } catch (error) {
        console.error('Failed to load projects', error);
      } finally {
        setLoading(false);
      }
    }
    loadProjects();
  }, [page, role]);

  const createProject = async () => {
    if (!name.trim() || !siteId || !pmId) return;
    setSaving(true);
    try {
      await apiFetch('/api/v1/projects/', {
        method: 'POST',
        body: JSON.stringify({ name, site_id: Number(siteId), pm_id: Number(pmId), budget_allocated: Number(budget), start_date: startDate || null, end_date: endDate || null, status }),
      });
      setShowCreate(false);
      setName('');
      setSiteId('');
      setPmId('');
      setBudget('0');
      setStartDate('');
      setEndDate('');
      setStatus('planning');
      setPage(1);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Projects"
        description="All construction projects across your sites"
        action={role === 'admin' ? <Button className="gap-2" onClick={() => setShowCreate((value) => !value)}><Plus className="h-4 w-4" /> New Project</Button> : undefined}
      />

      {role === 'admin' && showCreate && (
        <Card className="mb-6">
          <CardHeader><CardTitle className="text-lg">Create Project</CardTitle></CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Input placeholder="Project name" value={name} onChange={(event) => setName(event.target.value)} />
            <select className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" value={siteId} onChange={(event) => setSiteId(event.target.value)}><option value="">Select site</option>{sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}</select>
            <select className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" value={pmId} onChange={(event) => setPmId(event.target.value)}><option value="">Assign PM</option>{pms.map((pm) => <option key={pm.id} value={pm.id}>{pm.name} ({pm.email})</option>)}</select>
            <Input type="number" min="0" placeholder="Initial budget" value={budget} onChange={(event) => setBudget(event.target.value)} />
            <Input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
            <Input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
            <select className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" value={status} onChange={(event) => setStatus(event.target.value)}><option value="planning">Planning</option><option value="in_progress">In progress</option><option value="on_hold">On hold</option></select>
            <div className="sm:col-span-2 lg:col-span-4"><Button onClick={createProject} disabled={saving || !name.trim() || !siteId || !pmId}>{saving ? 'Creating...' : 'Create Project'}</Button></div>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="p-8">Loading projects...</div>
      ) : (
        <>
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <Link key={project.id} href={`/projects/${project.id}`}>
                <Card className="h-full transition-all hover:shadow-brutal-lg hover:translate-x-[-2px] hover:translate-y-[-2px]">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <div className="flex h-10 w-10 items-center justify-center border-2 border-border bg-primary shadow-brutal-sm">
                          <FolderKanban className="h-5 w-5 text-primary-foreground" />
                        </div>
                        <div>
                          <CardTitle className="text-base">{project.name}</CardTitle>
                          <p className="text-xs text-muted-foreground font-medium">{project.site_name || 'No site assigned'}</p>
                        </div>
                      </div>
                      <StatusBadge status={project.status} />
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="grid grid-cols-3 gap-2">
                      <div className="border-2 border-border bg-secondary px-2 py-1.5 text-center">
                        <div className="font-display text-lg font-extrabold">{project.task_count || 0}</div>
                        <div className="text-[10px] font-semibold text-muted-foreground">Tasks</div>
                      </div>
                      <div className="border-2 border-border bg-secondary px-2 py-1.5 text-center">
                        <div className="font-display text-lg font-extrabold">{project.completed_task_count || 0}</div>
                        <div className="text-[10px] font-semibold text-muted-foreground">Done</div>
                      </div>
                      <div className="border-2 border-border bg-secondary px-2 py-1.5 text-center">
                        <div className="font-display text-lg font-extrabold">{project.milestone_count || 0}</div>
                        <div className="text-[10px] font-semibold text-muted-foreground">Miles.</div>
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold text-muted-foreground">Progress</span>
                        <span className="text-xs font-extrabold">{project.progress_percent}%</span>
                      </div>
                      <div className="h-3 border-2 border-border bg-secondary">
                        <div className="h-full bg-primary transition-all" style={{ width: `${project.progress_percent}%` }} />
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
                      <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(project.end_date)}</span>
                      <span className="flex items-center gap-1"><Wallet className="h-3 w-3" />{formatCurrency(project.budget_allocated)}</span>
                    </div>
                    <div className="flex items-center justify-end gap-1 text-sm font-bold text-primary">
                      View Details <ArrowRight className="h-3 w-3" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
          {projects.length === 0 && (
            <div className="p-8 text-center text-muted-foreground">No projects found.</div>
          )}
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
