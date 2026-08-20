'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, FolderKanban, CheckCircle2, Circle, AlertCircle, Calendar, Flag } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import {
  projects, sites, getTasksByProject, getMilestonesByProject,
} from '@/lib/mock-data';
import { formatCurrency, formatDate } from '@/lib/types';

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.projectId as string;
  const project = projects.find((p) => p.id === projectId);

  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <p className="text-lg font-bold">Project not found</p>
        <Link href="/projects"><Button variant="outline">Back to Projects</Button></Link>
      </div>
    );
  }

  const site = sites.find((s) => s.id === project.site_id);
  const projectTasks = getTasksByProject(project.id);
  const projectMilestones = getMilestonesByProject(project.id);

  return (
    <div>
      <Link href="/projects" className="mb-4 flex items-center gap-2 text-sm font-bold text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to Projects
      </Link>

      <PageHeader
        title={project.name}
        description={`${site?.name} - ${site?.location_text}`}
        action={<StatusBadge status={project.status} />}
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold uppercase text-muted-foreground">Budget</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-display text-xl font-extrabold">{formatCurrency(project.budget_total)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold uppercase text-muted-foreground">Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-display text-xl font-extrabold">{project.progress_percent}%</div>
            <div className="mt-1 h-3 border-2 border-border bg-secondary">
              <div className="h-full bg-primary" style={{ width: `${project.progress_percent}%` }} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold uppercase text-muted-foreground">Start Date</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-display text-lg font-extrabold">{formatDate(project.start_date)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold uppercase text-muted-foreground">End Date</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-display text-lg font-extrabold">{formatDate(project.end_date)}</div>
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
            {projectTasks.map((task) => {
              const dep = task.depends_on_task_id
                ? projectTasks.find((t) => t.id === task.depends_on_task_id)
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
                    {dep && <span className="text-amber-600">Depends on: {dep.name}</span>}
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
            {projectMilestones.map((ms) => (
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
