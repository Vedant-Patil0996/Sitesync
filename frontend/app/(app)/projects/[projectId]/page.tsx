'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, FolderKanban, CheckCircle2, Circle, AlertCircle, Calendar, Flag, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { formatCurrency, formatDate } from '@/lib/types';
import { apiFetch } from '@/lib/api';
import { useAuth } from '@/providers/auth-provider';
import GanttChart from '@/components/projects/GanttChart';

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.projectId as string;
  const router = useRouter();
  const { role } = useAuth();
  const [projectData, setProjectData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editBudget, setEditBudget] = useState('');
  const [siteData, setSiteData] = useState<any>(null);
  const [sites, setSites] = useState<any[]>([]);
  const [pms, setPms] = useState<any[]>([]);
  const [taskForm, setTaskForm] = useState({ name: '', description: '', priority: 'medium', start_date: '', end_date: '', assigned_to: '', depends_on_task_id: '' });
  const [milestoneForm, setMilestoneForm] = useState({ name: '', due_date: '', status: 'upcoming' });
  const [editingMilestone, setEditingMilestone] = useState<any>(null);
  const [resourceSelection, setResourceSelection] = useState<Record<number, string>>({});
  const [scheduleHealth, setScheduleHealth] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'list' | 'gantt'>('list');

  const fetchProjectDetails = async () => {
    try {
      const data = await apiFetch<any>(`/api/v1/projects/${projectId}`);
      setProjectData(data);
      const site = await apiFetch<any>(`/api/v1/sites/${data.site_id}`);
      setSiteData(site);
      
      // Load schedule health metrics
      const health = await apiFetch<any>(`/api/v1/projects/${projectId}/schedule-health`);
      setScheduleHealth(health);

      if (role === 'admin') {
        const [siteResult, userResult] = await Promise.all([
          apiFetch<any>('/api/v1/sites?skip=0&limit=100'),
          apiFetch<any>('/api/v1/admin/users?skip=0&limit=100'),
        ]);
        setSites(siteResult.items || []);
        setPms((userResult.items || []).filter((user: any) => user.role === 'pm' && user.is_active));
      }
    } catch (error) {
      console.error('Failed to load project details', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjectDetails();
  }, [projectId, role]);

  const saveProject = async () => {
    await apiFetch(`/api/v1/projects/${projectId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        name: editName,
        budget_allocated: Number(editBudget),
        site_id: projectData.site_id,
        pm_id: projectData.pm_id,
        start_date: projectData.start_date || null,
        end_date: projectData.end_date || null,
        status: projectData.status
      }),
    });
    setEditing(false);
    await reloadProject();
  };

  const saveSchedule = async () => {
    await apiFetch(`/api/v1/projects/${projectId}/schedule`, {
      method: 'PATCH',
      body: JSON.stringify({
        start_date: projectData.start_date || null,
        end_date: projectData.end_date || null,
        status: projectData.status
      }),
    });
    await reloadProject();
  };

  const archiveProject = async () => {
    await apiFetch(`/api/v1/projects/${projectId}/archive`, { method: 'PATCH' });
    router.push('/projects');
  };

  const reloadProject = async () => {
    const data = await apiFetch<any>(`/api/v1/projects/${projectId}`);
    setProjectData(data);
    setSiteData(await apiFetch<any>(`/api/v1/sites/${data.site_id}`));
    const health = await apiFetch<any>(`/api/v1/projects/${projectId}/schedule-health`);
    setScheduleHealth(health);
  };

  const createTask = async () => {
    if (!taskForm.name.trim()) return;
    const result = await apiFetch<any>(`/api/v1/projects/${projectId}/tasks`, {
      method: 'POST',
      body: JSON.stringify({
        ...taskForm,
        assigned_to: taskForm.assigned_to ? Number(taskForm.assigned_to) : null,
        depends_on_task_id: taskForm.depends_on_task_id ? Number(taskForm.depends_on_task_id) : null,
        start_date: taskForm.start_date || null,
        end_date: taskForm.end_date || null
      }),
    });
    setTaskForm({ name: '', description: '', priority: 'medium', start_date: '', end_date: '', assigned_to: '', depends_on_task_id: '' });
    await reloadProject();
    return result;
  };

  const updateTask = async (task: any, values: Record<string, unknown>) => {
    await apiFetch(`/api/v1/projects/${projectId}/tasks/${task.id}`, {
      method: 'PATCH',
      body: JSON.stringify(values)
    });
    await reloadProject();
  };

  const createMilestone = async () => {
    if (!milestoneForm.name.trim()) return;
    await apiFetch(`/api/v1/projects/${projectId}/milestones`, {
      method: 'POST',
      body: JSON.stringify({
        ...milestoneForm,
        due_date: milestoneForm.due_date || null
      })
    });
    setMilestoneForm({ name: '', due_date: '', status: 'upcoming' });
    await reloadProject();
  };

  const saveMilestone = async () => {
    if (!editingMilestone) return;
    await apiFetch(`/api/v1/projects/${projectId}/milestones/${editingMilestone.id}`, {
      method: 'PATCH',
      body: JSON.stringify({
        name: editingMilestone.name,
        due_date: editingMilestone.due_date || null,
        status: editingMilestone.status
      })
    });
    setEditingMilestone(null);
    await reloadProject();
  };

  const allocateEquipment = async (taskId: number) => {
    const equipmentId = resourceSelection[taskId];
    if (!equipmentId) return;
    await apiFetch(`/api/v1/equipment/${equipmentId}/allocation`, {
      method: 'PATCH',
      body: JSON.stringify({ task_id: taskId })
    });
    await reloadProject();
  };

  if (loading) {
    return <div className="p-8">Loading project details...</div>;
  }

  if (!projectData) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <p className="text-lg font-bold">Project not found</p>
        <Link href="/projects"><Button variant="outline">Back to Projects</Button></Link>
      </div>
    );
  }

  const { tasks: projectTasks, milestones: projectMilestones } = projectData;

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      <Link href="/projects" className="mb-4 flex items-center gap-2 text-sm font-bold text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to Projects
      </Link>

      <PageHeader
        title={projectData.name}
        description={projectData.site_name || 'No site assigned'}
        action={
          <div className="flex items-center gap-2">
            <StatusBadge status={projectData.status} />
            {role === 'admin' && projectData.status !== 'archived' && (
              <>
                <Button size="sm" variant="outline" onClick={() => { setEditName(projectData.name); setEditBudget(String(projectData.budget_allocated)); setEditing(true); }}>Edit</Button>
                <Button size="sm" variant="destructive" onClick={archiveProject}>Archive</Button>
              </>
            )}
          </div>
        }
      />

      {/* ── Schedule Risk Alert Banner ────────────────────────────────────────── */}
      {scheduleHealth && scheduleHealth.risk_level !== 'on_track' && (
        <div className={`mb-6 p-4 rounded-lg border flex items-start gap-3 shadow-sm transition-all duration-300 ${
          scheduleHealth.risk_level === 'critical'
            ? 'bg-rose-50 border-rose-200 text-rose-900 dark:bg-rose-950/20 dark:border-rose-900/50 dark:text-rose-300'
            : 'bg-amber-50 border-amber-200 text-amber-900 dark:bg-amber-950/20 dark:border-amber-900/50 dark:text-amber-300'
        }`}>
          <AlertTriangle className={`h-5 w-5 shrink-0 mt-0.5 ${
            scheduleHealth.risk_level === 'critical' ? 'text-rose-600' : 'text-amber-600'
          }`} />
          <div className="flex-1">
            <h4 className="font-bold text-sm">
              {scheduleHealth.risk_level === 'critical' ? 'Schedule Risk Warning (CRITICAL)' : 'Schedule Drift Alert'}
            </h4>
            <p className="text-xs mt-1 leading-relaxed opacity-90">
              This project is currently flagged at <strong>{scheduleHealth.risk_level.toUpperCase()}</strong> risk.
              There are {scheduleHealth.overdue_task_count} overdue tasks, {scheduleHealth.delayed_task_count} delayed tasks,
              and {scheduleHealth.missed_milestone_count} missed milestones.
              Please check task dependencies and coordinate updates with contractors immediately.
            </p>
          </div>
        </div>
      )}

      {editing && role === 'admin' && (
        <Card className="mb-6">
          <CardHeader><CardTitle className="text-lg">Edit Project</CardTitle></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <input className="h-10 flex-1 rounded-sm border-2 border-border bg-card px-3 text-sm" value={editName} onChange={(event) => setEditName(event.target.value)} />
            <input className="h-10 w-full rounded-sm border-2 border-border bg-card px-3 text-sm sm:w-48" type="number" min="0" value={editBudget} onChange={(event) => setEditBudget(event.target.value)} />
            <select className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" value={projectData.site_id} onChange={(event) => setProjectData({ ...projectData, site_id: Number(event.target.value) })}>{sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}</select>
            <select className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" value={projectData.pm_id || ''} onChange={(event) => setProjectData({ ...projectData, pm_id: Number(event.target.value) })}>{pms.map((pm) => <option key={pm.id} value={pm.id}>{pm.name}</option>)}</select>
            <input className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" type="date" value={projectData.start_date || ''} onChange={(event) => setProjectData({ ...projectData, start_date: event.target.value })} />
            <input className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" type="date" value={projectData.end_date || ''} onChange={(event) => setProjectData({ ...projectData, end_date: event.target.value })} />
            <select className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" value={projectData.status} onChange={(event) => setProjectData({ ...projectData, status: event.target.value })}><option value="planning">Planning</option><option value="in_progress">In progress</option><option value="on_hold">On hold</option><option value="completed">Completed</option></select>
            <Button onClick={saveProject}>Save</Button>
            <Button variant="outline" onClick={() => setEditing(false)}>Cancel</Button>
          </CardContent>
        </Card>
      )}

      {(role === 'admin' || role === 'pm') && (
        <Card className="mb-6">
          <CardHeader><CardTitle className="text-lg">Manage Project Dates</CardTitle></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            <input className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" type="date" value={projectData.start_date || ''} onChange={(event) => setProjectData({ ...projectData, start_date: event.target.value })} />
            <input className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" type="date" value={projectData.end_date || ''} onChange={(event) => setProjectData({ ...projectData, end_date: event.target.value })} />
            <div className="flex gap-2">
              <select className="h-10 flex-1 rounded-sm border-2 border-border bg-card px-3 text-sm" value={projectData.status} onChange={(event) => setProjectData({ ...projectData, status: event.target.value })}>
                <option value="planning">Planning</option>
                <option value="in_progress">In progress</option>
                <option value="on_hold">On hold</option>
                <option value="completed">Completed</option>
              </select>
              <Button onClick={saveSchedule}>Save Schedule</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Key Metrics Cards Row ────────────────────────────────────────── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Budget</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-display text-xl font-extrabold">{formatCurrency(projectData.budget_total)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-display text-xl font-extrabold">{projectData.progress_percent}%</div>
            <div className="mt-1 h-3 border-2 border-border bg-secondary">
              <div className="h-full bg-primary" style={{ width: `${projectData.progress_percent}%` }} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">Start Date</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-display text-lg font-extrabold">{formatDate(projectData.start_date)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">End Date</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-display text-lg font-extrabold">{formatDate(projectData.end_date)}</div>
          </CardContent>
        </Card>
      </div>

      {/* ── Tabbed View Switcher ────────────────────────────────────────── */}
      <div className="flex border-b mb-6 gap-2">
        <button
          onClick={() => setActiveTab('list')}
          className={`pb-2.5 px-4 text-sm font-bold border-b-2 transition ${
            activeTab === 'list' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Tasks & Milestones List
        </button>
        <button
          onClick={() => setActiveTab('gantt')}
          className={`pb-2.5 px-4 text-sm font-bold border-b-2 transition ${
            activeTab === 'gantt' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Gantt Timeline Chart
        </button>
      </div>

      {activeTab === 'gantt' ? (
        <div className="mb-8">
          <GanttChart projectId={projectId} />
        </div>
      ) : (
        <div className="space-y-6">
          {(role === 'admin' || role === 'pm') && (
            <Card>
              <CardHeader><CardTitle>Manage Tasks</CardTitle></CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <input className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" placeholder="Task name" value={taskForm.name} onChange={(event) => setTaskForm({ ...taskForm, name: event.target.value })} />
                <input className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" placeholder="Description" value={taskForm.description} onChange={(event) => setTaskForm({ ...taskForm, description: event.target.value })} />
                <select className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" value={taskForm.priority} onChange={(event) => setTaskForm({ ...taskForm, priority: event.target.value })}><option value="low">Low priority</option><option value="medium">Medium priority</option><option value="high">High priority</option><option value="critical">Critical priority</option></select>
                <select className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" value={taskForm.assigned_to} onChange={(event) => setTaskForm({ ...taskForm, assigned_to: event.target.value })}><option value="">Unassigned</option>{(siteData?.contractors || []).filter((person: any) => person.specialty.toLowerCase() === 'contractor').map((person: any) => <option key={person.id} value={person.id}>{person.name}</option>)}</select>
                <input className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" type="date" value={taskForm.start_date} onChange={(event) => setTaskForm({ ...taskForm, start_date: event.target.value })} />
                <input className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" type="date" value={taskForm.end_date} onChange={(event) => setTaskForm({ ...taskForm, end_date: event.target.value })} />
                <select className="h-10 rounded-sm border-2 border-border bg-card px-3 text-sm" value={taskForm.depends_on_task_id} onChange={(event) => setTaskForm({ ...taskForm, depends_on_task_id: event.target.value })}><option value="">No dependency</option>{projectTasks.map((task: any) => <option key={task.id} value={task.id}>{task.name}</option>)}</select>
                <Button onClick={createTask} disabled={!taskForm.name.trim()}>Create Task</Button>
              </CardContent>
            </Card>
          )}

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Tasks */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><FolderKanban className="h-5 w-5" /> Tasks</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {projectTasks.map((task: any) => {
                  const dep = task.depends_on_task_id
                    ? projectTasks.find((t: any) => t.id === task.depends_on_task_id)
                    : null;
                  return (
                    <div key={task.id} className="border-2 border-border bg-secondary px-3 py-2.5 rounded-sm">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start gap-2">
                          {task.status === 'completed' ? (
                            <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                          ) : task.status === 'delayed' ? (
                            <AlertCircle className="h-4 w-4 text-destructive mt-0.5 shrink-0" />
                          ) : (
                            <Circle className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                          )}
                          <div>
                            <p className="font-bold text-sm">{task.name}</p>
                            <p className="text-xs text-muted-foreground font-medium mt-0.5">{task.description}</p>
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          <StatusBadge status={task.status} />
                          <span className="text-[10px] font-bold uppercase text-muted-foreground">{task.priority}</span>
                        </div>
                      </div>
                      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs font-medium text-muted-foreground">
                        <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(task.start_date)} - {formatDate(task.end_date)}</span>
                        {dep && <span className="text-rose-600 dark:text-rose-400">Depends on: {dep.name}</span>}
                        {task.assigned_to_name && <span>Assigned to: {task.assigned_to_name}</span>}
                      </div>
                      {role === 'contractor' && (
                        <div className="mt-3 flex flex-wrap items-center gap-2 border-t-2 border-border pt-2">
                          <input className="h-8 w-20 rounded-sm border-2 border-border bg-card px-2 text-xs" type="number" min="0" max="100" defaultValue={task.progress_percent} onBlur={(event) => updateTask(task, { progress_percent: Number(event.target.value) })} />
                          <Button size="sm" onClick={() => updateTask(task, { status: 'in_progress' })}>In Progress</Button>
                          <Button size="sm" variant="outline" onClick={() => updateTask(task, { status: 'delayed' })}>Report Delay</Button>
                          <Button size="sm" variant="outline" onClick={() => updateTask(task, { status: 'completed', progress_percent: 100 })}>Completed</Button>
                        </div>
                      )}
                      {(role === 'admin' || role === 'pm') && (
                        <div className="mt-3 grid gap-2 border-t-2 border-border pt-2 sm:grid-cols-2 lg:grid-cols-5">
                          <input className="h-8 rounded-sm border-2 border-border bg-card px-2 text-xs" defaultValue={task.name} onBlur={(event) => event.target.value !== task.name && updateTask(task, { name: event.target.value })} />
                          <input className="h-8 rounded-sm border-2 border-border bg-card px-2 text-xs" defaultValue={task.description || ''} placeholder="Description" onBlur={(event) => event.target.value !== (task.description || '') && updateTask(task, { description: event.target.value })} />
                          <select className="h-8 rounded-sm border-2 border-border bg-card px-2 text-xs" value={task.status} onChange={(event) => updateTask(task, { status: event.target.value })}><option value="not_started">Not started</option><option value="in_progress">In progress</option><option value="delayed">Delayed</option><option value="completed">Completed</option></select>
                          <select className="h-8 rounded-sm border-2 border-border bg-card px-2 text-xs" value={task.priority} onChange={(event) => updateTask(task, { priority: event.target.value })}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select>
                          <input className="h-8 rounded-sm border-2 border-border bg-card px-2 text-xs" type="number" min="0" max="100" defaultValue={task.progress_percent} onBlur={(event) => updateTask(task, { progress_percent: Number(event.target.value) })} />
                          <select className="h-8 rounded-sm border-2 border-border bg-card px-2 text-xs" value={task.assigned_to || ''} onChange={(event) => updateTask(task, { assigned_to: event.target.value ? Number(event.target.value) : null })}><option value="">Unassigned</option>{(siteData?.contractors || []).filter((person: any) => person.specialty.toLowerCase() === 'contractor').map((person: any) => <option key={person.id} value={person.id}>{person.name}</option>)}</select>
                          <select className="h-8 rounded-sm border-2 border-border bg-card px-2 text-xs" value={task.depends_on_task_id || ''} onChange={(event) => updateTask(task, { depends_on_task_id: event.target.value ? Number(event.target.value) : null })}><option value="">No dependency</option>{projectTasks.filter((other: any) => other.id !== task.id).map((other: any) => <option key={other.id} value={other.id}>{other.name}</option>)}</select>
                          <input className="h-8 rounded-sm border-2 border-border bg-card px-2 text-xs" type="date" defaultValue={task.start_date || ''} onBlur={(event) => updateTask(task, { start_date: event.target.value || null })} />
                          <input className="h-8 rounded-sm border-2 border-border bg-card px-2 text-xs" type="date" defaultValue={task.end_date || ''} onBlur={(event) => updateTask(task, { end_date: event.target.value || null })} />
                          <select className="h-8 rounded-sm border-2 border-border bg-card px-2 text-xs" value={resourceSelection[task.id] || ''} onChange={(event) => setResourceSelection({ ...resourceSelection, [task.id]: event.target.value })}><option value="">Assign equipment</option>{(siteData?.equipment || []).map((equipment: any) => <option key={equipment.id} value={equipment.id}>{equipment.name}</option>)}</select>
                          <Button size="sm" onClick={() => allocateEquipment(task.id)} disabled={!resourceSelection[task.id]}>Allocate Resource</Button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            {/* Milestones */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Flag className="h-5 w-5" /> Milestones</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {(role === 'admin' || role === 'pm') && <div className="mb-4 grid gap-2 sm:grid-cols-3"><input className="h-9 rounded-sm border-2 border-border bg-card px-2 text-sm" placeholder="Milestone name" value={milestoneForm.name} onChange={(event) => setMilestoneForm({ ...milestoneForm, name: event.target.value })} /><input className="h-9 rounded-sm border-2 border-border bg-card px-2 text-sm" type="date" value={milestoneForm.due_date} onChange={(event) => setMilestoneForm({ ...milestoneForm, due_date: event.target.value })} /><Button onClick={createMilestone} disabled={!milestoneForm.name.trim()}>Create Milestone</Button></div>}
                {editingMilestone && <div className="mb-4 grid gap-2 border-2 border-border p-2 sm:grid-cols-4"><input className="h-9 rounded-sm border-2 border-border bg-card px-2 text-sm" value={editingMilestone.name} onChange={(event) => setEditingMilestone({ ...editingMilestone, name: event.target.value })} /><input className="h-9 rounded-sm border-2 border-border bg-card px-2 text-sm" type="date" value={editingMilestone.due_date || ''} onChange={(event) => setEditingMilestone({ ...editingMilestone, due_date: event.target.value })} /><select className="h-9 rounded-sm border-2 border-border bg-card px-2 text-xs" value={editingMilestone.status} onChange={(event) => setEditingMilestone({ ...editingMilestone, status: event.target.value })}><option value="upcoming">Upcoming</option><option value="achieved">Achieved</option><option value="missed">Missed</option></select><Button onClick={saveMilestone}>Save Milestone</Button></div>}
                {projectMilestones.map((ms: any) => (
                  <div key={ms.id} className="flex items-center justify-between border-2 border-border bg-secondary px-3 py-2.5 rounded-sm">
                    <div className="flex items-center gap-2">
                      <div className={`flex h-8 w-8 items-center justify-center border-2 border-border ${
                        ms.status === 'achieved' ? 'bg-green-500 text-white' :
                        ms.status === 'missed' ? 'bg-destructive text-destructive-foreground' :
                        'bg-blue-500 text-white'
                      }`}>
                        <Flag className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="font-bold text-sm">{ms.name}</p>
                        <p className="text-xs text-muted-foreground font-medium">Due {formatDate(ms.due_date)}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2"><StatusBadge status={ms.status} />{(role === 'admin' || role === 'pm') && <Button size="sm" variant="outline" onClick={() => setEditingMilestone({ ...ms })}>Edit</Button>}</div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
