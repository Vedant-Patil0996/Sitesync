'use client';

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

const STATUS_VARIANTS: Record<string, string> = {
  active: 'bg-green-100 text-green-800 border-green-800 dark:bg-green-900 dark:text-green-200 dark:border-green-200',
  on_hold: 'bg-amber-100 text-amber-800 border-amber-800 dark:bg-amber-900 dark:text-amber-200 dark:border-amber-200',
  completed: 'bg-blue-100 text-blue-800 border-blue-800 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-200',
  planning: 'bg-blue-100 text-blue-800 border-blue-800 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-200',
  in_progress: 'bg-amber-100 text-amber-800 border-amber-800 dark:bg-amber-900 dark:text-amber-200 dark:border-amber-200',
  delayed: 'bg-red-100 text-red-800 border-red-800 dark:bg-red-900 dark:text-red-200 dark:border-red-200',
  not_started: 'bg-gray-100 text-gray-800 border-gray-800 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-200',
  pending: 'bg-amber-100 text-amber-800 border-amber-800 dark:bg-amber-900 dark:text-amber-200 dark:border-amber-200',
  approved: 'bg-green-100 text-green-800 border-green-800 dark:bg-green-900 dark:text-green-200 dark:border-green-200',
  rejected: 'bg-red-100 text-red-800 border-red-800 dark:bg-red-900 dark:text-red-200 dark:border-red-200',
  delivered: 'bg-blue-100 text-blue-800 border-blue-800 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-200',
  scheduled: 'bg-amber-100 text-amber-800 border-amber-800 dark:bg-amber-900 dark:text-amber-200 dark:border-amber-200',
  released: 'bg-green-100 text-green-800 border-green-800 dark:bg-green-900 dark:text-green-200 dark:border-green-200',
  open: 'bg-red-100 text-red-800 border-red-800 dark:bg-red-900 dark:text-red-200 dark:border-red-200',
  dismissed: 'bg-gray-100 text-gray-800 border-gray-800 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-200',
  snoozed: 'bg-amber-100 text-amber-800 border-amber-800 dark:bg-amber-900 dark:text-amber-200 dark:border-amber-200',
  idle: 'bg-gray-100 text-gray-800 border-gray-800 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-200',
  maintenance: 'bg-amber-100 text-amber-800 border-amber-800 dark:bg-amber-900 dark:text-amber-200 dark:border-amber-200',
  upcoming: 'bg-blue-100 text-blue-800 border-blue-800 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-200',
  achieved: 'bg-green-100 text-green-800 border-green-800 dark:bg-green-900 dark:text-green-200 dark:border-green-200',
  missed: 'bg-red-100 text-red-800 border-red-800 dark:bg-red-900 dark:text-red-200 dark:border-red-200',
  pending_finance: 'bg-amber-100 text-amber-800 border-amber-800 dark:bg-amber-900 dark:text-amber-200 dark:border-amber-200',
  not_applicable: 'bg-gray-100 text-gray-800 border-gray-800 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-200',
  critical: 'bg-red-100 text-red-800 border-red-800 dark:bg-red-900 dark:text-red-200 dark:border-red-200',
  warning: 'bg-amber-100 text-amber-800 border-amber-800 dark:bg-amber-900 dark:text-amber-200 dark:border-amber-200',
  info: 'bg-blue-100 text-blue-800 border-blue-800 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-200',
};

export function StatusBadge({ status, label }: { status: string; label?: string }) {
  const variantClass = STATUS_VARIANTS[status] ?? STATUS_VARIANTS['pending'];
  return (
    <Badge variant="outline" className={cn('brutal-badge', variantClass)}>
      {label ?? status.replace(/_/g, ' ')}
    </Badge>
  );
}
