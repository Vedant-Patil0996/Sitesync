'use client';

import * as React from 'react';
import { Plus, Calculator, Calendar, AlertCircle, IndianRupee } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { apiFetch } from '@/lib/api';
import { formatCurrency } from '@/lib/types';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface MaterialRequestDialogProps {
  siteId?: number;
  siteName?: string;
  onSuccess?: () => void;
}

export function MaterialRequestDialog({ siteId, siteName, onSuccess }: MaterialRequestDialogProps) {
  const [open, setOpen] = React.useState(false);
  const [selectedSiteId, setSelectedSiteId] = React.useState<string>(siteId ? String(siteId) : '');
  const [selectedMaterialId, setSelectedMaterialId] = React.useState<string>('');
  const [priority, setPriority] = React.useState<string>('normal');
  const [requiredDate, setRequiredDate] = React.useState<string>('');
  const [quantity, setQuantity] = React.useState<string>('');
  const [unitCost, setUnitCost] = React.useState<string>('');
  const [justification, setJustification] = React.useState<string>('');

  const queryClient = useQueryClient();

  const { data: materials } = useQuery({
    queryKey: ['materials'],
    queryFn: () => apiFetch<any[]>('/api/v1/inventory/materials'),
  });

  const { data: sites } = useQuery({
    queryKey: ['sites'],
    queryFn: () => apiFetch<any>('/api/v1/sites').then(res => res.items),
    enabled: !siteId,
  });

  // Calculate live total cost
  const parsedQty = parseFloat(quantity) || 0;
  const parsedUnitCost = parseFloat(unitCost) || 0;
  const totalCost = parsedQty * parsedUnitCost;

  const createRequestMutation = useMutation({
    mutationFn: (data: any) => apiFetch('/api/v1/procurement/requests', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['material-requests'] });
      setOpen(false);
      resetForm();
      if (onSuccess) onSuccess();
    },
  });

  const resetForm = () => {
    setSelectedMaterialId('');
    setPriority('normal');
    setRequiredDate('');
    setQuantity('');
    setUnitCost('');
    setJustification('');
    if (!siteId) setSelectedSiteId('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSiteId || !selectedMaterialId || !quantity) return;

    createRequestMutation.mutate({
      site_id: parseInt(selectedSiteId),
      material_id: parseInt(selectedMaterialId),
      quantity: parseFloat(quantity),
      priority,
      required_date: requiredDate || undefined,
      estimated_unit_cost: unitCost ? parseFloat(unitCost) : undefined,
      justification: justification || undefined,
    });
  };

  const selectedMaterial = materials?.find((m: any) => String(m.id) === selectedMaterialId);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2 shadow-brutal">
          <Plus className="h-4 w-4" />
          New Requirement Request
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[550px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl">Material Requirement Form</DialogTitle>
          <DialogDescription>
            Submit detailed site material requisitions with priority and unit cost estimates.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 pt-2">
          {/* Site & Material Selectors */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="site">Site</Label>
              {siteId ? (
                <Input id="site" value={siteName || `Site #${siteId}`} disabled className="bg-muted font-bold" />
              ) : (
                <Select value={selectedSiteId} onValueChange={setSelectedSiteId} required>
                  <SelectTrigger>
                    <SelectValue placeholder="Select site" />
                  </SelectTrigger>
                  <SelectContent>
                    {sites?.map((s: any) => (
                      <SelectItem key={s.id} value={String(s.id)}>
                        {s.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="material">Material</Label>
              <Select value={selectedMaterialId} onValueChange={setSelectedMaterialId} required>
                <SelectTrigger>
                  <SelectValue placeholder="Select material" />
                </SelectTrigger>
                <SelectContent>
                  {materials?.map((m: any) => (
                    <SelectItem key={m.id} value={String(m.id)}>
                      {m.name} ({m.unit})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Priority & Required Date */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="priority">Priority Level</Label>
              <Select value={priority} onValueChange={setPriority}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low Priority</SelectItem>
                  <SelectItem value="normal">Normal Priority</SelectItem>
                  <SelectItem value="high">High Priority</SelectItem>
                  <SelectItem value="urgent">🔴 Urgent / Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="requiredDate">Required By Date</Label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="requiredDate"
                  type="date"
                  value={requiredDate}
                  onChange={(e) => setRequiredDate(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
          </div>

          {/* Quantity & Unit Cost */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="quantity">
                Quantity {selectedMaterial && <span className="text-primary font-bold">({selectedMaterial.unit})</span>}
              </Label>
              <Input
                id="quantity"
                type="number"
                min="0.1"
                step="any"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="0.00"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="unitCost">Estimated Unit Cost (₹)</Label>
              <div className="relative">
                <IndianRupee className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="unitCost"
                  type="number"
                  min="0"
                  step="any"
                  value={unitCost}
                  onChange={(e) => setUnitCost(e.target.value)}
                  placeholder="0.00"
                  className="pl-10"
                />
              </div>
            </div>
          </div>

          {/* Dynamic Calculated Total Card */}
          <div className="border-2 border-primary bg-primary/10 p-3 flex items-center justify-between shadow-brutal-sm">
            <div className="flex items-center gap-2">
              <Calculator className="h-5 w-5 text-primary" />
              <div>
                <span className="text-xs font-bold text-muted-foreground block">Calculated Requirement Total</span>
                <span className="text-xs text-muted-foreground">
                  {parsedQty} × ₹{parsedUnitCost.toLocaleString('en-IN')}
                </span>
              </div>
            </div>
            <div className="font-display font-extrabold text-2xl text-primary">
              {formatCurrency(totalCost)}
            </div>
          </div>

          {/* Justification */}
          <div className="space-y-2">
            <Label htmlFor="justification">Justification & Specifications</Label>
            <Textarea
              id="justification"
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              placeholder="Detail site requirement justification, grade specs, or task dependencies..."
              rows={3}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setOpen(false);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createRequestMutation.isPending} className="shadow-brutal">
              {createRequestMutation.isPending ? 'Submitting Request...' : 'Submit Requirement'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
