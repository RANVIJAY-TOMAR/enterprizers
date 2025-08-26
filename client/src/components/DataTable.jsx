import React, { useMemo, useState } from 'react'

function toPct(v){
  if (v === null || v === undefined || Number.isNaN(v)) return ''
  return `${Math.round(Number(v))}%`
}

export default function DataTable({ rows, title }){
  const [q, setQ] = useState('')
  const filtered = useMemo(()=>{
    if (!q) return rows
    const needle = q.toLowerCase()
    return rows.filter(r => Object.values(r).some(v => String(v).toLowerCase().includes(needle)))
  }, [q, rows])

  const cols = rows?.length ? Object.keys(rows[0]) : []

  return (
    <div className="glass rounded-2xl p-4 animate-fade-in">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between mb-3">
        <h3 className="text-lg font-semibold tracking-[-0.01em]">{title}</h3>
        <input
          placeholder="Search…"
          className="px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
          value={q}
          onChange={e=>setQ(e.target.value)}
        />
      </div>
      <div className="overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="bg-slate-900/70 backdrop-blur supports-[backdrop-filter]:bg-slate-900/40">
              {cols.map(c => (
                <th key={c} className="px-3 py-2 text-left whitespace-nowrap font-medium text-slate-300 border-b border-slate-800">{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((r, i) => (
              <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
                {cols.map(c => (
                  <td key={c} className="px-3 py-2 whitespace-nowrap">
                    {c === 'Completion%' ? toPct(r[c]) : r[c]}
                  </td>
                ))}
              </tr>
            ))}
            {!rows?.length && (
              <tr><td className="px-3 py-6 text-slate-400">No data</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
