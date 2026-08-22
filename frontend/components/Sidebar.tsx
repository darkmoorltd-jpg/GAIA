'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const links = [
  { href: '/', label: 'Dashboard', icon: '🏠' },
  { href: '/crops', label: 'Crop Disease', icon: '🌿' },
  { href: '/pests', label: 'Pest Detection', icon: '🐛' },
  { href: '/soil', label: 'Soil Analysis', icon: '🏞️' },
  { href: '/livestock', label: 'Livestock Health', icon: '🐄' },
  { href: '/buy-scans', label: 'Buy Scans', icon: '💳' },
  { href: '/profile', label: 'Profile', icon: '👤' },
]

export default function Sidebar() {
  const pathname = usePathname()
  return (
    <aside className="w-64 bg-white shadow-lg h-screen">
      <div className="p-6 text-2xl font-bold text-gaia-green">🌱 GAIA</div>
      <nav className="space-y-2">
        {links.map((link) => {
          const active = pathname === link.href
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center px-4 py-3 rounded-lg ${
                active ? 'bg-gaia-green text-white' : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <span className="mr-3">{link.icon}</span>
              {link.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
