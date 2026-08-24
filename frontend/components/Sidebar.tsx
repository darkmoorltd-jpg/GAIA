"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"

const NAV = [
  ["Main", "/", "\u2302", "Dashboard"],
  ["Diagnose", "/crops", "\u2618", "Crop Disease"],
  ["Diagnose", "/pests", "\u25c8", "Pest Detection"],
  ["Diagnose", "/soil", "\u25c9", "Soil Analysis"],
  ["Diagnose", "/livestock", "\u25ce", "Livestock Health"],
  ["Diagnose", "/video-scan", "\u25b6", "Video Scan"],
  ["Diagnose", "/voice-agronomist", "\u266a", "Voice Agronomist"],
  ["Farm Business", "/wallet", "\u25a3", "Wallet"],
  ["Farm Business", "/buy-scans", "\u25c7", "Buy Scans"],
  ["Farm Business", "/marketplace", "\u25a6", "Marketplace"],
  ["Farm Business", "/loan-management", "\u25e4", "Loan Management"],
  ["Farm Business", "/crop-insurance", "\u25e5", "Crop Insurance"],
  ["Farm Business", "/payment-history", "\u2630", "Payment History"],
  ["Community", "/chat", "\u2726", "Community Chat"],
  ["Community", "/gaia-meet", "\u2727", "GAIA Meet"],
  ["Community", "/live-consultation", "\u2609", "Live Consultation"],
  ["Community", "/university", "\u2756", "GAIA University"],
  ["Data & Tools", "/early-warning", "\u25b3", "Early Warning"],
  ["Data & Tools", "/farmer-database", "\u25cd", "Farmer Database"],
  ["Data & Tools", "/verify-farmer", "\u2713", "Verify Farmer"],
  ["Data & Tools", "/verification-history", "\u2261", "Verification History"],
  ["Data & Tools", "/satellite", "\u25cb", "Satellite"],
  ["Data & Tools", "/farming-calendar", "\u25a1", "Farming Calendar"],
  ["Data & Tools", "/extension-dashboard", "\u25c8", "Extension Dashboard"],
  ["Data & Tools", "/admin", "\u2699", "Admin"],
  ["Account", "/profile", "\u25d0", "Profile"],
  ["Account", "/help", "?", "Help"],
]

export default function Sidebar() {
  const [open, setOpen] = useState(false)
  const path = usePathname()
  let last = ""
  const out: any[] = []
  NAV.forEach(([sec, href, icon, label]: [string, string, string, string], idx: number) => {
    if (sec !== last) {
      out.push(
        <div key={sec + "_h"} className="pt-4 pb-1 px-4 text-[10px] font-bold uppercase tracking-widest text-gray-400">
          {sec}
        </div>
      )
      last = sec
    }
    const active = path === href
    out.push(
      <motion.div
        key={href}
        initial={{ opacity: 0, x: -15 }}
        animate={{ opacity: open || typeof window !== "undefined" && window.innerWidth >= 768 ? 1 : 0, x: 0 }}
        transition={{ delay: idx * 0.02 }}
      >
        <Link
          href={href}
          onClick={() => setOpen(false)}
          className={
            "flex items-center px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 " +
            (active
              ? "bg-gaia-green text-white shadow-md"
              : "text-gray-600 hover:bg-gaia-bg hover:text-gaia-dark")
          }
        >
          <span className={"mr-3 w-6 text-center text-xs " + (active ? "text-white" : "text-gaia-green")}>{icon}</span>
          {label}
        </Link>
      </motion.div>
    )
  })

  return (
    <>
      {/* Hamburger with specular shine sweep */}
      <button
        aria-label="Toggle navigation"
        onClick={() => setOpen(!open)}
        className="md:hidden fixed top-3 left-3 z-[70] w-12 h-12 rounded-2xl bg-gaia-green text-white shadow-lg flex items-center justify-center overflow-hidden group active:scale-95 transition-transform duration-150 cursor-pointer"
        style={{ boxShadow: "0 4px 20px rgba(46,125,50,0.35)" }}
      >
        <span className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/30 to-transparent pointer-events-none" />
        <div className="relative w-5 h-5 flex flex-col items-center justify-center gap-[5px]">
          <span className={"block h-[2px] w-5 bg-white rounded-full transition-all duration-300 " + (open ? "rotate-45 translate-y-[7px]" : "")} />
          <span className={"block h-[2px] w-5 bg-white rounded-full transition-all duration-200 " + (open ? "opacity-0" : "")} />
          <span className={"block h-[2px] w-5 bg-white rounded-full transition-all duration-300 " + (open ? "-rotate-45 -translate-y-[7px]" : "")} />
        </div>
      </button>

      {/* Backdrop */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setOpen(false)}
            className="md:hidden fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
          />
        )}
      </AnimatePresence>

      {/* Sidebar drawer */}
      <AnimatePresence>
        <motion.aside
          initial={false}
          animate={{ x: open ? 0 : "-100%" }}
          transition={{ type: "spring", damping: 25, stiffness: 250 }}
          className={
            "md:hidden fixed top-0 left-0 z-50 w-64 bg-white shadow-2xl h-screen overflow-y-auto " +
            (open ? "translate-x-0" : "-translate-x-full")
          }
        >
          <div className="p-6 pt-16 text-2xl font-bold text-gaia-green">GAIA</div>
          <nav className="space-y-1 px-3 pb-8">{out}</nav>
          <div className="p-4 text-center text-xs text-gray-400 border-t border-gray-100 mt-4">
            GAIA v3.0 — Powered by AI
          </div>
        </motion.aside>
      </AnimatePresence>

      {/* Desktop static sidebar */}
      <aside className="hidden md:block sticky top-0 w-64 bg-white shadow-lg h-screen overflow-y-auto">
        <div className="p-6 text-2xl font-bold text-gaia-green">GAIA</div>
        <nav className="space-y-1 px-3 pb-8">{out}</nav>
        <div className="p-4 text-center text-xs text-gray-400 border-t border-gray-100 mt-4">
          GAIA v3.0 — Powered by AI
        </div>
      </aside>
    </>
  )
}
