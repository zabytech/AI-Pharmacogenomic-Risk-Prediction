import React from 'react'
import { motion } from 'framer-motion'

/*
  MediSphere Futuristic Biotech + Clinical Monogram (Neon MS)
  - No enclosing circle/frame
  - Large MS with neon glow and minimal accent bars
  - Professional geometric sans (Inter/system-ui/Arial)
*/

export default function Logo({ size = 180, showWordmark = false, animated = false }) {
  const w = size
  const h = Math.round(size * 0.66)
  const fontFamily = 'Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif'
  const MSize = Math.max(36, Math.floor(size * 0.44))
  const SSize = Math.max(36, Math.floor(size * 0.44))

  const Mark = (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="drop-shadow-[0_12px_40px_rgba(14,165,233,0.2)]">
      <defs>
        <filter id="neonCyan" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="neonBlue" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <linearGradient id="underlineGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#22d3ee" />
          <stop offset="100%" stopColor="#60a5fa" />
        </linearGradient>
      </defs>

      {/* Accent bars (subtle, clinical) */}
      <rect x={w*0.12} y={h*0.68} width={w*0.28} height={2} fill="url(#underlineGrad)" opacity="0.7" />
      <rect x={w*0.60} y={h*0.68} width={w*0.20} height={2} fill="url(#underlineGrad)" opacity="0.7" />

      {/* Monogram */}
      <text x={w*0.35} y={h*0.6} textAnchor="middle" fontFamily={fontFamily} fontSize={MSize} fontWeight={900} fill="#60a5fa" filter="url(#neonBlue)">M</text>
      <text x={w*0.65} y={h*0.6} textAnchor="middle" fontFamily={fontFamily} fontSize={SSize} fontWeight={900} fill="#22d3ee" filter="url(#neonCyan)">S</text>
    </svg>
  )

  const Wordmark = (
    <div className="text-center">
      <div className="font-black tracking-tight" style={{ fontSize: Math.max(18, Math.floor(size * 0.22)), fontFamily, letterSpacing: '-0.01em' }}>
        MediSphere
      </div>
      <div className="mt-0.5 text-xs md:text-sm text-slate-300" style={{ fontFamily, letterSpacing: '0.14em' }}>
        AI Pharmacogenomics
      </div>
    </div>
  )

  if (animated) {
    return (
      <div className="inline-flex flex-col items-center">
        <motion.div initial={{ scale: 0.96, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ duration: 0.6, ease: 'easeOut' }}>
          {Mark}
        </motion.div>
        {showWordmark && (
          <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }} className="mt-3">
            {Wordmark}
          </motion.div>
        )}
      </div>
    )
  }

  return (
    <div className="inline-flex flex-col items-center">
      {Mark}
      {showWordmark && <div className="mt-3">{Wordmark}</div>}
    </div>
  )
}
