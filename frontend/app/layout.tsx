import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Emperium · CRM Dashboard',
  description: 'Lead analytics and CRM management platform',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark" data-density="cozy">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;450;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
        <meta name="viewport" content="width=1440" />
      </head>
      <body>{children}</body>
    </html>
  );
}
