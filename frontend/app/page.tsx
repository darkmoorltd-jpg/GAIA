'use client'
import Link from 'next/link'
import { useState, useEffect } from 'react'

const STATS = [
  { value: '10+', label: 'Crop Models' },
  { value: '99.5%', label: 'Top Accuracy' },
  { value: '152', label: 'Diagnostic Classes' },
  { value: '24/7', label: 'Offline Ready' },
]

const DIAGNOSE = [
  { href: '/crops', icon: '🌿', label: 'Crop Disease', desc: 'Detect from leaf photos' },
  { href: '/pests', icon: '🐛', label: 'Pest Detection', desc: '102 insect species' },
  { href: '/soil', icon: '🏞️', label: 'Soil Analysis', desc: '11 soil types' },
  { href: '/livestock', icon: '🐄', label: 'Livestock', desc: 'Cattle and poultry' },
]

const TOOLS = [
  { href: '/wallet', icon: '💰', label: 'Wallet' },
  { href: '/buy-scans', icon: '🛒', label: 'Buy Scans' },
  { href: '/marketplace', icon: '🏪', label: 'Marketplace' },
  { href: '/loan-management', icon: '🏦', label: 'Loans' },
  { href: '/early-warning', icon: '⚠️', label: 'Alerts' },
  { href: '/university', icon: '🎓', label: 'University' },
  { href: '/farming-calendar', icon: '📅', label: 'Calendar' },
  { href: '/satellite', icon: '🛰️', label: 'Satellite' },
]

export default function Home() {
  const [dark, setDark] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('gaia-theme')
    const isDark = saved === 'dark'
    setDark(isDark)
    document.documentElement.classList.toggle('dark', isDark)
    setMounted(true)
  }, [])

  const toggleTheme = () => {
    const next = !dark
    setDark(next)
    localStorage.setItem('gaia-theme', next ? 'dark' : 'light')
    document.documentElement.classList.toggle('dark', next)
    window.dispatchEvent(new CustomEvent('gaia-theme-change', { detail: next ? 'dark' : 'light' }))
  }

  if (!mounted) return null

  return (
    <div className={dark
      ? 'min-h-screen bg-neutral-950 text-neutral-100 transition-colors duration-300'
      : 'min-h-screen bg-[#f4faf5] text-neutral-800 transition-colors duration-300'}>

      {/* Theme toggle — top RIGHT, global */}
      <div className="fixed top-3 right-4 z-[80] flex items-center gap-2">
        <span className="text-xs font-medium opacity-60">{dark ? 'Dark' : 'Light'}</span>
        <button
          onClick={toggleTheme}
          className="relative w-12 h-6 rounded-full cursor-pointer transition-colors duration-300"
          style={{ background: dark ? '#16a34a' : '#e5e7eb' }}
          aria-label="Toggle dark mode"
          role="switch"
          aria-checked={dark}
        >
          <span className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow-md transition-all duration-300 ${dark ? 'left-[26px]' : 'left-0.5'}`} />
        </button>
      </div>

      {/* Hero */}
      <div className="relative rounded-2xl overflow-hidden mx-4 mt-4 h-52 md:h-72 shadow-lg">
        <img src="https://images.unsplash.com/photo-1556801712-76c8eb07bbc9?w=900&q=80" alt="Farm field" className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/40 to-transparent" />
        <div className="absolute inset-0 flex flex-col justify-end p-6 md:p-8">
          <div className="text-white/70 text-xs font-semibold uppercase tracking-widest mb-2">Global Agricultural Intelligence</div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight leading-none">GAIA</h1>
          <p className="text-white/80 text-sm mt-2 max-w-sm">AI crop disease, pest, soil and livestock diagnosis — your pocket agronomist.</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 px-4 mt-6">
        {STATS.map(({ value, label }) => (
          <div key={label} className={`rounded-xl p-4 text-center ${dark ? 'bg-white/5 border border-white/10' : 'bg-white shadow-sm border border-neutral-100'}`}>
            <div className="text-2xl font-extrabold text-primary-600">{value}</div>
            <div className={`text-xs mt-1 ${dark ? 'text-gray-400' : 'text-gray-500'}`}>{label}</div>
          </div>
        ))}
      </div>

      {/* Quick Diagnose */}
      <div className="px-4 mt-8">
        <h2 className="font-bold text-lg mb-4">Quick Diagnose</h2>
        <div className="grid grid-cols-2 gap-4">
          {DIAGNOSE.map(({ href, icon, label, desc }) => (
            <Link key={href} href={href}>
              <div className={`group rounded-2xl p-5 cursor-pointer transition-all duration-200 hover:-translate-y-1 ${dark ? 'bg-white/5 border border-white/10 hover:bg-white/10' : 'bg-white shadow-sm hover:shadow-lg hover:border-primary-200 border border-neutral-100'}`}>
                <div className="text-4xl mb-3">{icon}</div>
                <h3 className={`font-semibold ${dark ? 'text-white' : 'text-neutral-800'}`}>{label}</h3>
                <p className={`text-xs mt-1 ${dark ? 'text-gray-500' : 'text-gray-500'}`}>{desc}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Tools */}
      <div className="px-4 mt-8 mb-8">
        <h2 className="font-bold text-lg mb-4">Tools & Services</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {TOOLS.map(({ href, icon, label }) => (
            <Link key={href} href={href}>
              <div className={`flex items-center gap-3 rounded-xl p-4 cursor-pointer transition-all duration-200 ${dark ? 'bg-white/5 hover:bg-white/10 border border-white/10' : 'bg-white shadow-sm hover:shadow-md border border-neutral-100 hover:border-primary-200'}`}>
                <span className="text-xl">{icon}</span>
                <span className={`font-medium text-sm ${dark ? 'text-gray-200' : 'text-gray-700'}`}>{label}</span>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className={`text-center py-6 border-t text-xs ${dark ? 'border-white/10 text-gray-500' : 'border-neutral-100 text-gray-400'}`}>
        Powered by <strong>Darkmoor Ltd</strong> · <a href="mailto:darkmoorltd@gmail.com" className="text-primary-600">darkmoorltd@gmail.com</a>
      </footer>
    </div>
  )
}
