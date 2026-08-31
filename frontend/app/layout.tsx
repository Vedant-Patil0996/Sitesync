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
  manifest: '/manifest.json',
  themeColor: '#A8323E',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'SiteSync',
  },
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
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#A8323E" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
      </head>
      <body className={`${inter.variable} ${ebGaramond.variable} font-sans`} suppressHydrationWarning>
        <ThemeProvider>
          {children}
        </ThemeProvider>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js');
                });
              }
            `,
          }}
        />
      </body>
    </html>
  );
}

