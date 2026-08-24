"use client"
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'
const NAV = [
 ["Main","/","HOME","Dashboard"],
 ["Diagnose","/crops","CROP","Crop Disease"],["Diagnose","/pests","PEST","Pest Detection"],["Diagnose","/soil","SOIL","Soil Analysis"],["Diagnose","/livestock","LIVE","Livestock Health"],["Diagnose","/video-scan","VID","Video Field Scanner"],["Diagnose","/voice-agronomist","VOX","Voice Agronomist"],
 ["Farm Business","/wallet","WAL","Wallet"],["Farm Business","/buy-scans","BUY","Buy Scans"],["Farm Business","/marketplace","MKT","Marketplace"],["Farm Business","/loan-management","LOAN","Loan Management"],["Farm Business","/crop-insurance","INS","Crop Insurance"],["Farm Business","/payment-history","PAYH","Payment History"],
 ["Community","/chat","CHT","Community Chat"],["Community","/gaia-meet","MEET","GAIA Meet"],["Community","/live-consultation","CALL","Live Consultation"],["Community","/university","UNI","GAIA University"],
 ["Data & Tools","/early-warning","WARN","Early Warning"],["Data & Tools","/farmer-database","FDB","Farmer Database"],["Data & Tools","/verify-farmer","VFY","Verify Farmer"],["Data & Tools","/verification-history","VHIST","Verification History"],["Data & Tools","/satellite","SAT","Satellite"],["Data & Tools","/farming-calendar","CAL","Farming Calendar"],["Data & Tools","/extension-dashboard","EXT","Extension Dashboard"],["Data & Tools","/admin","ADM","Admin"],
 ["Account","/profile","PROF","Profile"],["Account","/help","HELP","Help"],
]
export default function Sidebar(){
 const [open,setOpen]=useState(false)
 const path=usePathname()
 let last=""
 const out:any[]=[]
 NAV.forEach(([sec,href,icon,label])=>{
  if(sec!==last){out.push(<div key={sec+"h"} className="pt-4 pb-1 px-4 text-xs font-bold uppercase tracking-wide text-gray-400">{sec}</div>);last=sec}
  const active=path===href
  out.push(<Link key={href} href={href} onClick={()=>setOpen(false)} className={"flex items-center px-4 py-2.5 rounded-lg text-sm "+(active?"bg-gaia-green text-white":"text-gray-700 hover:bg-gray-100")}><span className="mr-3 w-5 text-center text-xs font-mono">{icon}</span>{label}</Link>)
 })
 return(
 <>
  <button aria-label="Toggle navigation" onClick={()=>setOpen(!open)} className={"md:hidden fixed top-3 left-3 z-[60] bg-gaia-green text-white rounded-xl px-3 py-2 shadow-lg text-sm font-bold"}>
   {open ? String.fromCharCode(10005) : String.fromCharCode(9776)}
  </button>
  {open && <div onClick={()=>setOpen(false)} className="md:hidden fixed inset-0 bg-black/50 z-40"></div>}
  <aside className={"fixed md:sticky top-0 left-0 z-50 w-64 bg-white shadow-lg h-screen overflow-y-auto transition-transform duration-200 "+(open?"translate-x-0":"-translate-x-full md:translate-x-0")}>
   <div className="p-6 pt-16 md:pt-6 text-2xl font-bold text-gaia-green">GAIA</div>
   <nav className="space-y-1 px-2 pb-8">{out}</nav>
  </aside>
 </>
 )
}
