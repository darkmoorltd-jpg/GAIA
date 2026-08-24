"use client"
import PageBackground from "@/components/PageBackground"
export default function Page(){
 return(<>
 <PageBackground imageUrl="https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=800&q=80" overlay={0.45} />
 <div className="relative z-10 max-w-4xl mx-auto">
  <h1 className="text-3xl font-bold text-gaia-green mb-6">🎥 Video Field Scanner</h1>
 <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-md p-6"><input type="file" accept="video/*" className="mb-3"/><button disabled className="bg-gray-300 px-6 py-3 rounded-lg w-full">Coming online with GPU queue</button></div>
 </div>
 </>)
}
