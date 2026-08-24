import './globals.css'
import type { Metadata, Viewport } from 'next'
import Sidebar from '@/components/Sidebar'

export const metadata: Metadata = {
  title: 'GAIA - Global Agricultural Intelligence Assistant',
  description: 'AI-powered crop disease, pest, soil, and livestock diagnosis.',
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#2e7d32',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gaia-bg min-h-screen">
        <Sidebar />
        <main className="md:ml-64 min-h-screen overflow-x-hidden pt-14 md:pt-0 px-4 md:px-6 pb-20 md:pb-6">
          {children}
        </main>
      </body>
    </html>
  )
}
