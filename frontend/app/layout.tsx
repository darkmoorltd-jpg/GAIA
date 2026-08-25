import './globals.css'
import type { Metadata, Viewport } from 'next'
import Sidebar from '@/components/Sidebar'
import Script from 'next/script'

export const metadata: Metadata = {
  title: 'GAIA - Global Agricultural Intelligence Assistant',
  description: 'AI-powered crop disease, pest, soil, and livestock diagnosis.',
  applicationName: 'GAIA',
  manifest: '/manifest.json',
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#16a34a',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gaia-bg min-h-screen antialiased font-[family-name:var(--font-body)]">
        <Sidebar />
        <main className="md:ml-64 min-h-screen overflow-x-hidden pt-14 md:pt-0 px-4 md:px-8 pb-20 md:pb-8">
          {children}
        </main>
        <Script id="sw-reg" strategy="afterInteractive">{`
          if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js').catch(()=>{});
          }
        `}</Script>
      </body>
    </html>
  )
}
