'use client'
import Link from 'next/link'
import Image from 'next/image'
const Q=[["/crops","🌿","Crop Disease"],["/pests","🐛","Pest Detection"],["/soil","🏞️","Soil Analysis"],["/livestock","🐄","Livestock"]]
const M=[["💰","/wallet","Wallet"],["🛒","/buy-scans","Buy Scans"],["🏪","/marketplace","Marketplace"],["🏦","/loan-management","Loans"],["⚠️","/early-warning","Early Warning"],["🎓","/university","University"],["📅","/farming-calendar","Calendar"],["🛰️","/satellite","Satellite"]]
export default function Home(){return(
<div className="max-w-6xl mx-auto pb-20">
 <div className="relative rounded-2xl overflow-hidden mb-8 h-48 md:h-64">
  <Image src="https://images.unsplash.com/photo-1600112356915-089abb8fc71a?w=800&q=80" alt="Farm field" fill className="object-cover"/>
  <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent flex items-end p-6">
   <div><h1 className="text-3xl md:text-4xl font-extrabold text-white">🌱 GAIA</h1><p className="text-white/90 text-sm mt-1">Global Agricultural Intelligence</p></div>
  </div>
 </div>
 <h2 className="font-bold text-lg mb-3">Quick Diagnose</h2>
 <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
  {Q.map(([h,i,t])=>(<Link key={h} href={h}><div className="bg-white rounded-xl shadow-md p-5 hover:shadow-lg transition"><div className="text-3xl mb-2">{i}</div><div className="font-semibold text-sm md:text-base">{t}</div></div></Link>))}
 </div>
 <h2 className="font-bold text-lg mb-3">Everything Else</h2>
 <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
  {M.map(([h,i,t])=>(<Link key={h} href={h}><div className="bg-white rounded-xl shadow-md p-4 hover:shadow-lg transition"><div className="text-2xl mb-1">{i}</div><div className="font-semibold text-sm">{t}</div></div></Link>))}
 </div>
</div>)}
