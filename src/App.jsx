import React, { useState } from 'react'
import FileDrop from './components/FileDrop'
import DataTable from './components/DataTable'
import { uploadFile, reportUrl } from './lib/api'

export default function App(){
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [result, setResult] = useState(null)
  const [fileName, setFileName] = useState('')
  const [downloading, setDownloading] = useState(false)

  async function handleFile(file){
    setErr(''); setBusy(true); setResult(null); setFileName(file.name)
    try{
      const data = await uploadFile(file)
      setResult(data)
    }catch(e){
      setErr(e.message || 'Upload failed')
    }finally{
      setBusy(false)
    }
  }

  async function handleDownload(){
    if (!result?.report_key || downloading) return
    setErr(''); setDownloading(true)
    try{
      const url = reportUrl(result.report_key)
      const res = await fetch(url)
      if (!res.ok) throw new Error(`Download failed (${res.status})`)
      const blob = await res.blob()
      // Try to extract filename from Content-Disposition
      const cd = res.headers.get('content-disposition') || ''
      let name = 'report.xlsx'
      const match = cd.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i)
      if (match) name = decodeURIComponent(match[1] || match[2])
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = name
      document.body.appendChild(link)
      link.click()
      link.remove()
      setTimeout(()=>URL.revokeObjectURL(link.href), 0)
    }catch(e){
      try{
        const url = reportUrl(result.report_key)
        window.location.assign(url)
      }catch(_){}
      setErr(e.message || 'Download failed')
    }finally{
      setDownloading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-[-0.02em]">Excel Summarizer</h1>
            <p className="text-slate-400 mt-1">Upload your Excel/CSV and get client‑wise and zone‑wise insights.</p>
          </div>
          <div className="hidden md:flex items-center gap-2 text-xs text-slate-500">
            <span className="px-2 py-1 rounded-md border border-slate-700 bg-slate-900/60">Fast</span>
            <span className="px-2 py-1 rounded-md border border-slate-700 bg-slate-900/60">Accurate</span>
            <span className="px-2 py-1 rounded-md border border-slate-700 bg-slate-900/60">Secure</span>
          </div>
        </div>
      </header>

      <div className="grid gap-6">
        <FileDrop onFile={handleFile} />

        {busy && (
          <div className="glass rounded-2xl p-5 animate-fade-in">
            <div className="mb-2">Analyzing <span className="font-medium">{fileName}</span>…</div>
            <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
              <div className="h-2 rounded-full bg-brand-500" style={{width:'60%'}} />
            </div>
          </div>
        )}

        {err && (
          <div className="rounded-2xl border border-red-800/60 bg-red-950/30 text-red-300 p-4 animate-fade-in">
            {err}
          </div>
        )}

        {result && (
          <div className="space-y-6 animate-fade-in">
            <div className="flex flex-wrap gap-3 items-center">
              <button
                type="button"
                onClick={handleDownload}
                disabled={downloading}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 disabled:cursor-not-allowed transition-colors shadow-soft"
              >
                {downloading ? 'Preparing…' : 'Download Excel Report'}
              </button>
              {!!result?.report_key && (
                <a
                  href={reportUrl(result.report_key)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-slate-400 hover:text-slate-200 underline underline-offset-4"
                >
                  Open directly
                </a>
              )}
              <div className="text-slate-400 text-sm">Includes Raw, Client Summary, Zone Summary</div>
            </div>
            <DataTable title="Zone × Client Summary" rows={result.client_summary} />
            <DataTable title="Zone Rollup" rows={result.zone_summary} />
          </div>
        )}
      </div>

      <footer className="mt-12 text-center text-slate-500 text-xs"></footer>
    </div>
  )
}
