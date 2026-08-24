"use client"
import { useMemo } from "react"

export default function PageBackground({ 
  imageUrl, 
  overlay = 0.35,
  particles = true 
}: { 
  imageUrl: string; 
  overlay?: number;
  particles?: boolean;
}) {
  const dots = useMemo(() => {
    if (!particles) return []
    return Array.from({ length: 15 }, (_, i) => ({
      id: i,
      left: `${(i * 37 + 13) % 100}%`,
      size: 3 + (i % 4),
      delay: `${(i * 0.7) % 8}s`,
      duration: `${6 + (i % 5)}s`,
      opacity: 0.15 + (i % 3) * 0.1,
    }))
  }, [particles])

  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
      {/* Background image */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${imageUrl})` }}
      />
      {/* Color overlay */}
      <div
        className="absolute inset-0"
        style={{
          background: `linear-gradient(to bottom, rgba(244,250,245,${overlay + 0.25}), rgba(244,250,245,${overlay + 0.15}), rgba(255,255,255,${overlay + 0.35}))`,
        }}
      />
      {/* Antigravity floating particles */}
      {particles && (
        <div className="absolute inset-0">
          {dots.map((d) => (
            <div
              key={d.id}
              className="absolute rounded-full bg-gaia-green animate-[floatUp_8s_ease-in-out_infinite]"
              style={{
                left: d.left,
                width: d.size,
                height: d.size,
                bottom: "-10px",
                opacity: d.opacity,
                animationDelay: d.delay,
                animationDuration: d.duration,
                boxShadow: "0 0 6px rgba(46,125,50,0.3)",
              }}
            />
          ))}
        </div>
      )}
    </div>
  )
}
