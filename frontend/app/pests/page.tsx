'use client'
import { useState } from 'react'
import axios from 'axios'

export default function PestsPage() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<any>(null)

  const handleUpload = async () => {
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/pests/diagnose`, formData)
      setResult(res.data)
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold text-gaia-green mb-6">🐛 Pest Detection</h1>
      <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="mb-4" />
      <button onClick={handleUpload} className="bg-gaia-green text-white px-6 py-3 rounded-lg">
        Upload & Detect
      </button>
      {result && (
        <div className="mt-6 bg-white p-6 rounded-xl shadow">
          <h2 className="font-bold">{result.diagnosis}</h2>
          <p>Confidence: {result.confidence.toFixed(1)}%</p>
        </div>
      )}
    </div>
  )
}
