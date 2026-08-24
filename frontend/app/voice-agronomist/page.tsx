'use client';
export default function Page(){
 return(<div className="max-w-4xl mx-auto">
  <h1 className="text-3xl font-bold text-gaia-green mb-6">🍅 Voice Agronomist</h1>
  <div className="bg-white rounded-xl shadow-md p-6">
   <p className="text-gray-600 mb-3">Ask anything by voice or text.</p>
   <input placeholder="Ask about your crops" className="w-full border rounded-lg px-4 py-2 mb-3"/>
   <button className="bg-gaia-green text-white px-6 py-3 rounded-lg">Ask</button>
  </div>
 </div>)}

