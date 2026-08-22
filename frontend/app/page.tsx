'use client'
import { motion } from 'framer-motion'
import Link from 'next/link'

export default function Home() {
  return (
    <div className="max-w-6xl mx-auto">
      <motion.h1
        className="text-5xl font-extrabold text-center text-gaia-green mb-4"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        🌱 GAIA
      </motion.h1>
      <p className="text-center text-gray-600 mb-10">
        Global Agricultural Intelligence Assistant
      </p>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Link href="/crops">
          <div className="bg-white rounded-xl shadow-md p-6 cursor-pointer hover:shadow-lg transition">
            <div className="text-3xl mb-3">🌿</div>
            <h3 className="font-semibold text-lg">Crop Disease</h3>
            <p className="text-sm text-gray-500">Detect diseases from leaf photos</p>
          </div>
        </Link>
        <Link href="/pests">
          <div className="bg-white rounded-xl shadow-md p-6 cursor-pointer hover:shadow-lg transition">
            <div className="text-3xl mb-3">🐛</div>
            <h3 className="font-semibold text-lg">Pest Detection</h3>
            <p className="text-sm text-gray-500">Identify 102 insect pests</p>
          </div>
        </Link>
        <Link href="/soil">
          <div className="bg-white rounded-xl shadow-md p-6 cursor-pointer hover:shadow-lg transition">
            <div className="text-3xl mb-3">🏞️</div>
            <h3 className="font-semibold text-lg">Soil Analysis</h3>
            <p className="text-sm text-gray-500">Classify 11 soil types</p>
          </div>
        </Link>
        <Link href="/livestock">
          <div className="bg-white rounded-xl shadow-md p-6 cursor-pointer hover:shadow-lg transition">
            <div className="text-3xl mb-3">🐄</div>
            <h3 className="font-semibold text-lg">Livestock Health</h3>
            <p className="text-sm text-gray-500">Cattle & poultry diagnosis</p>
          </div>
        </Link>
      </div>
    </div>
  )
}
