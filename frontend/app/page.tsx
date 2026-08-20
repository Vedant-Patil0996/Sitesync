'use client';

import Link from 'next/link';
import {
  HardHat, Building2, Package, Wrench, Wallet, AlertTriangle,
  Users, Map, ArrowRight, CheckCircle2, ShieldCheck, Layers,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="sticky top-0 z-40 border-b-2 border-border bg-card/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 md:px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center border-2 border-border bg-primary shadow-brutal-sm">
              <HardHat className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-display text-xl font-extrabold tracking-tight">SiteSync</span>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/login">
              <Button variant="outline" size="sm">Log In</Button>
            </Link>
            <Link href="/get-started">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden border-b-2 border-border">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_30%_20%,var(--tw-gradient-stops))] from-brand-200/40 via-background to-background" />
        <div className="mx-auto max-w-7xl px-4 py-16 md:px-6 md:py-24">
          <div className="grid items-center gap-8 md:grid-cols-2">
            <div className="flex flex-col gap-5">
              <Badge variant="outline" className="w-fit brutal-badge bg-brand-100 text-brand-800 border-brand-800">
                Built for Indian Construction
              </Badge>
              <h1 className="font-display text-4xl font-black leading-tight tracking-tight md:text-6xl">
                One system for{' '}
                <span className="text-primary">every site</span>, every resource.
              </h1>
              <p className="max-w-lg text-lg text-muted-foreground font-medium">
                SiteSync replaces scattered spreadsheets, WhatsApp groups, and phone calls with a single platform for tracking inventory, equipment, projects, procurement, and budgets across 3-15 sites.
              </p>
              <div className="flex flex-wrap gap-3">
                <Link href="/get-started">
                  <Button size="lg" className="gap-2">
                    Create Company Account <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/login">
                  <Button variant="outline" size="lg">Sign In</Button>
                </Link>
              </div>
              <div className="flex flex-wrap gap-4 pt-2">
                {['Multi-site overview', 'Role-based access', 'Two-step approvals'].map((item) => (
                  <div key={item} className="flex items-center gap-1.5 text-sm font-bold">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    {item}
                  </div>
                ))}
              </div>
            </div>

            {/* Hero card mockup */}
            <div className="relative hidden md:block">
              <Card className="rotate-2">
                <CardHeader>
                  <CardTitle>Whitefield Tower A</CardTitle>
                  <div className="flex gap-2">
                    <Badge variant="success" className="brutal-badge">Active</Badge>
                    <Badge variant="outline" className="brutal-badge">Bengaluru</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {[
                    { label: 'Cement (OPC 53)', value: '340 bags', level: 'OK' },
                    { label: 'TMT Steel 16mm', value: '12 tons', level: 'Low' },
                    { label: 'Red Bricks', value: '45,000', level: 'OK' },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center justify-between border-2 border-border bg-secondary px-3 py-2">
                      <span className="text-sm font-bold">{item.label}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{item.value}</span>
                        <Badge variant={item.level === 'Low' ? 'destructive' : 'success'} className="brutal-badge text-[10px]">
                          {item.level}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
              <Card className="absolute -bottom-6 -left-6 -rotate-3 w-48">
                <CardContent className="pt-5">
                  <div className="text-xs font-bold uppercase text-muted-foreground">Budget Used</div>
                  <div className="font-display text-2xl font-extrabold text-primary">42%</div>
                  <div className="mt-1 h-3 border-2 border-border bg-secondary">
                    <div className="h-full w-[42%] bg-primary" />
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Features grid */}
      <section className="border-b-2 border-border py-16 md:py-24">
        <div className="mx-auto max-w-7xl px-4 md:px-6">
          <div className="mb-10 text-center">
            <h2 className="font-display text-3xl font-extrabold tracking-tight md:text-4xl">
              Everything your construction company needs
            </h2>
            <p className="mt-2 text-muted-foreground font-medium">Six core modules, one connected system</p>
          </div>
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {[
              { icon: Building2, title: 'Sites', desc: 'Multi-site overview with map view, status tracking, and resource allocation across all your projects.' },
              { icon: Package, title: 'Inventory', desc: 'Real-time stock levels, reorder alerts, consumption tracking, and cross-site transfers for every material.' },
              { icon: Wrench, title: 'Equipment', desc: 'Track equipment status, allocation to tasks, usage hours, and maintenance schedules across sites.' },
              { icon: Wallet, title: 'Finance', desc: 'Budget vs actual spending, purchase order approvals, payment scheduling, and vendor quote comparison.' },
              { icon: AlertTriangle, title: 'Alerts', desc: 'Stock, equipment, task-delay, budget-drift, and fraud alerts with role-based routing and resolution.' },
              { icon: Users, title: 'Role-Based Access', desc: 'Four distinct roles — PM, Contractor, Finance, Admin — with permissions enforced at the database level.' },
            ].map((feature) => (
              <Card key={feature.title} className="transition-all hover:shadow-brutal-lg hover:translate-x-[-2px] hover:translate-y-[-2px]">
                <CardHeader>
                  <div className="flex h-12 w-12 items-center justify-center border-2 border-border bg-primary shadow-brutal-sm">
                    <feature.icon className="h-6 w-6 text-primary-foreground" />
                  </div>
                  <CardTitle className="mt-2">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground font-medium">{feature.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow section */}
      <section className="border-b-2 border-border bg-secondary py-16 md:py-24">
        <div className="mx-auto max-w-7xl px-4 md:px-6">
          <div className="mb-10 text-center">
            <h2 className="font-display text-3xl font-extrabold tracking-tight md:text-4xl">
              Two-step approval workflow
            </h2>
            <p className="mt-2 text-muted-foreground font-medium">Separating operational approval from financial approval</p>
          </div>
          <div className="grid gap-4 md:grid-cols-5">
            {[
              { step: '01', title: 'Contractor Requests', desc: 'Contractor submits a material request with quantity and details.', icon: HardHat },
              { step: '02', title: 'PM Approves', desc: 'Project Manager reviews — is this actually needed operationally?', icon: ShieldCheck },
              { step: '03', title: 'Vendor Quotes', desc: 'Quotes are attached and compared for the approved request.', icon: Layers },
              { step: '04', title: 'Finance Approves', desc: 'Finance reviews cost and budget — issues the Purchase Order.', icon: Wallet },
              { step: '05', title: 'Payment Released', desc: 'On delivery confirmation, Finance releases the payment.', icon: CheckCircle2 },
            ].map((item) => (
              <Card key={item.step} className="relative">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex h-10 w-10 items-center justify-center border-2 border-border bg-primary text-sm font-extrabold text-primary-foreground shadow-brutal-sm">
                      {item.step}
                    </div>
                    <item.icon className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <CardTitle className="mt-2 text-base">{item.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground font-medium">{item.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 md:py-24">
        <div className="mx-auto max-w-3xl px-4 text-center md:px-6">
          <h2 className="font-display text-3xl font-extrabold tracking-tight md:text-4xl">
            Ready to sync your sites?
          </h2>
          <p className="mt-2 text-muted-foreground font-medium">
            Create your company account and set up your first site in minutes.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link href="/get-started">
              <Button size="lg" className="gap-2">
                Get Started Free <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/login">
              <Button variant="outline" size="lg">Sign In</Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t-2 border-border bg-card py-8">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 md:flex-row md:px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center border-2 border-border bg-primary">
              <HardHat className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-display text-lg font-extrabold">SiteSync</span>
          </div>
          <p className="text-sm text-muted-foreground font-medium">Construction resource management for Indian builders</p>
        </div>
      </footer>
    </div>
  );
}
