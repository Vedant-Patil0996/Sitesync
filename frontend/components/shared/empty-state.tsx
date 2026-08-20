'use client';

import { cn } from '@/lib/utils';

interface EmptyStateProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3 border-2 border-dashed border-border bg-card p-12 text-center', className)}>
      <div className="flex h-16 w-16 items-center justify-center border-2 border-border bg-secondary shadow-brutal-sm">
        <Icon className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="font-display text-lg font-extrabold">{title}</h3>
      {description && <p className="max-w-md text-sm text-muted-foreground font-medium">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
