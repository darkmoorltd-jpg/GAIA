'use client';
import { useState, useEffect } from 'react'
const API = process.env.NEXT_PUBLIC_API_URL || ''
export default function Page(){
 const [posts,setPosts]=useState<any[]>([])
 const [user,setUser]=useState("")
 const [text,setText]=useState("")
 const load=async()=>{ const r=await fetch(API+"/api/v1/chat/posts"); const d=await r.json(); setPosts((d.posts||[]).slice().reverse()) }
 useEffect(()=>{ load() },[])
 return(<div className="max-w-3xl mx-auto">
  <h1 className="text-3xl font-bold text-gaia-green mb-6">💬 Community Chat</h1>
  <div className="bg-white rounded-xl shadow-md p-6 mb-6">
   <input placeholder="Your name" value={user} onChange={e=>setUser(e.target.value)} className="w-full border rounded-lg px-4 py-2 mb-3"/>
   <textarea placeholder="Share with farmers..." value={text} onChange={e=>setText(e.target.value)} rows={3} className="w-full border rounded-lg px-4 py-2 mb-3"/>
   <button onClick={async()=>{ if(!user||!text) return; const fd=new FormData(); fd.append("user",user); fd.append("text",text); await fetch(API+"/api/v1/chat/post",{method:"POST",body:fd}); setText(""); load(); }} disabled={!user||!text} className="bg-gaia-green text-white px-6 py-3 rounded-lg disabled:opacity-50">Post</button>
  </div>
  <div className="space-y-3">
   {posts.length===0 && <p className="text-gray-500">No posts yet - start the conversation!</p>}
   {posts.map(p=>(<div key={p.id} className="bg-white rounded-xl shadow-md p-4"><b>{p.user}</b><span className="text-xs text-gray-400 ml-2">{new Date(p.t*1000).toLocaleTimeString()}</span><p className="text-sm mt-1">{p.text}</p></div>))}
  </div></div>)}
