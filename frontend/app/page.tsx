'use client';

import Link from 'next/link';
import { HardHat, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_50%,var(--tw-gradient-stops))] from-brand-200/40 via-background to-background" />
      
      <Card className="w-full max-w-md border-4 border-border shadow-brutal-xl">
        <CardContent className="flex flex-col items-center pt-10 pb-8 px-8 text-center">
          <div className="mb-6 flex h-20 w-20 items-center justify-center border-4 border-border bg-primary shadow-brutal-sm">
            <HardHat className="h-10 w-10 text-primary-foreground" />
          </div>
          
          <h1 className="font-display text-4xl font-black tracking-tight mb-2">SiteSync</h1>
          <p className="text-muted-foreground font-medium mb-8">
            Resource Command Center for Multi-Site Construction.
          </p>
          
          <div className="flex w-full flex-col gap-4">
            <Link href="/login" className="w-full">
              <Button size="lg" className="w-full text-lg h-14">
                Log In
              </Button>
            </Link>
            
            <Link href="/register" className="w-full">
              <Button variant="outline" size="lg" className="w-full text-lg h-14 gap-2">
                Create Organization <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
      
      <p className="mt-8 text-sm font-bold text-muted-foreground">
        Demo Credentials: admin / pm / contractor / finance (Password: password123)
      </p>
    </div>
  );
}
