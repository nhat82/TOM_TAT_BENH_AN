import { useState } from 'react'

const PLACEHOLDER = 'Tóm tắt được tạo sẽ hiển thị ở đây...'

export default function PatientSummaryPanel({ patientId: initialPatientId }: { patientId?: string }) {
  const [patientId, setPatientId] = useState(initialPatientId ?? '')
  const [summary, setSummary] = useState('')
  const [refineInput, setRefineInput] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
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
    } catch {
      setError('Lỗi mạng — máy chủ có đang chạy không?')
    } finally {
      setIsGenerating(false)
    }
  }

  async function handleRefine() {
    if (!refineInput.trim() || !summary) return
    const prompt = refineInput
    setRefineInput('')
    setIsGenerating(true)
    setError('')
    try {
      const res = await fetch('/api/refine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, summary, ma_bn_an: patientId.trim() }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        setError(detail.detail ?? `Lỗi ${res.status}`)
        return
      }
      const data = await res.json()
      setSummary(data.summary ?? summary)
    } catch {
      setError('Chức năng tinh chỉnh chưa khả dụng.')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
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
            placeholder="vd. BN0052"
            className="w-full bg-white border border-outline-variant rounded-lg px-md py-2 text-sm focus:ring-1 focus:ring-primary focus:border-primary outline-none"
          />
        </div>

        <button
          onClick={handleGenerate}
          disabled={isGenerating || !patientId.trim()}
          className="w-full py-3 px-4 bg-primary text-white rounded-lg text-title-sm font-semibold hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <span className="material-symbols-outlined text-[20px]">
            {isGenerating ? 'hourglass_empty' : 'auto_awesome'}
          </span>
          {isGenerating ? 'Đang tạo…' : 'Tạo tóm tắt bệnh án'}
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
                disabled={isGenerating || !summary}
                className="text-primary hover:scale-110 transition-transform disabled:opacity-40"
              >
                <span className="material-symbols-outlined">send</span>
              </button>
            </div>
          </div>

          <div className="flex gap-sm pt-2">
            <button className="flex-1 py-2 px-3 border border-primary text-primary text-[11px] font-bold rounded-lg hover:bg-primary/5 transition-colors uppercase tracking-wider flex items-center justify-center gap-1">
              <span className="material-symbols-outlined text-sm">visibility</span>
              Xem trước
            </button>
            <button className="flex-1 py-2 px-3 bg-primary text-white text-[11px] font-bold rounded-lg hover:bg-primary/90 transition-colors uppercase tracking-wider flex items-center justify-center gap-1">
              <span className="material-symbols-outlined text-sm">download</span>
              Xuất DOCX
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
