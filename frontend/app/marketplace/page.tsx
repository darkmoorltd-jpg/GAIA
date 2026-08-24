'use client';
import { useState, useEffect } from 'react'
const API = process.env.NEXT_PUBLIC_API_URL || ''
export default function Page(){
 const [items,setItems]=useState<any[]>([])
 const [form,setForm]=useState({item:"",price:"",contact:""})
 const load=async()=>{ const r=await fetch(API+"/api/v1/marketplace/listings"); const d=await r.json(); setItems(d.listings||[]) }
 useEffect(()=>{ load() },[])
 return(<div className="max-w-4xl mx-auto">
  <h1 className="text-3xl font-bold text-gaia-green mb-6">🏪 Marketplace</h1>
  <div className="bg-white rounded-xl shadow-md p-6 mb-6"><h3 className="font-bold mb-3">Post a listing</h3>
   <input placeholder="Item" value={form.item} onChange={e=>setForm({...form,item:e.target.value})} className="w-full border rounded-lg px-4 py-2 mb-3"/>
   <input placeholder="Price NGN" type="number" value={form.price} onChange={e=>setForm({...form,price:e.target.value})} className="w-full border rounded-lg px-4 py-2 mb-3"/>
   <input placeholder="Contact phone" value={form.contact} onChange={e=>setForm({...form,contact:e.target.value})} className="w-full border rounded-lg px-4 py-2 mb-3"/>
   <button onClick={async()=>{ if(!form.item||!form.price||!form.contact) return; const fd=new FormData(); fd.append("item",form.item); fd.append("price",String(form.price)); fd.append("contact",form.contact); await fetch(API+"/api/v1/marketplace/listing",{method:"POST",body:fd}); setForm({item:"",price:"",contact:""}); load(); }} disabled={!form.item||!form.price||!form.contact} className="bg-gaia-green text-white px-6 py-3 rounded-lg disabled:opacity-50">Post Listing</button>
  </div>
  {items.map(x=>(<div key={x.id} className="bg-white rounded-xl shadow-md p-4 flex justify-between items-center"><div><b>{x.item}</b><p className="text-sm text-gray-500">Contact: {x.contact}</p></div><span className="font-bold text-gaia-green">NGN {Number(x.price).toLocaleString()}</span></div>))}
 </div>)}

