import './globals.css'
import type { Metadata } from 'next'
import Sidebar from '@/components/Sidebar'

export const metadata: Metadata = {
  title: 'GAIA - Global Agricultural Intelligence Assistant',
  description: 'AI-powered crop disease, pest, soil, and livestock diagnosis.',
  viewport: { width: 'device-width', initialScale: 1, maximumScale: 1 },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gaia-bg min-h-screen">
        <Sidebar />
        <main className="md:ml-64 min-h-screen overflow-y-auto p-4 pt-16 md:p-6 md:pt-6">{children}</main>
      </body>
    </html>
  )
}
