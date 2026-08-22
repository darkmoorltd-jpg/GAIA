import './globals.css'
import type { Metadata } from 'next'
import Sidebar from '@/components/Sidebar'

export const metadata: Metadata = {
  title: 'GAIA - Global Agricultural Intelligence Assistant',
  description: 'AI-powered crop disease, pest, soil, and livestock diagnosis.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gaia-bg">
        <div className="flex h-screen">
          <Sidebar />
          <main className="flex-1 overflow-y-auto p-6">{children}</main>
        </div>
      </body>
    </html>
  )
}
