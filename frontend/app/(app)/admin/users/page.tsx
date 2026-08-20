'use client';

import { useState, useEffect } from 'react';
import { Users, UserPlus, Shield, Ban, CheckCircle, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/shared/page-header';
import { StatusBadge } from '@/components/shared/status-badge';
import { Pagination } from '@/components/shared/pagination';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatDate } from '@/lib/types';
import { apiFetch } from '@/lib/api';
import { toast } from 'sonner';

export default function UserManagementPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const itemsPerPage = 10;

  const loadData = async (page: number) => {
    setLoading(true);
    try {
      const skip = (page - 1) * itemsPerPage;
      const data = await apiFetch(`/api/v1/admin/users?skip=${skip}&limit=${itemsPerPage}`);
      setUsers(data.items);
      setTotalPages(data.pages);
      setCurrentPage(data.page);
    } catch (error) {
      console.error('Failed to load users:', error);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(1);
  }, []);

  const handleRoleChange = async (userId: number, role: string) => {
    try {
      await apiFetch(`/api/v1/admin/users/${userId}/role?role=${role}`, { method: 'PATCH' });
      toast.success('User role updated');
      loadData(currentPage);
    } catch (error) {
      toast.error('Failed to update user role');
    }
  };

  const handleToggleStatus = async (userId: number, isActive: boolean) => {
    try {
      const action = isActive ? 'deactivate' : 'activate';
      await apiFetch(`/api/v1/admin/users/${userId}/${action}`, { method: 'PATCH' });
      toast.success(`User ${isActive ? 'deactivated' : 'activated'}`);
      loadData(currentPage);
    } catch (error) {
      toast.error(`Failed to ${isActive ? 'deactivate' : 'activate'} user`);
    }
  };

  return (
    <div>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-8">
        <PageHeader title="User Management" description="Manage access, roles, and status of users in your organization" />
        <Button className="gap-2 shrink-0 h-12 px-6 shadow-brutal-sm border-2 border-border font-bold self-start sm:self-auto">
          <UserPlus className="h-5 w-5" />
          Invite User
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Joined</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-primary mx-auto" />
                  </TableCell>
                </TableRow>
              ) : users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                    No users found.
                  </TableCell>
                </TableRow>
              ) : (
                users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-bold">{user.name}</TableCell>
                    <TableCell className="text-sm">{user.email}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="outline" size="sm" className="h-8 gap-2">
                            <Shield className="h-3 w-3" /> {user.role}
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleRoleChange(user.id, 'admin')}>Admin</DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleRoleChange(user.id, 'pm')}>Project Manager (PM)</DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleRoleChange(user.id, 'contractor')}>Contractor</DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleRoleChange(user.id, 'finance')}>Finance</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={user.is_active ? 'active' : 'inactive'} />
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{formatDate(user.created_at)}</TableCell>
                    <TableCell>
                      <Button 
                        size="sm" 
                        variant={user.is_active ? "destructive" : "outline"} 
                        className="gap-1 h-8"
                        onClick={() => handleToggleStatus(user.id, user.is_active)}
                      >
                        {user.is_active ? <Ban className="h-3 w-3" /> : <CheckCircle className="h-3 w-3" />}
                        {user.is_active ? 'Deactivate' : 'Activate'}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
          
          {!loading && totalPages > 1 && (
            <div className="p-4 border-t-2 border-border flex justify-end bg-accent/20">
              <Pagination 
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={loadData}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
