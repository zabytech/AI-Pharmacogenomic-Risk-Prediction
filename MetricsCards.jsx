import React from 'react'
import { motion } from 'framer-motion'

const toneClass = (tone) => {
  switch (tone) {
    case 'blue':
      return 'bg-blue-500/10 border-blue-400/30'
    case 'violet':
      return 'bg-violet-500/10 border-violet-400/30'
    case 'emerald':
      return 'bg-emerald-500/10 border-emerald-400/30'
    default:
      return 'bg-cyan-500/10 border-cyan-400/30'
  }
}

const Card = ({ title, value, tone='cyan', delay=0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay }}
    className={`rounded-xl p-5 ${toneClass(tone)} backdrop-blur-sm`}
  >
    <div className="text-sm text-slate-200/80">{title}</div>
    <div
      className="mt-1 text-2xl font-bold text-white break-all overflow-hidden text-ellipsis"
      title={typeof value === 'string' ? value : String(value)}
    >
      {value}
    </div>
  </motion.div>
)

export default function MetricsCards({ summary }) {
  if (!summary) return null
  return (
    <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4">
      <Card title="Total Variants" value={summary.total_variants} tone="cyan" delay={0.05} />
      <Card title="Genes Covered" value={summary.genes_covered?.length || 0} tone="blue" delay={0.1} />
      <Card title="RS IDs Detected" value={summary.rsids_detected?.length || 0} tone="violet" delay={0.15} />
      <Card title="Patient ID" value={summary.patient_id} tone="emerald" delay={0.2} />
    </div>
  )
}
