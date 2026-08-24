"use client"
import PageBackground from "@/components/PageBackground"
export default function Page(){
 return(<>
 <PageBackground imageUrl="https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800&q=80" overlay={0.45} />
 <div className="relative z-10 max-w-4xl mx-auto">
  <h1 className="text-3xl font-bold text-gaia-green mb-6">📅 Farming Calendar</h1>
 <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-md p-6 mb-4"><b>Planting Window</b><p>Maize: Apr-Jul (South), Jun-Aug (North)</p></div><div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-md p-6"><b>Harvest</b><p>Jul-Oct depending on variety</p></div>
 </div>
 </>)
}
