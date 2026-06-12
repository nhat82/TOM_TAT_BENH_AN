import { useState } from 'react'

const PLACEHOLDER = 'Tóm tắt được tạo sẽ hiển thị ở đây...'

export default function PatientSummaryPanel({ patientId: initialPatientId }: { patientId?: string }) {
  const [patientId, setPatientId] = useState(initialPatientId ?? '')
  const [summary, setSummary] = useState('')
  const [refineInput, setRefineInput] = useState('')
  const [refineHistory, setRefineHistory] = useState<{ instruction: string; result_summary: string }[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [isRefining, setIsRefining] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [isPreviewing, setIsPreviewing] = useState(false)
  const [previewHtml, setPreviewHtml] = useState<string | null>(null)
  const [error, setError] = useState('')

  async function handleGenerate() {
    if (!patientId.trim()) return
    setIsGenerating(true)
    setError('')
    try {
      const res = await fetch('/api/summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ma_bn_an: patientId.trim() }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        setError(detail.detail ?? `Lỗi ${res.status}`)
        return
      }
      const data = await res.json()
      setSummary(data.summary ?? '')
      setRefineHistory([])
    } catch {
      setError('Lỗi mạng — máy chủ có đang chạy không?')
    } finally {
      setIsGenerating(false)
    }
  }

  async function handlePreview() {
    if (!summary || !patientId.trim()) return
    setIsPreviewing(true)
    setError('')
    try {
      const res = await fetch('/api/preview-html', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ma_bn_an: patientId.trim(), summary }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        setError(detail.detail ?? `Lỗi ${res.status}`)
        return
      }
      const html = await res.text()
      setPreviewHtml(html)
    } catch {
      setError('Lỗi mạng — máy chủ có đang chạy không?')
    } finally {
      setIsPreviewing(false)
    }
  }

  async function handleExport() {
    if (!summary || !patientId.trim()) return
    setIsExporting(true)
    setError('')
    try {
      const res = await fetch('/api/export-docx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ma_bn_an: patientId.trim(), summary }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        setError(detail.detail ?? `Lỗi ${res.status}`)
        return
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tom_tat_${patientId.trim()}.docx`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('Lỗi mạng — máy chủ có đang chạy không?')
    } finally {
      setIsExporting(false)
    }
  }

  async function handleRefine() {
    if (!refineInput.trim() || !summary) return
    const prompt = refineInput
    setRefineInput('')
    setIsRefining(true)
    setError('')
    try {
      const res = await fetch('/api/refine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, summary, ma_bn_an: patientId.trim(), history: refineHistory }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        setError(detail.detail ?? `Lỗi ${res.status}`)
        return
      }
      const data = await res.json()
      const refined = data.summary ?? summary
      setRefineHistory(h => [...h, { instruction: prompt, result_summary: refined }])
      setSummary(refined)
    } catch {
      setError('Lỗi mạng — máy chủ có đang chạy không?')
    } finally {
      setIsRefining(false)
    }
  }

  return (
    <>
    <div className="bg-surface-container border border-outline rounded-xl flex flex-col mb-lg shadow-sm overflow-hidden">
      <div className="px-lg py-md border-b border-outline flex items-center gap-md bg-white">
        <span className="material-symbols-outlined text-primary">description</span>
        <h3 className="text-title-sm font-semibold text-on-surface">Tóm tắt bệnh án</h3>
      </div>

      <div className="p-lg space-y-md">
        <div className="flex flex-col gap-xs">
          <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">
            Mã bệnh nhân
          </label>
          <input
            type="text"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            placeholder="vd. BN0012"
            className="w-full bg-white border border-outline-variant rounded-lg px-md py-2 text-sm focus:ring-1 focus:ring-primary focus:border-primary outline-none"
          />
        </div>

        <button
          onClick={handleGenerate}
          disabled={isGenerating || isRefining || !patientId.trim()}
          className="w-full py-3 px-4 bg-primary text-white rounded-lg text-title-sm font-semibold hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <span className="material-symbols-outlined text-[20px]">
            {isGenerating || isRefining ? 'hourglass_empty' : 'auto_awesome'}
          </span>
          {isGenerating ? 'Đang tạo…' : isRefining ? 'Đang tinh chỉnh…' : 'Tạo tóm tắt bệnh án'}
        </button>

        {error && (
          <p className="text-xs text-error bg-error-container rounded-lg px-md py-2">{error}</p>
        )}

        <div className="space-y-md">
          <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">
            Bản thảo tóm tắt
          </label>
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            className="w-full h-[400px] p-md bg-white border border-outline-variant rounded-lg text-sm text-on-surface focus:ring-1 focus:ring-primary focus:border-primary outline-none resize-none leading-relaxed"
            placeholder={PLACEHOLDER}
          />

          <div className="space-y-sm">
            <label className="text-[10px] font-bold text-primary uppercase tracking-widest flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">auto_fix</span>
              Tinh chỉnh với AI
            </label>
            <div className="flex items-center gap-sm bg-white px-md py-2 rounded-full border border-outline-variant focus-within:border-primary/50 transition-all">
              <input
                type="text"
                value={refineInput}
                onChange={(e) => setRefineInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleRefine()}
                placeholder="Yêu cầu AI chỉnh sửa bản thảo..."
                className="flex-1 bg-transparent border-none focus:ring-0 text-body-sm py-1 placeholder:text-on-surface-variant/50 outline-none"
              />
              <button
                onClick={handleRefine}
                disabled={isGenerating || isRefining || !summary}
                className="text-primary hover:scale-110 transition-transform disabled:opacity-40"
              >
                <span className="material-symbols-outlined">
                  {isRefining ? 'hourglass_empty' : 'send'}
                </span>
              </button>
            </div>
          </div>

          <div className="flex gap-sm pt-2">
            <button
              onClick={handlePreview}
              disabled={isPreviewing || !summary}
              className="flex-1 py-2 px-3 border border-primary text-primary text-[11px] font-bold rounded-lg hover:bg-primary/5 transition-colors uppercase tracking-wider flex items-center justify-center gap-1 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined text-sm">
                {isPreviewing ? 'hourglass_empty' : 'visibility'}
              </span>
              {isPreviewing ? 'Đang tải…' : 'Xem trước'}
            </button>
            <button
              onClick={handleExport}
              disabled={isExporting || !summary}
              className="flex-1 py-2 px-3 bg-primary text-white text-[11px] font-bold rounded-lg hover:bg-primary/90 transition-colors uppercase tracking-wider flex items-center justify-center gap-1 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined text-sm">
                {isExporting ? 'hourglass_empty' : 'download'}
              </span>
              {isExporting ? 'Đang xuất…' : 'Xuất DOCX'}
            </button>
          </div>
        </div>
      </div>
    </div>

    {previewHtml && (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
        onClick={() => setPreviewHtml(null)}
      >
        <div
          className="bg-white rounded-xl shadow-2xl w-full max-w-4xl h-[96vh] flex flex-col"
          onClick={e => e.stopPropagation()}
        >
          <div className="flex items-center justify-between px-6 py-3 border-b border-outline shrink-0">
            <span className="text-sm font-semibold text-on-surface">Xem trước tóm tắt</span>
            <button
              onClick={() => setPreviewHtml(null)}
              className="text-on-surface-variant hover:text-on-surface transition-colors"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>

          <iframe
            srcDoc={previewHtml ?? undefined}
            className="flex-1 w-full border-none min-h-[200px]"
            title="Xem trước tóm tắt bệnh án"
          />

          <div className="flex items-center gap-sm px-6 py-3 border-t border-outline shrink-0">
            <button
              onClick={() => setPreviewHtml(null)}
              className="ml-auto px-4 py-2 bg-primary text-white rounded-lg text-xs font-bold hover:bg-primary/90 transition-colors uppercase tracking-wider"
            >
              Đóng
            </button>
          </div>
        </div>
      </div>
    )}
    </>
  )
}
