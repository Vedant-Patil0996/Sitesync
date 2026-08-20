'use client';

import { useState, useEffect } from 'react';
import { FileText, Loader2, Search } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/shared/page-header';
import { Pagination } from '@/components/shared/pagination';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { formatDateTime } from '@/lib/types';
import { apiFetch } from '@/lib/api';
import { toast } from 'sonner';

export default function AuditLogPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const itemsPerPage = 20;

  const loadData = async (page: number) => {
    setLoading(true);
    try {
      const skip = (page - 1) * itemsPerPage;
      const data = await apiFetch<any>(`/api/v1/admin/audit-log?skip=${skip}&limit=${itemsPerPage}`);
      setLogs(data.items);
      setTotalPages(data.pages);
      setCurrentPage(data.page);
    } catch (error) {
      console.error('Failed to load audit logs:', error);
      toast.error('Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(1);
  }, []);

  const filteredLogs = logs.filter((log) => {
    if (!search) return true;
    const lowerSearch = search.toLowerCase();
    return (
      (log.action && log.action.toLowerCase().includes(lowerSearch)) ||
      (log.user_name && log.user_name.toLowerCase().includes(lowerSearch)) ||
      (log.entity_type && log.entity_type.toLowerCase().includes(lowerSearch))
    );
  });

  return (
    <div>
      <PageHeader title="Audit Log" description="Review system events and user actions across the platform" />

      <div className="mb-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search logs by action, user, or entity..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Entity ID</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-primary mx-auto" />
                  </TableCell>
                </TableRow>
              ) : filteredLogs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    No audit logs found.
                  </TableCell>
                </TableRow>
              ) : (
                filteredLogs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="text-xs text-muted-foreground whitespace-nowrap">{formatDateTime(log.created_at)}</TableCell>
                    <TableCell className="font-bold">{log.user_name}</TableCell>
                    <TableCell className="font-mono text-xs font-bold text-primary">{log.action}</TableCell>
                    <TableCell className="text-sm">{log.entity_type || '-'}</TableCell>
                    <TableCell className="text-sm font-mono">{log.entity_id || '-'}</TableCell>
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
