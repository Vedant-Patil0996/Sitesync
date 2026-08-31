import React, { useState, useRef, useEffect } from 'react';
import { X, QrCode, PlusCircle, ShoppingBag, CheckCircle, Sparkles, Camera } from 'lucide-react';
import { addInventoryItem, createPurchaseOrder } from '../services/api';

interface QuickActionModalProps {
  type: 'scan' | 'new_stock' | 'new_po' | null;
  onClose: () => void;
  onSuccess: (message: string) => void;
}

export const QuickActionModal: React.FC<QuickActionModalProps> = ({ type, onClose, onSuccess }) => {
  if (!type) return null;

  // Stock Form State
  const [stockName, setStockName] = useState('');
  const [stockCategory, setStockCategory] = useState<'Cement & Concrete' | 'Steel & Metals' | 'Aggregates' | 'Electrical' | 'Plumbing' | 'Safety'>('Cement & Concrete');
  const [stockQty, setStockQty] = useState('');
  const [stockUnit, setStockUnit] = useState('Bags');
  const [stockMinThreshold, setStockMinThreshold] = useState('50');

  // PO Form State
  const [vendorName, setVendorName] = useState('');
  const [poSiteName, setPoSiteName] = useState('Skyline Metro Tower Phase 2');
  const [poAmount, setPoAmount] = useState('');
  const [poUrgent, setPoUrgent] = useState(false);

  // Camera & Scan state
  const [scanning, setScanning] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [scannedData, setScannedData] = useState<{ sku: string; name: string; qty: number } | null>(null);

  const startPhoneCamera = async () => {
    try {
      setCameraActive(true);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (e) {
      console.log('Camera access fallback to simulator:', e);
      handleSimulateScan();
    }
  };

  const stopPhoneCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
    }
    setCameraActive(false);
  };

  useEffect(() => {
    return () => {
      stopPhoneCamera();
    };
  }, []);

  const handleSimulateScan = () => {
    setScanning(true);
    setTimeout(() => {
      setScanning(false);
      stopPhoneCamera();
      setScannedData({
        sku: 'CEM-OPC-53',
        name: 'UltraTech OPC 53 Grade Cement',
        qty: 50
      });
    }, 1200);
  };

  const handleConfirmScan = () => {
    onSuccess(`Successfully logged 50 Bags of UltraTech Cement to Inventory!`);
    onClose();
  };

  const handleCreateStock = (e: React.FormEvent) => {
    e.preventDefault();
    if (!stockName || !stockQty) return;
    addInventoryItem({
      siteId: 'site-1',
      name: stockName,
      sku: `SKU-${Math.floor(1000 + Math.random() * 9000)}`,
      category: stockCategory,
      quantity: Number(stockQty),
      unit: stockUnit,
      minThreshold: Number(stockMinThreshold) || 10,
      unitCost: 250
    });
    onSuccess(`Added ${stockQty} ${stockUnit} of ${stockName} to inventory.`);
    onClose();
  };

  const handleCreatePO = (e: React.FormEvent) => {
    e.preventDefault();
    if (!vendorName || !poAmount) return;
    createPurchaseOrder({
      siteName: poSiteName,
      vendorName: vendorName,
      totalAmount: Number(poAmount),
      itemsCount: 1,
      urgent: poUrgent
    });
    onSuccess(`Created purchase order for ${vendorName} (₹${poAmount})`);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
      <div className="w-full max-w-md glass-panel rounded-2xl border border-slate-700/80 p-6 shadow-2xl animate-in zoom-in-95">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2">
            {type === 'scan' && <QrCode className="h-5 w-5 text-brand-accent" />}
            {type === 'new_stock' && <PlusCircle className="h-5 w-5 text-emerald-400" />}
            {type === 'new_po' && <ShoppingBag className="h-5 w-5 text-brand-orange" />}
            <h3 className="text-base font-bold text-slate-100">
              {type === 'scan' && 'Mobile QR Material Scanner'}
              {type === 'new_stock' && 'Add Material to Stock'}
              {type === 'new_po' && 'Create Requisition PO'}
            </h3>
          </div>
          <button onClick={() => { stopPhoneCamera(); onClose(); }} className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="mt-4">
          
          {/* SCANNER MODAL */}
          {type === 'scan' && (
            <div className="text-center space-y-4">
              {!scannedData ? (
                <div className="space-y-3">
                  {cameraActive ? (
                    <div className="relative rounded-2xl overflow-hidden border-2 border-brand-accent bg-black h-56 flex items-center justify-center">
                      <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
                      <div className="absolute inset-0 border-2 border-dashed border-brand-orange/70 m-8 rounded-xl pointer-events-none animate-pulse" />
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center p-8 rounded-xl border-2 border-dashed border-brand-500/40 bg-slate-900/60">
                      <div className={`h-16 w-16 rounded-2xl flex items-center justify-center bg-brand-500/20 text-brand-accent mb-3 ${scanning ? 'animate-bounce' : ''}`}>
                        <QrCode className="h-8 w-8" />
                      </div>
                      <p className="text-xs text-slate-300 font-medium">
                        {scanning ? 'Analyzing QR / Barcode tag...' : 'Point phone camera at material QR tag'}
                      </p>
                    </div>
                  )}

                  <div className="flex gap-2 pt-2">
                    {!cameraActive && (
                      <button
                        onClick={startPhoneCamera}
                        className="flex-1 active-tap flex items-center justify-center gap-1.5 rounded-xl bg-slate-800 py-2.5 text-xs font-bold text-slate-200 border border-slate-700 hover:text-white transition-all"
                      >
                        <Camera className="h-4 w-4 text-brand-accent" /> Open Phone Camera
                      </button>
                    )}
                    <button
                      onClick={handleSimulateScan}
                      disabled={scanning}
                      className="flex-1 active-tap flex items-center justify-center gap-1.5 rounded-xl bg-brand-500 py-2.5 text-xs font-bold text-white shadow-glow hover:bg-brand-600 transition-all"
                    >
                      <Sparkles className="h-4 w-4" /> {scanning ? 'Scanning...' : 'Simulate Scan'}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 rounded-xl bg-slate-900/80 p-4 border border-emerald-500/30">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                    <CheckCircle className="h-5 w-5" /> QR Code Scanned
                  </div>
                  <div className="text-left text-xs space-y-1.5 bg-slate-950 p-3 rounded-lg font-mono">
                    <div><span className="text-slate-500">SKU:</span> <span className="text-slate-200">{scannedData.sku}</span></div>
                    <div><span className="text-slate-500">ITEM:</span> <span className="text-slate-200">{scannedData.name}</span></div>
                    <div><span className="text-slate-500">BATCH:</span> <span className="text-brand-accent">{scannedData.qty} Bags</span></div>
                  </div>
                  <button
                    onClick={handleConfirmScan}
                    className="w-full active-tap rounded-xl bg-emerald-500 py-2.5 text-xs font-bold text-white shadow-md hover:bg-emerald-600 transition-all"
                  >
                    Log Received Quantity to Inventory
                  </button>
                </div>
              )}
            </div>
          )}

          {/* NEW STOCK MODAL */}
          {type === 'new_stock' && (
            <form onSubmit={handleCreateStock} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Material Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. UltraTech Cement, TMT 12mm Rebar"
                  value={stockName}
                  onChange={(e) => setStockName(e.target.value)}
                  className="w-full glass-input rounded-lg px-3 py-2 text-slate-100"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Category</label>
                  <select
                    value={stockCategory}
                    onChange={(e) => setStockCategory(e.target.value as any)}
                    className="w-full glass-input rounded-lg px-3 py-2 text-slate-100 bg-dark-card"
                  >
                    <option value="Cement & Concrete">Cement & Concrete</option>
                    <option value="Steel & Metals">Steel & Metals</option>
                    <option value="Aggregates">Aggregates</option>
                    <option value="Electrical">Electrical</option>
                    <option value="Plumbing">Plumbing</option>
                    <option value="Safety">Safety</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Unit Type</label>
                  <input
                    type="text"
                    required
                    placeholder="Bags, Tons, Meters"
                    value={stockUnit}
                    onChange={(e) => setStockUnit(e.target.value)}
                    className="w-full glass-input rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Initial Quantity</label>
                  <input
                    type="number"
                    required
                    placeholder="100"
                    value={stockQty}
                    onChange={(e) => setStockQty(e.target.value)}
                    className="w-full glass-input rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Min Threshold</label>
                  <input
                    type="number"
                    placeholder="50"
                    value={stockMinThreshold}
                    onChange={(e) => setStockMinThreshold(e.target.value)}
                    className="w-full glass-input rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full active-tap rounded-xl bg-emerald-500 py-2.5 text-xs font-bold text-white shadow-md hover:bg-emerald-600 transition-all mt-2"
              >
                Add Material Stock
              </button>
            </form>
          )}

          {/* NEW PO MODAL */}
          {type === 'new_po' && (
            <form onSubmit={handleCreatePO} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Target Construction Site</label>
                <select
                  value={poSiteName}
                  onChange={(e) => setPoSiteName(e.target.value)}
                  className="w-full glass-input rounded-lg px-3 py-2 text-slate-100 bg-dark-card"
                >
                  <option value="Skyline Metro Tower Phase 2">Skyline Metro Tower Phase 2</option>
                  <option value="Greenfield Highway Extension">Greenfield Highway Extension</option>
                  <option value="Harbor Logistics Hub">Harbor Logistics Hub</option>
                  <option value="TechPark Commercial Complex">TechPark Commercial Complex</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Vendor / Supplier Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ambuja Cements, Tata Steel Ltd."
                  value={vendorName}
                  onChange={(e) => setVendorName(e.target.value)}
                  className="w-full glass-input rounded-lg px-3 py-2 text-slate-100"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Total Amount (₹)</label>
                <input
                  type="number"
                  required
                  placeholder="250000"
                  value={poAmount}
                  onChange={(e) => setPoAmount(e.target.value)}
                  className="w-full glass-input rounded-lg px-3 py-2 text-slate-100"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="urgent"
                  checked={poUrgent}
                  onChange={(e) => setPoUrgent(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-brand-orange focus:ring-brand-orange"
                />
                <label htmlFor="urgent" className="text-slate-300 font-medium cursor-pointer">
                  Mark as High Priority / Urgent Order
                </label>
              </div>

              <button
                type="submit"
                className="w-full active-tap rounded-xl bg-brand-orange py-2.5 text-xs font-bold text-white shadow-glow-orange hover:brightness-110 transition-all mt-2"
              >
                Submit Purchase Order Requisition
              </button>
            </form>
          )}

        </div>

      </div>
    </div>
  );
};
