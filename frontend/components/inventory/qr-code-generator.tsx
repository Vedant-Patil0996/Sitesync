'use client';

import React, { useRef } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Download, Printer, X } from 'lucide-react';

interface QRCodeGeneratorProps {
  open: boolean;
  onClose: () => void;
  batch: {
    batch_code: string;
    material_name: string;
    unit: string;
    site_name: string;
    original_qty: number;
    current_qty: number;
    status: string;
  } | null;
}

export function QRCodeGenerator({ open, onClose, batch }: QRCodeGeneratorProps) {
  const labelRef = useRef<HTMLDivElement>(null);

  if (!batch) return null;

  const qrPayload = batch.batch_code;

  const handlePrint = () => {
    const content = labelRef.current?.innerHTML;
    if (!content) return;
    const w = window.open('', '_blank');
    if (!w) return;
    w.document.write(`
      <html><head><title>QR Label - ${batch.batch_code}</title>
      <style>
        body { font-family: 'Courier New', monospace; margin: 20px; }
        .label { border: 3px solid black; padding: 16px; max-width: 300px; text-align: center; }
        .brand { font-size: 10px; font-weight: bold; letter-spacing: 4px; }
        .mat { font-size: 18px; font-weight: bold; margin: 8px 0 4px; }
        .detail { font-size: 11px; color: #444; margin: 2px 0; }
        .batch { font-size: 13px; font-weight: bold; margin: 8px 0; font-family: monospace; }
        .qr { margin: 12px auto; }
      </style></head>
      <body onload="window.print();window.close()">
        <div class="label">${content}</div>
      </body></html>
    `);
    w.document.close();
  };

  const handleDownload = () => {
    const svg = labelRef.current?.querySelector('svg');
    if (!svg) return;
    const svgData = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([svgData], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${batch.batch_code}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const statusColors: Record<string, string> = {
    IN_STOCK: 'bg-green-100 text-green-800 border-green-300',
    RECEIVED: 'bg-blue-100 text-blue-800 border-blue-300',
    PARTIALLY_CONSUMED: 'bg-amber-100 text-amber-800 border-amber-300',
    DEPLETED: 'bg-red-100 text-red-800 border-red-300',
    TRANSFER_PENDING: 'bg-purple-100 text-purple-800 border-purple-300',
    TRANSFERRED: 'bg-gray-100 text-gray-800 border-gray-300',
    DAMAGED: 'bg-red-200 text-red-900 border-red-400',
    RETURNED: 'bg-gray-100 text-gray-600 border-gray-300',
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            QR Label — {batch.batch_code}
          </DialogTitle>
        </DialogHeader>

        {/* Printable Label */}
        <div ref={labelRef} className="border-4 border-border p-5 text-center shadow-brutal bg-white dark:bg-card">
          <div className="text-[10px] font-black tracking-[5px] text-muted-foreground mb-2">SITESYNC</div>
          <div className="text-xl font-black leading-tight mb-1">{batch.material_name}</div>
          <div className="text-xs text-muted-foreground font-medium mb-1">{batch.original_qty} {batch.unit}</div>
          <div className="text-xs font-medium mb-1">📍 {batch.site_name}</div>
          <div className="text-xs font-mono font-bold border border-border px-2 py-1 inline-block mb-3">
            {batch.batch_code}
          </div>
          <div className="flex justify-center mb-2">
            <QRCodeSVG
              value={qrPayload}
              size={160}
              level="H"
              includeMargin={true}
            />
          </div>
          <div className={`text-[10px] font-bold px-2 py-0.5 border rounded inline-block ${statusColors[batch.status] || ''}`}>
            {batch.status.replace(/_/g, ' ')}
          </div>
          <div className="text-[10px] text-muted-foreground mt-2">
            Scan to view material passport & take action
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 mt-2">
          <Button variant="outline" className="flex-1 gap-2" onClick={handlePrint}>
            <Printer className="h-4 w-4" /> Print
          </Button>
          <Button variant="outline" className="flex-1 gap-2" onClick={handleDownload}>
            <Download className="h-4 w-4" /> Download
          </Button>
        </div>
        <p className="text-xs text-muted-foreground text-center">
          QR payload: <code className="font-mono text-[10px]">{batch.batch_code}</code>
        </p>
      </DialogContent>
    </Dialog>
  );
}
