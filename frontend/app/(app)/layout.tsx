'use client';

import { RoleProvider } from '@/components/providers/role-provider';
import { AppShell } from '@/components/layout/app-shell';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleProvider>
      <AppShell>
        {children}
      </AppShell>
    </RoleProvider>
  );
}
