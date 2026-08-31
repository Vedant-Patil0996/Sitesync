import React, { useState } from 'react';
import { Download, X, Smartphone, Sparkles, Share, PlusSquare, CheckCircle } from 'lucide-react';

interface PWAInstallPromptProps {
  onInstall: () => void;
  onDismiss: () => void;
}

export const PWAInstallPrompt: React.FC<PWAInstallPromptProps> = ({ onInstall, onDismiss }) => {
  const [showGuide, setShowGuide] = useState(false);
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as any).MSStream;

  return (
    <div className="relative mx-4 my-3 overflow-hidden rounded-2xl bg-gradient-to-r from-brand-900/95 via-slate-900/95 to-dark-card p-4 border border-brand-500/40 shadow-glow">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-md">
            <Smartphone className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-1.5 text-xs font-bold text-brand-accent">
              <Sparkles className="h-3.5 w-3.5" /> Install App on Your Phone
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Add SiteSync directly to your mobile Home Screen for a native app experience.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => {
              if (isIOS) setShowGuide(!showGuide);
              else onInstall();
            }}
            className="active-tap flex items-center gap-1.5 rounded-xl bg-brand-500 px-3.5 py-2 text-xs font-bold text-white shadow-md hover:bg-brand-600 transition-all"
          >
            <Download className="h-3.5 w-3.5" />
            {isIOS ? 'How to Install' : 'Install PWA'}
          </button>
          <button
            onClick={onDismiss}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-all"
            aria-label="Dismiss banner"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* iOS / Mobile Installation Guide */}
      {showGuide && (
        <div className="mt-3.5 border-t border-slate-800 pt-3 text-xs space-y-2 bg-slate-950/80 p-3 rounded-xl border border-brand-500/20">
          <p className="font-bold text-slate-200 flex items-center gap-1.5">
            <Share className="h-4 w-4 text-brand-accent" /> To Install on iPhone / iPad (Safari):
          </p>
          <ol className="list-decimal list-inside space-y-1 text-slate-300 text-[11px]">
            <li>Tap the <strong className="text-brand-accent">Share button</strong> at the bottom of Safari.</li>
            <li>Scroll down and tap <strong className="text-brand-accent">"Add to Home Screen" <PlusSquare className="inline h-3.5 w-3.5" /></strong>.</li>
            <li>Tap <strong className="text-emerald-400">Add</strong> in the top right corner.</li>
          </ol>
        </div>
      )}
    </div>
  );
};
