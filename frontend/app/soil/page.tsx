"use client"
import PageBackground from "@/components/PageBackground"
export default function Page(){
 return(<>
 <PageBackground imageUrl="https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?w=800&q=80" overlay={0.45} />
 <div className="relative z-10 max-w-4xl mx-auto">
  <h1 className="text-3xl font-bold text-gaia-green mb-6">🏞️ Soil Analysis</h1>
 <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-md p-6 mb-4"><input type="file" accept="image/*" className="mb-3"/><button className="bg-gaia-green text-white px-6 py-3 rounded-lg w-full">Analyze Soil</button></div>
 </div>
 </>)
}
