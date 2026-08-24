'use client';
export default function Page(){
 return(<div className="max-w-4xl mx-auto">
  <h1 className="text-3xl font-bold text-gaia-green mb-6">🎥 Video Field Scanner</h1>
  <div className="bg-white rounded-xl shadow-md p-6">
   <p className="text-gray-600 mb-3">Record a walking video of your field. Frames get batch-diagnosed on GPU.</p>
   <input type="file" accept="video/*" className="mb-3"/>
   <br/><button disabled className="bg-gray-300 px-6 py-3 rounded-lg">Coming online with GPU queue</button>
  </div>
 </div>)
}
