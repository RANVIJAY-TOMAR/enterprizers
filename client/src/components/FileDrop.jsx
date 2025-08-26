import React, { useCallback, useRef, useState } from 'react'

export default function FileDrop({ onFile }) {
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false)
    const f = e.dataTransfer.files?.[0]
    if (f) onFile(f)
  }, [onFile])

  return (
    <div
      onDragOver={(e)=>{e.preventDefault(); setDragOver(true)}}
      onDragLeave={()=>setDragOver(false)}
      onDrop={onDrop}
      className={`glass rounded-2xl p-8 text-center cursor-pointer transition-colors relative overflow-hidden ${dragOver ? 'border-brand-500/50' : ''}`}
      onClick={()=>inputRef.current?.click()}
    >
      <div className={`absolute inset-0 pointer-events-none transition-opacity duration-300 ${dragOver ? 'opacity-100' : 'opacity-0'}`} style={{background: 'radial-gradient(600px 240px at 50% -20%, rgba(99,102,241,0.18), transparent 60%)'}} />
      <input ref={inputRef} type="file" accept=".xlsx,.xls,.csv" className="hidden"
             onChange={(e)=>{ if (e.target.files?.[0]) onFile(e.target.files[0]) }} />
      <div className="text-xl font-medium tracking-[-0.01em]">
        Drop your Excel/CSV here or <span className="text-brand-400 underline underline-offset-4">browse</span>
      </div>
      <div className="text-sm text-slate-400 mt-2">Supports ~50k × 100 — include Zone, Client Name, Order Status</div>
    </div>
  )
}
