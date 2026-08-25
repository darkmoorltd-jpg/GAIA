'use client'
import Link from 'next/link'
import { useState } from 'react'

const STATS = [
  { value: '10+', label: 'Crop Models' },
  { value: '99.5%', label: 'Top Accuracy' },
  { value: '152', label: 'Diagnostic Classes' },
  { value: '24/7', label: 'Offline Ready' },
]

const NAV_PRIMARY = [
  { href: '/crops', label: 'Crops' },
  { href: '/pests', label: 'Pests' },
  { href: '/soil', label: 'Soil' },
  { href: '/livestock', label: 'Livestock' },
  { href: '/video-scan', label: 'Video Scan' },
  { href: '/satellite', label: 'Satellite' },
  { href: '/voice-agronomist', label: 'Voice AI' },
  { href: '/buy-scans', label: 'Buy Scans' },
]

const NAV_SECONDARY = [
  { href: '/verify-farmer', label: 'Verify' },
  { href: '/verification-history', label: 'History' },
  { href: '/wallet', label: 'Wallet' },
  { href: '/badges', label: 'Badges' },
  { href: '/chat', label: 'Chat' },
  { href: '/marketplace', label: 'Market' },
  { href: '/crop-insurance', label: 'Insurance' },
  { href: '/payment-history', label: 'Payments' },
  { href: '/profile', label: 'Profile' },
  { href: '/help', label: 'Help' },
]

export default function Home() {
  const [dark, setDark] = useState(false)

  return (
    <div className={`${dark ? 'dark' : ''} min-h-screen`}>
      <div className={`min-h-screen transition-colors duration-300 ${
        dark
          ? 'bg-gradient-to-br from-neutral-900 via-neutral-800 to-neutral-900 text-white'
          : 'bg-gradient-to-br from-primary-50 via-primary-50/50 to-yellow-50 text-neutral-800'
      }`}>

        {/* Theme Toggle */}
        <div className="flex justify-center pt-4">
          <button
            onClick={() => setDark(!dark)}
            className={`relative w-14 h-7 rounded-full transition-colors duration-200 cursor-pointer ${
              dark ? 'bg-primary-600' : 'bg-gray-300'
            }`}
            aria-label="Toggle dark mode"
          >
            <span className={`absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full shadow-md transition-transform duration-200 ${
              dark ? 'translate-x-7' : ''
            }`} />
          </button>
        </div>

        {/* Hero Section — animated glowing title */}
        <section className="text-center py-12 px-4">
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight bg-gradient-to-r from-primary-600 via-primary-400 to-primary-600 bg-clip-text text-transparent animate-[pulseGlow_2s_ease-in-out_infinite_alternate]"
            style={{ animationName: 'pulseGlow' }}>
            GAIA
          </h1>
          <style>{`
            @keyframes pulseGlow {
              from { filter: drop-shadow(0 0 8px rgba(22,163,74,0.5)); }
              to { filter: drop-shadow(0 0 20px rgba(22,163,74,0.9)); }
            }
          `}</style>
          <p className={`mt-2 text-lg md:text-xl ${dark ? 'text-gray-400' : 'text-primary-800'}`}>
            Global Agricultural Intelligence Assistant
          </p>
        </section>

        {/* Farm Image */}
        <section className="flex justify-center px-4 mb-10">
          <img
            src="https://images.unsplash.com/photo-1556801712-76c8eb07bbc9?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
            alt="Fresh farm produce"
            className="rounded-2xl shadow-lg w-full max-w-2xl object-cover h-48 md:h-64"
          />
        </section>

        {/* Stats Bar — 4 metrics like Streamlit */}
        <section className="px-4 mb-10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            {STATS.map(({ value, label }) => (
              <div key={label} className={`rounded-xl p-4 text-center backdrop-blur-sm ${
                dark ? 'bg-white/5 border border-white/10' : 'bg-white shadow-md'
              }`}>
                <div className="text-2xl font-bold text-primary-600">{value}</div>
                <div className={`text-xs mt-1 ${dark ? 'text-gray-400' : 'text-primary-700'}`}>{label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Quick Navigation */}
        <section className="px-4 mb-8">
          <h3 className="font-semibold mb-3 text-sm uppercase tracking-wide opacity-60">Quick Navigation</h3>
          <div className="flex flex-wrap gap-2 justify-center max-w-3xl mx-auto">
            {NAV_PRIMARY.map(nav => (
              <Link key={nav.href} href={nav.href}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-150 min-h-[44px] flex items-center ${
                  dark ? 'bg-white/10 hover:bg-white/20 text-white' : 'bg-white hover:bg-primary-50 text-gray-700 shadow-sm'
                }`}>
                {nav.label}
              </Link>
            ))}
          </div>
        </section>

        {/* More Features */}
        <section className="px-4 mb-10">
          <h3 className="font-semibold mb-3 text-sm uppercase tracking-wide opacity-60">More Features</h3>
          <div className="flex flex-wrap gap-2 justify-center max-w-3xl mx-auto">
            {NAV_SECONDARY.map(nav => (
              <Link key={nav.href} href={nav.href}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-150 min-h-[44px] flex items-center ${
                  dark ? 'bg-white/10 hover:bg-white/20 text-white' : 'bg-white hover:bg-primary-50 text-gray-700 shadow-sm'
                }`}>
                {nav.label}
              </Link>
            ))}
          </div>
        </section>

        {/* Footer */}
        <footer className={`text-center py-8 border-t ${dark ? 'border-white/10 text-gray-400' : 'border-black/5 text-gray-500'}`}>
          <p>Powered by <strong>Darkmoor Ltd</strong></p>
          <a href="mailto:darkmoorltd@gmail.com" className="text-primary-600 hover:underline text-sm">darkmoorltd@gmail.com</a>
        </footer>
      </div>
    </div>
  )
}
