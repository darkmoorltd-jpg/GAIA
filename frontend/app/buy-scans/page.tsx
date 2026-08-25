'use client'
import { useState } from 'react'
const API = process.env.NEXT_PUBLIC_API_URL || 'https://maxvwede-source--gaiya-backend-fastapi-app.modal.run'
export default function Page(){
 const [uid,setUid]=useState('demo-user')
 const [email,setEmail]=useState('')
 const [msg,setMsg]=useState('')
 const [busy,setBusy]=useState(false)
 const plans=[{name:'Starter',price:500,scans:10,features:['10 diagnoses','Basic support']},{name:'Farmer',price:2000,scans:50,features:['50 diagnoses','Priority support','Weather alerts'],popular:true},{name:'Cooperative',price:8000,scans:250,features:['250 diagnoses','Dedicated support','All features'],}]
 const buy=async(plan:string)=>{ if(!uid||!email){ setMsg('Enter User ID and Email first.'); return; } setBusy(true)
  const fd=new FormData(); fd.append('user_id',uid); fd.append('email',email); fd.append('plan',plan)
  try{ const r=await fetch(API+'/api/v1/payments/init',{method:'POST',body:fd}); const d=await r.json()
   if(d.authorization_url){ localStorage.setItem('gaia_ref',d.reference); window.location.href=d.authorization_url }
   else setMsg(d.error||'Failed') }catch{ setMsg('Network error') } finally{ setBusy(false) }}
 return(<div className="max-w-4xl mx-auto">
  <h1 className="text-2xl font-bold text-primary-700 mb-2">🛒 Buy Scans</h1>
  <p className="text-gray-500 text-sm mb-6">Secure payment via Paystack.</p>
  <div className="grid md:grid-cols-3 gap-4 mb-6">
   <input defaultValue="demo-user" onBlur={e=>setUid(e.target.value||'demo-user')} placeholder="User ID" className="border rounded-xl px-4 py-2.5"/>
   <input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email" className="border rounded-xl px-4 py-2.5 md:col-span-1"/>
  </div>
  <div className="grid md:grid-cols-3 gap-4">
   {plans.map(p=>(<div key={p.name} className={`rounded-2xl border-2 p-6 ${p.popular?'border-primary-600 bg-primary-50':'border-neutral-200 bg-white'} relative`}>
    {p.popular&&<span className="absolute top-3 right-3 bg-primary-600 text-white text-xs px-2 py-0.5 rounded-full">Popular</span>}
    <h3 className="font-bold text-lg">{p.name}</h3><p className="text-3xl font-extrabold my-3 text-primary-700">₦{p.price.toLocaleString()}</p>
    <ul className="space-y-1.5 mb-4">{p.features.map(f=><li key={f} className="text-sm text-gray-600 flex items-center gap-2"><span className="text-primary-600">✓</span>{f}</li>)}</ul>
    <button onClick={()=>buy(p.name)} disabled={busy} className={`w-full py-3 rounded-xl font-semibold min-h-[48px] ${p.popular?'bg-primary-600 text-white hover:bg-primary-700':'bg-primary-50 text-primary-700 hover:bg-primary-100'} disabled:opacity-40`}>{busy?'Processing...':`Buy ${p.name}`}</button>
   </div>))}
  </div>
  {msg && <div className="mt-6 p-4 bg-gaia-bg rounded-xl"><b>{msg}</b></div>}
 </div>)}
