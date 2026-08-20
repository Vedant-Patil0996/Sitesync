'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, Building2, FolderKanban, Package, Wrench,
  ShoppingCart, Wallet, AlertTriangle, Users, FileText, Map,
  Settings, HardHat, X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/providers/auth-provider';

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  roles: string[];
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, roles: ['admin', 'pm', 'contractor', 'finance'] },
  { label: 'Sites', href: '/sites', icon: Building2, roles: ['admin', 'pm', 'contractor', 'finance'] },
  { label: 'Projects', href: '/projects', icon: FolderKanban, roles: ['admin', 'pm', 'contractor', 'finance'] },
  { label: 'Inventory', href: '/inventory', icon: Package, roles: ['admin', 'pm'] },
  { label: 'Equipment', href: '/equipment', icon: Wrench, roles: ['admin', 'pm'] },
  { label: 'Material Requests', href: '/procurement/requests', icon: ShoppingCart, roles: ['admin', 'pm', 'contractor'] },
  { label: 'Vendor Quotes', href: '/procurement/quotes', icon: FileText, roles: ['admin', 'finance'] },
  { label: 'Finance', href: '/finance', icon: Wallet, roles: ['admin', 'finance'] },
  { label: 'Purchase Orders', href: '/finance/purchase-orders', icon: FileText, roles: ['admin', 'finance'] },
  { label: 'Payments', href: '/finance/payments', icon: Wallet, roles: ['admin', 'finance'] },
  { label: 'Alerts', href: '/alerts', icon: AlertTriangle, roles: ['admin', 'pm', 'finance'] },
  { label: 'My Site', href: '/my-site', icon: HardHat, roles: ['contractor'] },
  { label: 'User Management', href: '/admin/users', icon: Users, roles: ['admin'] },
  { label: 'Audit Log', href: '/admin/audit-log', icon: FileText, roles: ['admin'] },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { role } = useAuth();

  const visibleItems = navItems.filter((item) => item.roles.includes(role || ''));

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={cn(
          'fixed left-0 top-0 z-50 h-full w-64 border-r-2 border-border bg-card transition-transform duration-300 lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center justify-between border-b-2 border-border px-4">
          <Link href="/dashboard" className="flex items-center gap-2" onClick={onClose}>
            <div className="flex h-9 w-9 items-center justify-center border-2 border-border bg-primary shadow-brutal-sm">
              <HardHat className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-display text-xl font-extrabold tracking-tight">SiteSync</span>
          </Link>
          <button onClick={onClose} className="lg:hidden">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex flex-col gap-1 overflow-y-auto p-3 scrollbar-thin" style={{ maxHeight: 'calc(100vh - 4rem)' }}>
          {visibleItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  'flex items-center gap-3 rounded-sm border-2 px-3 py-2.5 text-sm font-bold transition-all',
                  isActive
                    ? 'border-border bg-primary text-primary-foreground shadow-brutal-sm'
                    : 'border-transparent text-foreground hover:border-border hover:bg-accent hover:shadow-brutal-sm'
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
