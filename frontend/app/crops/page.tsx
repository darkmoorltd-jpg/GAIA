'use client'
import { useState } from 'react'
const API = process.env.NEXT_PUBLIC_API_URL || ''
export default function Page(){
 const [f,setF]=useState<File|null>(null)
 const [r,setR]=useState<any>(null)
 const [l,setL]=useState(false)
 return(<div className="max-w-3xl mx-auto">
  <div className="relative rounded-2xl overflow-hidden mb-6 h-32">
   <img src="https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=600&q=80" alt="Crops" className="object-cover w-full h-full"/>
   <div className="absolute inset-0 bg-black/40 flex items-end p-4"><h1 className="text-2xl font-bold text-white">🌿 Crop Disease Diagnosis</h1></div>
  </div>
  <div className="bg-white rounded-xl shadow-md p-6">
   <input type="file" accept="image/*" onChange={e=>setF(e.target.files?.[0]||null)} className="mb-3"/>
   <button onClick={async()=>{if(!f)return;setL(true);try{const fd=new FormData();fd.append("file",f);const res=await fetch(API+"/api/v1/crops/maize/diagnose",{method:"POST",body:fd});setR(await res.json())}catch{setR({error:"Network error"})}finally{setL(false)}}} disabled={!f||l} className="bg-gaia-green text-white px-6 py-3 rounded-lg disabled:opacity-50 w-full">{l?"Diagnosing...":"Upload & Diagnose"}</button>
   {r&&<div className="mt-4 p-4 bg-gaia-bg rounded-xl"><b>{r.diagnosis}</b> — Confidence: {r.confidence}%</div>}
  </div>
 </div>)}
