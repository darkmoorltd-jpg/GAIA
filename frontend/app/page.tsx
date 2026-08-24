"use client"
import PageBackground from "@/components/PageBackground"
import Link from "next/link"
export default function Page(){
 return(<>
 <PageBackground imageUrl="https://images.unsplash.com/photo-1556801712-76c8eb07bbc9?w=800&q=80" overlay={0.5} />
 <div className="relative z-10 max-w-6xl mx-auto">
  <h1 className="text-4xl font-extrabold text-gaia-green mb-8 text-center">🌱 GAIA Dashboard</h1>
  <h2 className="font-bold text-lg mb-3">Quick Diagnose</h2>
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
   {[["🌿","/crops","Crop Disease"],["🐛","/pests","Pests"],["🏞️","/soil","Soil"],["🐄","/livestock","Livestock"]].map(([i,t,h])=>(<Link key={h} href={h}><div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-md p-5 hover:shadow-lg transition"><div className="text-3xl mb-2">{i}</div><div className="font-semibold text-sm">{t}</div></div></Link>))}
  </div>
  <h2 className="font-bold text-lg mb-3">Farm Tools</h2>
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
   {[["💰","/wallet","Wallet"],["🏪","/marketplace","Marketplace"],["⚠️","/early-warning","Early Warning"],["🎓","/university","University"]].map(([i,t,h])=>(<Link key={h} href={h}><div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-md p-4 hover:shadow-lg transition"><div className="text-2xl mb-1">{i}</div><div className="font-semibold text-xs">{t}</div></div></Link>))}
  </div>
 </div>
 </>)
}
