'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/providers/auth-provider';
import { HardHat } from 'lucide-react';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="flex h-16 w-16 animate-bounce items-center justify-center border-4 border-border bg-primary shadow-brutal-md">
            <HardHat className="h-8 w-8 text-primary-foreground" />
          </div>
          <p className="font-display text-xl font-bold">Verifying credentials...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
