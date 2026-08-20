'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, FolderKanban, CheckCircle2, Circle, AlertCircle, Calendar, Flag } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { formatCurrency, formatDate } from '@/lib/types';
import { apiFetch } from '@/lib/api';

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.projectId as string;
  const [projectData, setProjectData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchProject() {
      try {
        const data = await apiFetch<any>(`/api/v1/projects/${projectId}`);
        setProjectData(data);
      } catch (error) {
        console.error('Failed to load project details', error);
      } finally {
        setLoading(false);
      }
    }
    fetchProject();
  }, [projectId]);

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
    <div>
      <Link href="/projects" className="mb-4 flex items-center gap-2 text-sm font-bold text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to Projects
      </Link>

      <PageHeader
        title={projectData.name}
        description={projectData.site_name || 'No site assigned'}
        action={<StatusBadge status={projectData.status} />}
      />

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
                <div key={task.id} className="border-2 border-border bg-secondary px-3 py-2.5">
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
                    <StatusBadge status={task.status} />
                  </div>
                  <div className="mt-2 flex items-center gap-3 text-xs font-medium text-muted-foreground">
                    <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(task.start_date)} - {formatDate(task.end_date)}</span>
                    {dep && <span className="text-mahogany">Depends on: {dep.name}</span>}
                  </div>
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
            {projectMilestones.map((ms: any) => (
              <div key={ms.id} className="flex items-center justify-between border-2 border-border bg-secondary px-3 py-2.5">
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
                <StatusBadge status={ms.status} />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
