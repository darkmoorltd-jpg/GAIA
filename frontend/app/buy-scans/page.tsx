'use client';
import { useState } from 'react'
const API = process.env.NEXT_PUBLIC_API_URL || ''
export default function Page(){
 const [uid,setUid]=useState("demo-user")
 const [email,setEmail]=useState("")
 const [msg,setMsg]=useState("")
 const [busy,setBusy]=useState(false)
 const plans=[["Starter",500,10],["Farmer",2000,50],["Cooperative",8000,250]]
 return(<div className="max-w-4xl mx-auto">
  <h1 className="text-3xl font-bold text-gaia-green mb-3">Buy Scans</h1>
  <p className="text-gray-600 mb-4">Pay securely with card, bank transfer or USSD via Paystack.</p>
  <div className="bg-white rounded-xl shadow-md p-6 mb-6 grid md:grid-cols-2 gap-3">
   <input defaultValue="demo-user" onBlur={e=>setUid(e.target.value||"demo-user")} placeholder="User ID" className="border rounded-lg px-4 py-2"/>
   <input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email" className="border rounded-lg px-4 py-2"/>
  </div>
  <div className="grid md:grid-cols-3 gap-4">{plans.map(pl=>(
   <div key={pl[0]} className="bg-white rounded-xl shadow-md p-6"><h3 className="font-bold">{pl[0]}</h3><p className="text-2xl font-extrabold text-gaia-green my-2">NGN {Number(pl[1]).toLocaleString()}</p><p className="text-sm text-gray-500 mb-3">{pl[2]} scans</p>
   <button onClick={async()=>{ if(!uid||!email){ setMsg("Enter User ID and Email first."); return; } setBusy(true); setMsg("Opening Paystack...");
    const fd=new FormData(); fd.append("user_id",uid); fd.append("email",email); fd.append("plan",String(pl[0]));
    const r=await fetch(API+"/api/v1/payments/init",{method:"POST",body:fd}); const d=await r.json();
    if(d.authorization_url){ localStorage.setItem("gaia_ref",d.reference); window.location.href=d.authorization_url; } else { setMsg(d.error||"Failed"); setBusy(false); }
   }} disabled={busy} className="bg-gaia-green text-white px-6 py-3 rounded-lg w-full disabled:opacity-50">{busy?"Please wait":"Buy "+pl[0]}</button></div>))}
  </div>
  {msg && <div className="mt-6 p-4 bg-gaia-bg rounded-lg"><b>{msg}</b></div>}
 </div>)}

