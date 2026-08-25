'use client'
import Link from 'next/link'

const DIAGNOSE = [
  { href: '/crops', icon: '🌿', label: 'Crop Disease', desc: 'Detect from leaf photos' },
  { href: '/pests', icon: '🐛', label: 'Pest Detection', desc: '102 insect species' },
  { href: '/soil', icon: '🏞️', label: 'Soil Analysis', desc: '11 soil types classified' },
  { href: '/livestock', icon: '🐄', label: 'Livestock Health', desc: 'Cattle & poultry' },
]

const TOOLS = [
  { href: '/wallet', icon: '💰', label: 'Wallet' },
  { href: '/buy-scans', icon: '🛒', label: 'Buy Scans' },
  { href: '/marketplace', icon: '🏪', label: 'Marketplace' },
  { href: '/loan-management', icon: '🏦', label: 'Loans' },
  { href: '/early-warning', icon: '⚠️', label: 'Early Warning' },
  { href: '/university', icon: '🎓', label: 'University' },
  { href: '/farming-calendar', icon: '📅', label: 'Calendar' },
  { href: '/satellite', icon: '🛰️', label: 'Satellite' },
]

export default function Home() {
  return (
    <div className="max-w-6xl mx-auto space-y-10 pb-8">
      {/* Hero */}
      <section className="relative rounded-3xl overflow-hidden shadow-lg h-56 md:h-72">
        <img
          src="https://images.unsplash.com/photo-1600112356915-089abb8fc71a?w=1200&q=80"
          alt="Green farm field"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />
        <div className="absolute bottom-0 left-0 p-6 md:p-8">
          <h1 className="text-3xl md:text-5xl font-extrabold text-white tracking-tight">🌱 GAIA</h1>
          <p className="text-white/90 mt-2 text-sm md:text-base max-w-md">
            AI-powered agricultural intelligence. Diagnose crops, detect pests, analyze soil.
          </p>
        </div>
      </section>

      {/* Quick Diagnose */}
      <section>
        <h2 className="font-bold text-xl mb-4 text-neutral-800">Quick Diagnose</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {DIAGNOSE.map(({ href, icon, label, desc }) => (
            <Link key={href} href={href}>
              <div className="group bg-white rounded-2xl shadow-sm hover:shadow-lg border border-neutral-100 p-5 h-full transition-all duration-200 hover:-translate-y-1 cursor-pointer">
                <div className="text-3xl mb-3">{icon}</div>
                <h3 className="font-semibold text-base text-neutral-800 group-hover:text-primary-600 transition-colors">{label}</h3>
                <p className="text-xs text-gray-500 mt-1">{desc}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Tools Bento */}
      <section>
        <h2 className="font-bold text-xl mb-4 text-neutral-800">Farm Business & Tools</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {TOOLS.map(({ href, icon, label }) => (
            <Link key={href} href={href}>
              <div className="bg-white rounded-2xl shadow-sm hover:shadow-md border border-neutral-100 p-4 hover:border-primary-200 transition-all duration-200 hover:-translate-y-0.5 cursor-pointer flex items-center gap-3">
                <span className="text-2xl">{icon}</span>
                <span className="font-medium text-sm text-gray-700">{label}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
