"use client"
import dynamic from "next/dynamic"
const PageBg = dynamic(() => import("@/components/PageBackground"), { ssr: false })
export default function Page(){
 return(<>
 <PageBg imageUrl="https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=800&q=80" overlay={0.45} count={120} color="#2e7d32" />
 <div className="relative z-10 max-w-4xl mx-auto">
  <h1 className="text-3xl font-bold text-gaia-green mb-6">🎥 Video Field Scanner</h1>
  <div className="bg-white/70 backdrop-blur-sm rounded-xl shadow-md p-6">
   <p className="text-gray-600">Upload an image to get AI-powered analysis.</p>
  </div>
 </div>
 </>)
}
