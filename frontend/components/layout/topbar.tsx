'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Menu, Bell, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ThemeToggle } from '@/components/layout/theme-toggle';
import { useAuth } from '@/providers/auth-provider';
import { ROLE_LABELS } from '@/lib/types';
import { LanguageSelect } from '@/components/shared/language-select';
import { apiFetch } from '@/lib/api';

interface TopbarProps {
  onMenuClick: () => void;
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const { user, role, logout } = useAuth();
  const [notifications, setNotifications] = useState<any[]>([]);

  useEffect(() => {
    async function fetchNotifications() {
      if (!user) return;
      try {
        const data = await apiFetch<any[]>('/api/v1/notifications/');
        setNotifications(data);
      } catch (error) {
        console.error('Failed to load notifications', error);
      }
    }
    fetchNotifications();
  }, [user]);

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
        <LanguageSelect />
        <ThemeToggle />

        <Button asChild variant="outline" size="icon" className="relative" aria-label="Notifications">
          <Link href="/alerts">
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-sm border-2 border-border bg-destructive text-[10px] font-bold text-destructive-foreground">
                {unreadCount}
              </span>
            )}
          </Link>
        </Button>

        {user && (
          <div className="flex items-center gap-2 border-2 border-border bg-card px-2 py-1 shadow-brutal-sm">
            <div className="flex h-8 w-8 items-center justify-center border-2 border-border bg-primary text-sm font-bold text-primary-foreground">
              {user.name.split(' ').map((n) => n[0]).join('')}
            </div>
            <div className="hidden sm:block">
              <div className="text-sm font-bold leading-none">{user.name}</div>
              <div className="text-xs text-muted-foreground font-medium">{role ? ROLE_LABELS[role as keyof typeof ROLE_LABELS] : ''}</div>
            </div>
          </div>
        )}

        <Button variant="outline" size="sm" onClick={logout} className="ml-2">
          Log Out
        </Button>
      </div>
    </header>
  );
}
