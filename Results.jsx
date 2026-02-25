import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Clipboard, Download, FileJson } from 'lucide-react'
import { jsPDF } from 'jspdf'

const riskColor = (label) => {
  switch(label){
    case 'Safe': return 'bg-emerald-500'
    case 'Adjust Dosage': return 'bg-yellow-400'
    case 'Toxic': return 'bg-red-500'
    case 'Ineffective': return 'bg-red-500'
    default: return 'bg-slate-400'
  }
}

function ReportCard({ report }){
  const [open, setOpen] = useState(false)
  const jsonStr = JSON.stringify(report, null, 2)

  const copyJSON = async () => {
    await navigator.clipboard.writeText(jsonStr)
    alert('JSON copied to clipboard')
  }

  const downloadTxt = () => {
    const blob = new Blob([jsonStr], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.patient_id}_${report.drug}_report.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadPDF = () => {
    const doc = new jsPDF()
    doc.setFontSize(14)
    doc.text('MediSphere Pharmacogenomic Report', 14, 16)
    doc.setFontSize(10)
    const lines = doc.splitTextToSize(jsonStr, 180)
    doc.text(lines, 14, 26)
    doc.save(`${report.patient_id}_${report.drug}_report.pdf`)
  }

  const color = riskColor(report?.risk_assessment?.risk_label)

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="rounded-2xl bg-white/5 border border-white/10 overflow-hidden hover:bg-white/7 transition"
    >
      <div className="p-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm text-slate-900 ${color}`}>{report.risk_assessment.risk_label}</span>
          <div>
            <div className="text-white font-semibold">{report.drug}</div>
            <div className="text-xs text-slate-300">{report.timestamp}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={copyJSON} className="px-3 py-2 rounded-lg bg-slate-800 text-slate-200 border border-white/10 hover:bg-slate-700 transition">
            <Clipboard className="w-4 h-4" />
          </button>
          <button onClick={downloadTxt} className="px-3 py-2 rounded-lg bg-slate-800 text-slate-200 border border-white/10 hover:bg-slate-700 transition">
            <Download className="w-4 h-4" /> TXT
          </button>
          <button onClick={downloadPDF} className="px-3 py-2 rounded-lg bg-slate-800 text-slate-200 border border-white/10 hover:bg-slate-700 transition">
            <Download className="w-4 h-4" /> PDF
          </button>
          <button onClick={()=>setOpen(v=>!v)} className="px-3 py-2 rounded-lg bg-cyan-500 text-slate-900 font-semibold hover:bg-cyan-400 inline-flex items-center gap-1 transition">
            <FileJson className="w-4 h-4" /> Details
            <ChevronDown className={`w-4 h-4 transition ${open ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>
      <AnimatePresence>
        {open && (
          <motion.div initial={{height:0, opacity:0}} animate={{height:'auto', opacity:1}} exit={{height:0, opacity:0}} className="border-t border-white/10">
            <div className="grid md:grid-cols-3 gap-6 p-6">
              <div>
                <h4 className="text-slate-200 font-semibold mb-2">Pharmacogenomic Profile</h4>
                <div className="text-sm text-slate-300 space-y-1">
                  <div>Primary Gene: <span className="font-medium text-white">{report.pharmacogenomic_profile.primary_gene}</span></div>
                  <div>Diplotype: <span className="font-medium text-white">{report.pharmacogenomic_profile.diplotype}</span></div>
                  <div>Phenotype: <span className="font-medium text-white">{report.pharmacogenomic_profile.phenotype}</span></div>
                  <div>Variants:
                    <ul className="list-disc list-inside">
                      {report.pharmacogenomic_profile.detected_variants.map((v,i)=> (
                        <li key={i} className="text-cyan-200">{v.rsid}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
              <div>
                <h4 className="text-slate-200 font-semibold mb-2">Clinical Recommendation</h4>
                <div className="text-sm text-slate-300 space-y-1">
                  <div>CPIC: <span className="text-white">{report.clinical_recommendation.cpic_guideline_reference}</span></div>
                  <div>Action: <span className="text-white">{report.clinical_recommendation.recommended_action}</span></div>
                  <div>Dose: <span className="text-white">{report.clinical_recommendation.dose_adjustment || 'None'}</span></div>
                </div>
              </div>
              <div>
                <h4 className="text-slate-200 font-semibold mb-2">AI Explanation</h4>
                <div className="text-sm text-slate-300 space-y-2">
                  <div><span className="text-white">Summary:</span> {report.llm_generated_explanation.summary}</div>
                  <div><span className="text-white">Mechanism:</span> {report.llm_generated_explanation.mechanism}</div>
                  <div><span className="text-white">Clinical Significance:</span> {report.llm_generated_explanation.clinical_significance}</div>
                </div>
              </div>
            </div>
            <div className="bg-slate-900/50 p-4">
              <h4 className="text-slate-200 font-semibold mb-2">JSON Output</h4>
              <pre className="text-xs text-cyan-100 whitespace-pre-wrap bg-slate-800 rounded-lg p-4 border border-white/10 overflow-auto max-h-64">{jsonStr}</pre>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default function Results({ data }){
  if (!data) return null
  return (
    <div className="space-y-4">
      {data.reports?.map((r, idx)=> (
        <ReportCard key={idx} report={r} />
      ))}
      <div className="text-xs text-slate-300">vcf_parsing_success: {String(data.reports?.[0]?.quality_metrics?.vcf_parsing_success)}</div>
    </div>
  )
}
