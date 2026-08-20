'use client';

import Link from 'next/link';
import { FolderKanban, ArrowRight, Calendar, Wallet } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { projects, sites, getTasksByProject, getMilestonesByProject } from '@/lib/mock-data';
import { formatCurrency, formatDate } from '@/lib/types';

export default function ProjectsListPage() {
  return (
    <div>
      <PageHeader title="Projects" description="All construction projects across your sites" />

      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => {
          const site = sites.find((s) => s.id === project.site_id);
          const projectTasks = getTasksByProject(project.id);
          const projectMilestones = getMilestonesByProject(project.id);
          const completedTasks = projectTasks.filter((t) => t.status === 'completed').length;

          return (
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
                        <p className="text-xs text-muted-foreground font-medium">{site?.name}</p>
                      </div>
                    </div>
                    <StatusBadge status={project.status} />
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-3 gap-2">
                    <div className="border-2 border-border bg-secondary px-2 py-1.5 text-center">
                      <div className="font-display text-lg font-extrabold">{projectTasks.length}</div>
                      <div className="text-[10px] font-bold uppercase text-muted-foreground">Tasks</div>
                    </div>
                    <div className="border-2 border-border bg-secondary px-2 py-1.5 text-center">
                      <div className="font-display text-lg font-extrabold">{completedTasks}</div>
                      <div className="text-[10px] font-bold uppercase text-muted-foreground">Done</div>
                    </div>
                    <div className="border-2 border-border bg-secondary px-2 py-1.5 text-center">
                      <div className="font-display text-lg font-extrabold">{projectMilestones.length}</div>
                      <div className="text-[10px] font-bold uppercase text-muted-foreground">Miles.</div>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold uppercase text-muted-foreground">Progress</span>
                      <span className="text-xs font-extrabold">{project.progress_percent}%</span>
                    </div>
                    <div className="h-3 border-2 border-border bg-secondary">
                      <div className="h-full bg-primary transition-all" style={{ width: `${project.progress_percent}%` }} />
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
                    <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(project.end_date)}</span>
                    <span className="flex items-center gap-1"><Wallet className="h-3 w-3" />{formatCurrency(project.budget_total)}</span>
                  </div>
                  <div className="flex items-center justify-end gap-1 text-sm font-bold text-primary">
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
