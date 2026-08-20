import './globals.css';
import type { Metadata } from 'next';
import { Inter, EB_Garamond } from 'next/font/google';
import { ThemeProvider } from '@/components/providers/theme-provider';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const ebGaramond = EB_Garamond({
  subsets: ['latin'],
  variable: '--font-eb-garamond',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'SiteSync — Construction Resource Management',
  description: 'Multi-site construction resource management for Indian construction companies.',
  openGraph: {
    title: 'SiteSync',
    description: 'Multi-site construction resource management platform',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${ebGaramond.variable} font-sans`}>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
