'use client'
import { useState, useEffect } from 'react'
const API = process.env.NEXT_PUBLIC_API_URL || 'https://maxvwede-source--gaiya-backend-fastapi-app.modal.run'
export default function Page(){
  const [posts,setPosts]=useState<any[]>([])
  const [user,setUser]=useState('')
  const [text,setText]=useState('')
  const [sending,setSending]=useState(false)
  const load=async()=>{ const r=await fetch(API+'/api/v1/chat/posts'); const d=await r.json(); setPosts((d.posts||[]).slice().reverse()) }
  useEffect(()=>{ load() },[])
  return(
  <div className="max-w-2xl mx-auto flex flex-col min-h-[80vh]">
   <h1 className="text-2xl font-bold text-primary-700 mb-4 font-[family-name:var(--font-heading)]">💬 Community Chat</h1>
   <div className="bg-white rounded-t-2xl shadow-sm border border-neutral-100 flex-1 overflow-y-auto max-h-[55vh] p-4 space-y-3">
    {posts.length===0 && <p className="text-gray-400 text-center py-8">No posts yet — start the conversation!</p>}
    {posts.map(p=>(
     <div key={p.id} className="flex gap-3">
      <div className="w-9 h-9 bg-primary-100 rounded-full flex items-center justify-center shrink-0 text-sm font-bold text-primary-700">{(p.user||'?')[0].toUpperCase()}</div>
      <div className="flex-1"><b className="text-sm">{p.user}</b><span className="text-xs text-gray-400 ml-2">{new Date(p.t*1000).toLocaleTimeString()}</span><p className="text-sm mt-0.5 text-neutral-800">{p.text}</p></div>
     </div>))}
   </div>
   <div className="sticky bottom-0 bg-white border-t border-neutral-200 rounded-b-2xl shadow-lg p-4 flex gap-3">
    <input value={user} onChange={e=>setUser(e.target.value)} placeholder="Name" className="w-24 border rounded-xl px-3 py-2.5 text-sm"/>
    <input value={text} onChange={e=>setText(e.target.value)} onKeyDown={e=>e.key==='Enter'&&user&&text&&setSending(true)} placeholder="Share with farmers..." className="flex-1 border rounded-xl px-4 py-2.5 text-sm"/>
    <button onClick={async()=>{ if(!user||!text||sending)return; setSending(true); const fd=new FormData(); fd.append('user',user); fd.append('text',text); await fetch(API+'/api/v1/chat/post',{method:'POST',body:fd}); setText(''); setSending(false); load(); }} disabled={!user||!text||sending} className="bg-primary-600 text-white px-5 rounded-xl disabled:opacity-40 min-h-[44px]">Send</button>
   </div>
  </div>)}
