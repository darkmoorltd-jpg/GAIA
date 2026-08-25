'use client'
import { useState } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'https://maxvwede-source--gaiya-backend-fastapi-app.modal.run'

export default function Page() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    if (!file) return
    setLoading(true); setError('')
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('crop', 'maize')
      const res = await fetch(`${API}/api/v1/crops/maize/diagnose`, { method: 'POST', body: fd })
      setResult(await res.json())
    } catch { setError('Network error. Please try again.') } finally { setLoading(false) }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-primary-700 mb-2 font-[family-name:var(--font-heading)]">🌿 Crop Disease Diagnosis</h1>
      <p className="text-gray-500 text-sm mb-6">Upload a clear photo of the affected leaf for AI analysis.</p>

      <form onSubmit={e => { e.preventDefault(); handleSubmit() }} className="space-y-4">
        <div>
          <label htmlFor="leaf-photo" className="block text-sm font-medium text-gray-700 mb-1">
            Leaf Photo <span className="text-red-500">*</span>
          </label>
          <input
            id="leaf-photo"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={e => setFile(e.target.files?.[0] || null)}
            className="w-full border-2 border-dashed border-gray-300 rounded-xl px-4 py-8 text-center cursor-pointer hover:border-primary-400 transition-colors bg-white"
          />
          <p className="text-xs text-gray-400 mt-1">JPEG, PNG or WebP · Max 5MB</p>
        </div>

        <button
          type="submit"
          disabled={!file || loading}
          className="w-full bg-primary-600 text-white px-6 py-3 rounded-xl font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-primary-700 active:scale-[0.98] transition-all min-h-[48px]"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              Analyzing...
            </span>
          ) : 'Upload & Diagnose'}
        </button>
      </form>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">{error}</div>
      )}

      {result && !result.error && (
        <div className="mt-6 bg-white rounded-2xl shadow-md border border-green-100 overflow-hidden">
          <div className="bg-primary-600 text-white p-4"><h2 className="font-bold">Diagnosis Result</h2></div>
          <div className="p-6 space-y-3">
            <div className="flex items-center gap-3">
              <span className={`inline-block w-3 h-3 rounded-full ${result.diagnosis === 'Healthy' ? 'bg-green-500' : 'bg-yellow-500'}`} />
              <span className="font-bold text-lg">{result.diagnosis}</span>
            </div>
            <div>
              <p className="text-sm text-gray-500 mb-1">Confidence</p>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div className="bg-primary-600 h-2.5 rounded-full transition-all duration-500" style={{ width: `${result.confidence}%` }} />
              </div>
              <p className="text-sm font-semibold mt-1">{result.confidence}%</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
