'use client';

import { useEffect, useState, useRef } from 'react';
import { apiFetch } from '@/lib/api';
import { Calendar, AlertTriangle, ArrowRight, User } from 'lucide-react';
import { formatDate } from '@/lib/types';

interface GanttTask {
  id: number;
  name: string;
  description?: string;
  status: string;
  priority: string;
  start_date: string | null;
  end_date: string | null;
  progress_percent: number;
  depends_on_task_id: number | null;
  assigned_to_name: string | null;
  days_overdue: number;
  is_on_critical_path: boolean;
}

interface GanttMilestone {
  id: number;
  name: string;
  due_date: string | null;
  status: string;
}

interface GanttData {
  project_id: number;
  project_name: string;
  project_start: string | null;
  project_end: string | null;
  project_status: string;
  tasks: GanttTask[];
  milestones: GanttMilestone[];
}

export default function GanttChart({ projectId }: { projectId: string }) {
  const [data, setData] = useState<GanttData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'days' | 'weeks'>('days');
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadGantt() {
      try {
        const result = await apiFetch<GanttData>(`/api/v1/projects/${projectId}/gantt`);
        setData(result);
      } catch (err: any) {
        setError(err.message || 'Failed to load Gantt chart data');
      } finally {
        setLoading(false);
      }
    }
    loadGantt();
  }, [projectId]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
        <span className="ml-2 text-sm text-muted-foreground">Loading Gantt timeline...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-lg border-2 border-destructive/20 bg-destructive/5 p-4 text-center text-destructive">
        <AlertTriangle className="mx-auto h-8 w-8 mb-2" />
        <p className="font-semibold">Failed to load schedule visualization</p>
        <p className="text-xs mt-1 text-muted-foreground">{error}</p>
      </div>
    );
  }

  // ── Calculate Timeline Boundaries ──────────────────────────────────────────
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let minDate = new Date(today);
  minDate.setDate(minDate.getDate() - 7); // Default start: 7 days ago
  let maxDate = new Date(today);
  maxDate.setDate(maxDate.getDate() + 30); // Default end: 30 days out

  const allDates: Date[] = [];
  const parseAndAdd = (dStr: string | null) => {
    if (!dStr) return;
    const d = new Date(dStr);
    if (!isNaN(d.getTime())) {
      allDates.push(d);
    }
  };

  parseAndAdd(data.project_start);
  parseAndAdd(data.project_end);
  data.tasks.forEach((t) => {
    parseAndAdd(t.start_date);
    parseAndAdd(t.end_date);
  });
  data.milestones.forEach((m) => {
    parseAndAdd(m.due_date);
  });

  if (allDates.length > 0) {
    const dates = allDates.map((d) => d.getTime());
    minDate = new Date(Math.min(...dates));
    maxDate = new Date(Math.max(...dates));
    // Pad boundaries by 5 days on each end
    minDate.setDate(minDate.getDate() - 5);
    maxDate.setDate(maxDate.getDate() + 10);
  }

  // Reset hours for date comparison integrity
  minDate.setHours(0, 0, 0, 0);
  maxDate.setHours(0, 0, 0, 0);

  const totalDays = Math.ceil((maxDate.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24));
  const dayWidth = viewMode === 'days' ? 44 : 12; // Width in px for 1 day
  const rowHeight = 56; // Row height in px
  const gridWidth = totalDays * dayWidth;

  // Generate Date Headers
  const dateHeaders: { label: string; offset: number; date: Date }[] = [];
  const currentHeaderDate = new Date(minDate);
  for (let i = 0; i < totalDays; i++) {
    dateHeaders.push({
      label: currentHeaderDate.getDate().toString(),
      offset: i * dayWidth,
      date: new Date(currentHeaderDate),
    });
    currentHeaderDate.setDate(currentHeaderDate.getDate() + 1);
  }

  // Generate Month Headers
  const monthHeaders: { label: string; width: number; offset: number }[] = [];
  let currentMonthIndex = -1;
  let currentMonthWidth = 0;
  let currentMonthOffset = 0;

  dateHeaders.forEach((dh, index) => {
    const monthKey = dh.date.toLocaleDateString('default', { month: 'short', year: '2-digit' });
    if (index === 0) {
      currentMonthIndex = dh.date.getMonth();
      currentMonthOffset = 0;
      currentMonthWidth = dayWidth;
    } else if (dh.date.getMonth() !== currentMonthIndex) {
      monthHeaders.push({
        label: new Date(dh.date.getFullYear(), currentMonthIndex, 1).toLocaleDateString('default', { month: 'long', year: 'numeric' }),
        width: currentMonthWidth,
        offset: currentMonthOffset,
      });
      currentMonthIndex = dh.date.getMonth();
      currentMonthOffset = index * dayWidth;
      currentMonthWidth = dayWidth;
    } else {
      currentMonthWidth += dayWidth;
    }
    if (index === dateHeaders.length - 1) {
      monthHeaders.push({
        label: dh.date.toLocaleDateString('default', { month: 'long', year: 'numeric' }),
        width: currentMonthWidth,
        offset: currentMonthOffset,
      });
    }
  });

  // Calculate coordinates for a task bar
  const getTaskCoords = (t: GanttTask) => {
    if (!t.start_date || !t.end_date) return null;
    const start = new Date(t.start_date);
    const end = new Date(t.end_date);
    start.setHours(0, 0, 0, 0);
    end.setHours(0, 0, 0, 0);

    const startOffsetDays = Math.max(0, Math.ceil((start.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24)));
    const durationDays = Math.max(1, Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1);

    return {
      x: startOffsetDays * dayWidth,
      width: durationDays * dayWidth,
    };
  };

  // Calculate coordinates for a milestone diamond
  const getMilestoneCoords = (m: GanttMilestone) => {
    if (!m.due_date) return null;
    const due = new Date(m.due_date);
    due.setHours(0, 0, 0, 0);
    const offsetDays = Math.ceil((due.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24));
    return offsetDays * dayWidth;
  };

  // Today marker offset
  const todayOffset = Math.ceil((today.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24)) * dayWidth;

  // Task index map for drawing connection lines
  const taskIndexMap = new Map<number, number>();
  data.tasks.forEach((t, i) => taskIndexMap.set(t.id, i));

  // Determine Task Bar Color
  const getTaskColorClass = (t: GanttTask) => {
    if (t.status === 'completed') return 'bg-emerald-500 border-emerald-600 dark:bg-emerald-600';
    if (t.status === 'delayed') return 'bg-rose-500 border-rose-600 dark:bg-rose-600 animate-pulse';
    if (t.status === 'in_progress') return 'bg-amber-500 border-amber-600 dark:bg-amber-600';
    return 'bg-slate-300 border-slate-400 text-slate-700 dark:bg-slate-700 dark:border-slate-600';
  };

  const getPriorityBadge = (priority: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300',
      high: 'bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300',
      medium: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
      low: 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300',
    };
    return colors[priority] || colors.medium;
  };

  return (
    <div className="flex flex-col rounded-lg border bg-card text-card-foreground shadow-sm overflow-hidden">
      {/* Chart Control Bar */}
      <div className="flex flex-wrap items-center justify-between border-b bg-muted/30 px-4 py-3 gap-2">
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-primary" />
          <span className="font-semibold text-sm">Gantt Timeline Schedule</span>
          <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
            {data.tasks.length} Tasks
          </span>
        </div>
        <div className="flex items-center gap-1.5 bg-background border rounded-md p-1">
          <button
            onClick={() => setViewMode('days')}
            className={`px-3 py-1 text-xs font-medium rounded-sm transition ${
              viewMode === 'days' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted text-muted-foreground'
            }`}
          >
            Day View
          </button>
          <button
            onClick={() => setViewMode('weeks')}
            className={`px-3 py-1 text-xs font-medium rounded-sm transition ${
              viewMode === 'weeks' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted text-muted-foreground'
            }`}
          >
            Compact View
          </button>
        </div>
      </div>

      {/* Main Gantt Grid Container */}
      <div className="flex overflow-hidden relative">
        {/* Left Side: Tasks Table List (Sticky Left Pane) */}
        <div className="w-[280px] sm:w-[320px] shrink-0 border-r bg-card z-10 select-none">
          {/* Top headers aligned with timeline */}
          <div className="h-[76px] border-b bg-muted/40 flex items-end px-3 pb-2.5">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Task / Assigned To</span>
          </div>
          <div className="divide-y">
            {data.tasks.map((task) => (
              <div key={task.id} className="h-[56px] flex flex-col justify-center px-3 hover:bg-muted/30 group">
                <div className="flex items-center justify-between gap-1">
                  <span className="text-sm font-medium truncate text-card-foreground group-hover:text-primary transition" title={task.name}>
                    {task.name}
                  </span>
                  {task.days_overdue > 0 && (
                    <span className="shrink-0 bg-red-100 text-red-800 text-[10px] font-bold px-1.5 py-0.5 rounded dark:bg-red-950 dark:text-red-400">
                      {task.days_overdue}d over
                    </span>
                  )}
                </div>
                <div className="flex items-center justify-between mt-0.5 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <User className="h-3 w-3 shrink-0" />
                    <span className="truncate max-w-[100px]">
                      {task.assigned_to_name || 'Unassigned'}
                    </span>
                  </div>
                  <span className={`text-[10px] font-semibold uppercase px-1 rounded ${getPriorityBadge(task.priority)}`}>
                    {task.priority}
                  </span>
                </div>
              </div>
            ))}
            {/* Row for milestones */}
            {data.milestones.length > 0 && (
              <div className="bg-muted/10 h-10 flex items-center px-3">
                <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Milestones</span>
              </div>
            )}
            {data.milestones.map((ms) => (
              <div key={ms.id} className="h-12 flex flex-col justify-center px-3 hover:bg-muted/20">
                <span className="text-sm font-medium truncate text-card-foreground" title={ms.name}>
                  ♦ {ms.name}
                </span>
                <span className="text-xs text-muted-foreground">{ms.due_date ? formatDate(ms.due_date) : 'No Date'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right Side: Horizontal Scrolling Timeline Grid */}
        <div ref={scrollContainerRef} className="grow overflow-x-auto select-none bg-card relative">
          <div style={{ width: `${gridWidth}px` }} className="relative">
            {/* 1. Timeline Month + Day Headers */}
            <div className="h-[76px] border-b relative sticky top-0 bg-card z-20">
              {/* Month Header Row */}
              <div className="h-[38px] border-b flex bg-muted/20">
                {monthHeaders.map((mh, idx) => (
                  <div
                    key={idx}
                    style={{ width: `${mh.width}px` }}
                    className="h-full border-r shrink-0 flex items-center justify-center text-xs font-semibold text-muted-foreground bg-muted/10 border-muted-foreground/10 px-2 truncate"
                  >
                    {mh.label}
                  </div>
                ))}
              </div>
              {/* Day Header Row */}
              <div className="h-[38px] flex relative bg-muted/5">
                {dateHeaders.map((dh, idx) => {
                  const isToday = dh.date.toDateString() === today.toDateString();
                  return (
                    <div
                      key={idx}
                      style={{ width: `${dayWidth}px` }}
                      className={`h-full border-r shrink-0 flex flex-col items-center justify-center text-[10px] font-medium border-muted-foreground/10 ${
                        isToday ? 'bg-red-500/10 font-bold text-red-600' : 'text-muted-foreground'
                      }`}
                    >
                      {viewMode === 'days' ? (
                        <>
                          <span>{dh.date.toLocaleDateString('default', { weekday: 'narrow' })}</span>
                          <span>{dh.label}</span>
                        </>
                      ) : (
                        idx % 7 === 0 && <span>{dh.label}</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 2. Grid vertical division lines */}
            <div className="absolute inset-y-0 pointer-events-none z-0">
              {dateHeaders.map((dh, idx) => (
                <div
                  key={idx}
                  style={{ left: `${dh.offset}px`, width: `${dayWidth}px` }}
                  className="absolute top-[76px] bottom-0 border-r border-muted-foreground/5"
                />
              ))}
            </div>

            {/* 3. Today timeline marker */}
            {todayOffset >= 0 && todayOffset <= gridWidth && (
              <div
                style={{ left: `${todayOffset}px` }}
                className="absolute top-0 bottom-0 w-0.5 bg-rose-500 z-10 pointer-events-none"
              >
                <div className="bg-rose-500 text-white text-[8px] font-extrabold px-1 rounded-sm absolute -left-4 top-1 shadow-sm uppercase tracking-wider">
                  Today
                </div>
              </div>
            )}

            {/* 4. SVGs Connections Canvas (drawn under bars) */}
            <svg
              style={{ width: `${gridWidth}px`, height: `${data.tasks.length * rowHeight}px` }}
              className="absolute top-[76px] left-0 pointer-events-none z-10"
            >
              <defs>
                <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 2 L 8 5 L 0 8 z" fill="#94a3b8" />
                </marker>
                <marker id="arrow-critical" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 2 L 8 5 L 0 8 z" fill="#ef4444" />
                </marker>
              </defs>

              {data.tasks.map((task, idx) => {
                if (task.depends_on_task_id === null) return null;
                const parentIdx = taskIndexMap.get(task.depends_on_task_id);
                if (parentIdx === undefined) return null;

                const parentTask = data.tasks[parentIdx];
                const parentCoords = getTaskCoords(parentTask);
                const childCoords = getTaskCoords(task);

                if (!parentCoords || !childCoords) return null;

                // Parent end point and Child start point
                const parentX = parentCoords.x + parentCoords.width;
                const parentY = parentIdx * rowHeight + rowHeight / 2;
                const childX = childCoords.x;
                const childY = idx * rowHeight + rowHeight / 2;

                const isCriticalLink = parentTask.is_on_critical_path || task.is_on_critical_path;
                const strokeColor = isCriticalLink ? '#ef4444' : '#cbd5e1';
                const markerId = isCriticalLink ? 'url(#arrow-critical)' : 'url(#arrow)';

                // Draw a nice elbow routing line
                const midX = parentX + (childX - parentX) / 2;

                return (
                  <path
                    key={`dep-${task.id}`}
                    d={`M ${parentX} ${parentY} L ${midX} ${parentY} L ${midX} ${childY} L ${childX} ${childY}`}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth={isCriticalLink ? 2 : 1.5}
                    markerEnd={markerId}
                    strokeDasharray={isCriticalLink ? 'none' : '4 3'}
                  />
                );
              })}
            </svg>

            {/* 5. Right timeline row container */}
            <div className="divide-y relative z-10">
              {data.tasks.map((task, idx) => {
                const coords = getTaskCoords(task);
                const hasDates = coords !== null;

                return (
                  <div key={task.id} className="h-[56px] flex items-center relative hover:bg-muted/10">
                    {hasDates && coords ? (
                      <div
                        style={{
                          left: `${coords.x}px`,
                          width: `${coords.width}px`,
                        }}
                        className={`absolute h-8 rounded-md border flex items-center justify-between px-2 overflow-hidden shadow-sm transition hover:shadow group ${getTaskColorClass(task)}`}
                      >
                        {/* Task Progress fill */}
                        <div
                          style={{ width: `${task.progress_percent}%` }}
                          className="absolute inset-y-0 left-0 bg-black/10 dark:bg-white/10 z-0 pointer-events-none"
                        />
                        {/* Task text inside bar */}
                        <span className="text-xs font-bold text-white z-10 truncate drop-shadow-sm select-none pr-1">
                          {task.progress_percent > 0 ? `${Math.round(task.progress_percent)}%` : ''}
                        </span>
                        {task.is_on_critical_path && (
                          <span className="shrink-0 text-red-100 font-extrabold text-[9px] border border-red-200 bg-red-600 px-1 py-0.5 rounded z-10 animate-pulse">
                            CRITICAL
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-xs italic text-muted-foreground pl-4">No dates set (Scheduling required)</span>
                    )}
                  </div>
                );
              })}

              {/* Milestones grid row */}
              {data.milestones.length > 0 && (
                <div className="bg-muted/10 h-10" />
              )}
              {data.milestones.map((ms) => {
                const x = getMilestoneCoords(ms);
                const hasDate = x !== null;
                const isMissed = ms.status === 'missed';

                return (
                  <div key={ms.id} className="h-12 flex items-center relative hover:bg-muted/10">
                    {hasDate && x !== null && (
                      <div
                        style={{ left: `${x - 8}px` }}
                        className={`absolute flex flex-col items-center justify-center cursor-default z-10`}
                      >
                        {/* Milestone Diamond */}
                        <div
                          className={`h-4 w-4 rotate-45 border-2 shadow-sm ${
                            isMissed
                              ? 'bg-rose-500 border-rose-700 animate-bounce'
                              : ms.status === 'achieved'
                              ? 'bg-emerald-500 border-emerald-700'
                              : 'bg-primary border-primary-foreground'
                          }`}
                          title={`${ms.name} (${ms.due_date})`}
                        />
                        <span className="text-[9px] font-bold mt-1 text-card-foreground bg-background px-1 rounded shadow-sm border truncate max-w-[80px]">
                          {ms.name}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
