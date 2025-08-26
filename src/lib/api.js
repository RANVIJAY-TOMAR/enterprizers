export async function uploadFile(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/upload', { method: 'POST', body: form })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export function reportUrl(key) {
  return `/api/report/${key}`
}
