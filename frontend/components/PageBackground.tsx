"use client"
import dynamic from "next/dynamic"
const Antigravity = dynamic(() => import("./Antigravity"), { ssr: false })

export default function PageBackground({
  imageUrl = "",
  overlay = 0.35,
  count = 150,
  color = "#2e7d32",
}: {
  imageUrl?: string;
  overlay?: number;
  count?: number;
  color?: string;
}) {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
      {/* Unsplash background image */}
      {imageUrl && (
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: `url(${imageUrl})` }}
        />
      )}
      {/* Light overlay so text is readable but particles show through */}
      <div
        className="absolute inset-0"
        style={{
          background: `linear-gradient(to bottom, rgba(244,250,245,${overlay + 0.15}), rgba(255,255,255,${overlay + 0.25}))`,
        }}
      />
      {/* REAL Antigravity 3D particles */}
      <div className="absolute inset-0 opacity-40">
        <Antigravity count={count} color={color} particleShape="capsule" autoAnimate magnetRadius={8} ringRadius={6} particleSize={1.5} />
      </div>
    </div>
  )
}
