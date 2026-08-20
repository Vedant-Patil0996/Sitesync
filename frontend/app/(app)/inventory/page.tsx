'use client';

import * as React from 'react';
import { Package, Plus, ArrowRightLeft, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/shared/page-header';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { inventory, sites, inventoryTransactions } from '@/lib/mock-data';
import { formatDate } from '@/lib/types';

export default function InventoryPage() {
  const [search, setSearch] = React.useState('');
  const [siteFilter, setSiteFilter] = React.useState('all');
  const [showTxForm, setShowTxForm] = React.useState(false);

  const filtered = inventory.filter((item) => {
    const matchesSearch = item.material_name.toLowerCase().includes(search.toLowerCase());
    const matchesSite = siteFilter === 'all' || item.site_id === siteFilter;
    return matchesSearch && matchesSite;
  });

  return (
    <div>
      <PageHeader
        title="Inventory"
        description="Track stock levels across all sites"
        action={
          <Button className="gap-2" onClick={() => setShowTxForm(!showTxForm)}>
            <Plus className="h-4 w-4" /> Log Transaction
          </Button>
        }
      />

      {showTxForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Log Stock Transaction</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <label className="text-sm font-bold">Type</label>
                <Select defaultValue="stock_in">
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="stock_in">Stock In</SelectItem>
                    <SelectItem value="stock_out">Stock Out</SelectItem>
                    <SelectItem value="transfer_out">Transfer Out</SelectItem>
                    <SelectItem value="transfer_in">Transfer In</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-bold">Material</label>
                <Select>
                  <SelectTrigger><SelectValue placeholder="Select material" /></SelectTrigger>
                  <SelectContent>
                    {inventory.map((item) => (
                      <SelectItem key={item.id} value={item.id}>{item.material_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-bold">Quantity</label>
                <Input type="number" placeholder="0" />
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <Button>Save Transaction</Button>
              <Button variant="outline" onClick={() => setShowTxForm(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search materials..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={siteFilter} onValueChange={setSiteFilter}>
          <SelectTrigger className="w-full sm:w-[200px]">
            <SelectValue placeholder="Filter by site" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Sites</SelectItem>
            {sites.map((site) => (
              <SelectItem key={site.id} value={site.id}>{site.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Inventory table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Material</TableHead>
                <TableHead>Site</TableHead>
                <TableHead>Current Stock</TableHead>
                <TableHead>Reorder Level</TableHead>
                <TableHead>Daily Usage</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Updated</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((item) => {
                const site = sites.find((s) => s.id === item.site_id);
                const isLow = item.current_stock <= item.reorder_level;
                const daysLeft = item.consumption_rate_per_day > 0
                  ? Math.floor(item.current_stock / item.consumption_rate_per_day)
                  : Infinity;
                return (
                  <TableRow key={item.id}>
                    <TableCell className="font-bold">{item.material_name}</TableCell>
                    <TableCell className="text-muted-foreground">{site?.name}</TableCell>
                    <TableCell className="font-extrabold">{item.current_stock} {item.unit}</TableCell>
                    <TableCell>{item.reorder_level} {item.unit}</TableCell>
                    <TableCell>{item.consumption_rate_per_day} {item.unit}/day</TableCell>
                    <TableCell>
                      {isLow ? (
                        <Badge variant="destructive" className="brutal-badge">LOW STOCK</Badge>
                      ) : daysLeft < 30 ? (
                        <Badge variant="warning" className="brutal-badge">MONITOR</Badge>
                      ) : (
                        <Badge variant="success" className="brutal-badge">OK</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{formatDate(item.updated_at)}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Recent transactions */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><ArrowRightLeft className="h-5 w-5" /> Recent Transactions</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Material</TableHead>
                <TableHead>Quantity</TableHead>
                <TableHead>Performed By</TableHead>
                <TableHead>Note</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {inventoryTransactions.slice(0, 10).map((tx) => {
                const inv = inventory.find((i) => i.id === tx.inventory_id);
                return (
                  <TableRow key={tx.id}>
                    <TableCell>
                      <Badge variant={tx.type === 'stock_in' || tx.type === 'transfer_in' ? 'success' : 'warning'} className="brutal-badge">
                        {tx.type.replace(/_/g, ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-bold">{inv?.material_name ?? 'Unknown'}</TableCell>
                    <TableCell className="font-extrabold">{tx.quantity} {inv?.unit}</TableCell>
                    <TableCell className="text-sm">{tx.performed_by_name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{tx.note}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{formatDate(tx.created_at)}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
