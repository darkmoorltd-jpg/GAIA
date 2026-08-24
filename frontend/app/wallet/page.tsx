'use client';
import { useState, useEffect } from 'react'
const API = process.env.NEXT_PUBLIC_API_URL || ''
export default function Page(){
 const [uid,setUid]=useState("demo-user")
 const [w,setW]=useState<any>(null)
 const [txns,setTxns]=useState<any[]>([])
 const load=async(u:string)=>{ const wr=await fetch(API+"/api/v1/wallet/"+u); setW(await wr.json()); const tr=await fetch(API+"/api/v1/payments/history/"+u); const td=await tr.json(); setTxns(td.transactions||[]) }
 useEffect(()=>{ load(uid) },[uid])
 return(<div className="max-w-4xl mx-auto">
  <h1 className="text-3xl font-bold text-gaia-green mb-6">💰 Digital Wallet</h1>
  <input defaultValue="demo-user" onBlur={e=>setUid(e.target.value||"demo-user")} placeholder="User ID" className="w-full border rounded-lg px-4 py-2 mb-6"/>
  {w && <div className="grid md:grid-cols-3 gap-4 mb-6"><div className="bg-white rounded-xl shadow-md p-6"><p className="text-sm text-gray-500">Balance</p><p className="text-3xl font-extrabold text-gaia-green">NGN {Number(w.balance).toLocaleString()}</p></div><div className="bg-white rounded-xl shadow-md p-6"><p className="text-sm text-gray-500">Scans Left</p><p className="text-3xl font-extrabold">{w.scans}</p></div></div>}
  <div className="bg-white rounded-xl shadow-md p-6 mb-6"><h3 className="font-bold mb-3">Top Up</h3>{[1000,5000,10000].map((a:number)=>(<button key={a} onClick={async()=>{ const fd=new FormData(); fd.append("amount",String(a)); await fetch(API+"/api/v1/wallet/"+uid+"/topup",{method:"POST",body:fd}); load(uid); }} className="bg-gaia-green text-white px-4 py-2 rounded-lg mr-2">+ NGN {a.toLocaleString()}</button>))}</div>
  <h3 className="font-bold mb-3">Transactions</h3>
  {txns.length===0 ? <p className="text-gray-500">No transactions yet.</p> : txns.slice().reverse().map((t:any,i:number)=>(<div key={i} className="bg-white rounded-xl shadow p-4 mb-2 flex justify-between"><span>{t.type}</span><b>{t.amount?"NGN "+Number(t.amount).toLocaleString():""}</b></div>))}
 </div>)}

