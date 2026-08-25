'use client'
import dynamic from 'next/dynamic'

const LiquidMetalHero = dynamic(
  () => import('@/components/ui/liquid-metal-hero'),
  { ssr: false }
)

export default function Home() {
  return <LiquidMetalHero
    badge="GAIA v3.0 · Production"
    title="GAIA"
    subtitle="AI crop disease, pest, soil and livestock diagnosis. Your pocket agronomist — instant answers, no agronomist visit needed."
    primaryCta="Start Diagnosing"
    primaryHref="/crops"
    secondaryCta="Explore Tools"
    secondaryHref="/wallet"
    features={[
      "152 Diagnostic Classes",
      "10+ Crop Models",
      "24/7 Offline Ready"
    ]}
  />
}
