'use client';

import { Menu, Bell, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ThemeToggle } from '@/components/layout/theme-toggle';
import { useRole } from '@/components/providers/role-provider';
import { ROLE_LABELS } from '@/lib/types';
import { notifications } from '@/lib/mock-data';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { Role } from '@/lib/types';

interface TopbarProps {
  onMenuClick: () => void;
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const { user, role, switchRole } = useRole();
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b-2 border-border bg-card px-4">
      <Button variant="outline" size="icon" onClick={onMenuClick} className="lg:hidden">
        <Menu className="h-5 w-5" />
      </Button>

      <div className="relative hidden flex-1 max-w-md md:block">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input placeholder="Search sites, projects, materials..." className="pl-10" />
      </div>

      <div className="flex flex-1 items-center justify-end gap-2 md:flex-none">
        <div className="hidden items-center gap-2 sm:flex">
          <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Role:</span>
          <Select value={role} onValueChange={(v) => switchRole(v as Role)}>
            <SelectTrigger className="w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="admin">Admin</SelectItem>
              <SelectItem value="pm">Project Manager</SelectItem>
              <SelectItem value="contractor">Contractor</SelectItem>
              <SelectItem value="finance">Finance</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <ThemeToggle />

        <Button variant="outline" size="icon" className="relative" aria-label="Notifications">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-sm border-2 border-border bg-destructive text-[10px] font-bold text-destructive-foreground">
              {unreadCount}
            </span>
          )}
        </Button>

        <div className="flex items-center gap-2 border-2 border-border bg-card px-2 py-1 shadow-brutal-sm">
          <div className="flex h-8 w-8 items-center justify-center border-2 border-border bg-primary text-sm font-bold text-primary-foreground">
            {user.full_name.split(' ').map((n) => n[0]).join('')}
          </div>
          <div className="hidden sm:block">
            <div className="text-sm font-bold leading-none">{user.full_name}</div>
            <div className="text-xs text-muted-foreground font-medium">{ROLE_LABELS[user.role]}</div>
          </div>
        </div>
      </div>
    </header>
  );
}
