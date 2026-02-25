import React, { useState } from 'react'
import { MessageCircle } from 'lucide-react'

export default function Chatbot({ patientId }){
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const send = async () => {
    if (!input) return
    const userMsg = { role: 'user', message: input }
    setMessages((m)=>[...m, userMsg])
    setInput('')
    setLoading(true)
    try {
      const res = await fetch(`${import.meta.env.VITE_BACKEND_URL || ''}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: patientId, message: userMsg.message, provider: 'openai' })
      })
      const data = await res.json()
      setMessages((m)=>[
        ...m,
        { role: 'assistant', message: data.reply },
        { role: 'assistant', message: `Disclaimer: ${data.disclaimer}` }
      ])
    } catch (e) {
      setMessages((m)=>[...m, { role: 'assistant', message: 'Sorry, something went wrong.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-2xl bg-white/5 border border-white/10 p-5">
      <div className="flex items-center gap-2 mb-3">
        <MessageCircle className="w-5 h-5 text-cyan-300" />
        <h3 className="text-white font-semibold">AI Supportive Chatbot (GPT)</h3>
      </div>
      <div className="space-y-3 max-h-64 overflow-auto">
        {messages.map((m, idx)=> (
          <div key={idx} className={`text-sm ${m.role==='user' ? 'text-cyan-200' : 'text-slate-200'}`}>{m.message}</div>
        ))}
      </div>
      <div className="mt-4 flex gap-2">
        <input
          value={input}
          onChange={(e)=>setInput(e.target.value)}
          placeholder="Ask about risks, dosage, or genetics"
          className="flex-1 px-4 py-3 rounded-lg bg-slate-800 text-white border border-white/10 focus:outline-none focus:ring-2 focus:ring-cyan-400"
        />
        <button onClick={send} className="px-4 py-3 rounded-lg bg-cyan-500 text-slate-900 font-semibold hover:bg-cyan-400" disabled={loading}>
          {loading ? 'Sending…' : 'Send'}
        </button>
      </div>
      <p className="mt-2 text-xs text-slate-400">This chatbot uses GPT and provides educational guidance. Not a substitute for professional medical advice.</p>
    </div>
  )
}
