"use client"

import { useEffect, useState } from "react"
import dynamic from "next/dynamic"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { motion } from "framer-motion"

const Shaders = dynamic(
  () => import("@paper-design/shaders-react").then((m) => ({ default: m.LiquidMetal })),
  { ssr: false }
)

export default function LiquidMetalHero({
  badge = "GAIA v3.0",
  title = "GAIA",
  subtitle = "AI crop disease, pest, soil and livestock diagnosis — your pocket agronomist.",
  primaryCta = "Start Diagnosing",
  primaryHref = "/crops",
  secondaryCta = "Explore Tools",
  secondaryHref = "/wallet",
  features = [],
}: {
  badge?: string
  title?: string
  subtitle?: string
  primaryCta?: string
  primaryHref?: string
  secondaryCta?: string
  secondaryHref?: string
  features?: string[]
}) {
  const [presets, setPresets] = useState<any>(null)

  useEffect(() => {
    import("@paper-design/shaders-react").then((m) => {
      setPresets((m as any).liquidMetalPresets || (m as any).default?.liquidMetalPresets)
    })
  }, [])

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { delayChildren: 0.2, staggerChildren: 0.15 } },
  }
  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0 },
  }

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden -mx-4 md:mx-0 -mt-14 md:mt-0">
      {presets && presets[2] && (
        <Shaders
          {...presets[2]}
          style={{ position: "fixed", inset: 0, zIndex: -10 }}
        />
      )}

      <div className="container mx-auto px-6 lg:px-8 max-w-7xl relative z-10">
        <motion.div
          className="text-center space-y-8"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          transition={{ duration: 0.8, ease: [0.25, 0.1, 0.25, 1] }}
        >
          {badge && (
            <motion.div className="flex justify-center" variants={itemVariants}>
              <Badge
                variant="secondary"
                className="bg-white/10 text-white border-white/20 hover:bg-white/20 transition-colors duration-300 backdrop-blur-sm px-4 py-1.5"
              >
                {badge}
              </Badge>
            </motion.div>
          )}

          <motion.div className="space-y-6" variants={itemVariants}>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl xl:text-8xl font-extrabold text-white leading-tight tracking-tight">
              {title}
            </h1>
            <p className="max-w-2xl mx-auto text-lg sm:text-xl text-white/80 leading-relaxed">
              {subtitle}
            </p>
          </motion.div>

          <motion.div
            className="flex flex-col sm:flex-row gap-4 justify-center items-center"
            variants={itemVariants}
          >
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                size="lg"
                className="bg-white text-foreground hover:bg-white/90 transition-all duration-300 shadow-2xl text-base px-8 py-6 font-semibold"
                onClick={() => (window.location.href = primaryHref)}
              >
                {primaryCta}
              </Button>
            </motion.div>

            {secondaryCta && (
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  variant="outline"
                  size="lg"
                  className="border-white/30 text-white hover:bg-white/10 hover:border-white/50 transition-all duration-300 backdrop-blur-sm text-base px-8 py-6 font-semibold"
                  onClick={() => (window.location.href = secondaryHref)}
                >
                  {secondaryCta}
                </Button>
              </motion.div>
            )}
          </motion.div>

          {features.length > 0 && (
            <motion.div className="pt-10" variants={itemVariants}>
              <Card className="bg-white/10 border-white/20 backdrop-blur-md shadow-2xl">
                <div className="p-6 md:p-8">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {features.map((f, i) => (
                      <motion.p
                        key={i}
                        className="text-white/90 font-medium text-base md:text-lg"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.5, delay: 0.8 + i * 0.1 }}
                      >
                        {f}
                      </motion.p>
                    ))}
                  </div>
                </div>
              </Card>
            </motion.div>
          )}
        </motion.div>
      </div>
    </section>
  )
}
