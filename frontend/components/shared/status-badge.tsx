'use client';

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

// Palette tokens used here:
//   "pending/warning/in-progress" → soft sand (#E9DCCB) + dark espresso text (#211715)
//   "active/approved/released"    → green (kept semantic — not part of the palette swap)
//   "error/critical/rejected"     → red  (kept semantic)
//   "neutral/idle/not_started"    → soft sand tint / mahogany borders

const STATUS_VARIANTS: Record<string, string> = {
  active:          'bg-green-100 text-green-800 border-green-800 dark:bg-green-900 dark:text-green-200 dark:border-green-200',
  on_hold:         'bg-soft-sand text-dark-espresso border-dark-espresso dark:bg-soft-sand/20 dark:text-soft-sand dark:border-soft-sand',
  completed:       'bg-blue-100 text-blue-800 border-blue-800 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-200',
  planning:        'bg-blue-100 text-blue-800 border-blue-800 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-200',
  in_progress:     'bg-soft-sand text-dark-espresso border-dark-espresso dark:bg-soft-sand/20 dark:text-soft-sand dark:border-soft-sand',
  delayed:         'bg-red-100 text-red-800 border-red-800 dark:bg-red-900 dark:text-red-200 dark:border-red-200',
  not_started:     'bg-soft-sand/20 text-mahogany border-mahogany dark:bg-soft-sand/10 dark:text-soft-sand dark:border-soft-sand',
  pending:         'bg-soft-sand text-dark-espresso border-dark-espresso dark:bg-soft-sand/20 dark:text-soft-sand dark:border-soft-sand',
  approved:        'bg-green-100 text-green-800 border-green-800 dark:bg-green-900 dark:text-green-200 dark:border-green-200',
  rejected:        'bg-red-100 text-red-800 border-red-800 dark:bg-red-900 dark:text-red-200 dark:border-red-200',
  delivered:       'bg-blue-100 text-blue-800 border-blue-800 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-200',
  scheduled:       'bg-soft-sand text-dark-espresso border-dark-espresso dark:bg-soft-sand/20 dark:text-soft-sand dark:border-soft-sand',
  released:        'bg-green-100 text-green-800 border-green-800 dark:bg-green-900 dark:text-green-200 dark:border-green-200',
  open:            'bg-red-100 text-red-800 border-red-800 dark:bg-red-900 dark:text-red-200 dark:border-red-200',
  dismissed:       'bg-soft-sand/20 text-mahogany border-mahogany dark:bg-soft-sand/10 dark:text-soft-sand dark:border-soft-sand',
  snoozed:         'bg-soft-sand text-dark-espresso border-dark-espresso dark:bg-soft-sand/20 dark:text-soft-sand dark:border-soft-sand',
  idle:            'bg-soft-sand/20 text-mahogany border-mahogany dark:bg-soft-sand/10 dark:text-soft-sand dark:border-soft-sand',
  maintenance:     'bg-soft-sand text-dark-espresso border-dark-espresso dark:bg-soft-sand/20 dark:text-soft-sand dark:border-soft-sand',
  upcoming:        'bg-blue-100 text-blue-800 border-blue-800 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-200',
  achieved:        'bg-green-100 text-green-800 border-green-800 dark:bg-green-900 dark:text-green-200 dark:border-green-200',
  missed:          'bg-red-100 text-red-800 border-red-800 dark:bg-red-900 dark:text-red-200 dark:border-red-200',
  pending_finance: 'bg-soft-sand text-dark-espresso border-dark-espresso dark:bg-soft-sand/20 dark:text-soft-sand dark:border-soft-sand',
  not_applicable:  'bg-soft-sand/20 text-mahogany border-mahogany dark:bg-soft-sand/10 dark:text-soft-sand dark:border-soft-sand',
  critical:        'bg-red-100 text-red-800 border-red-800 dark:bg-red-900 dark:text-red-200 dark:border-red-200',
  warning:         'bg-soft-sand text-dark-espresso border-dark-espresso dark:bg-soft-sand/20 dark:text-soft-sand dark:border-soft-sand',
  info:            'bg-blue-100 text-blue-800 border-blue-800 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-200',
  cancelled:       'bg-red-100 text-red-800 border-red-800 dark:bg-red-900 dark:text-red-200 dark:border-red-200',
};

export function StatusBadge({ status, label }: { status: string; label?: string }) {
  const variantClass = STATUS_VARIANTS[status] ?? STATUS_VARIANTS['pending'];
  return (
    <Badge variant="outline" className={cn('brutal-badge', variantClass)}>
      {label ?? status.replace(/_/g, ' ')}
    </Badge>
  );
}
