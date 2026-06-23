import { useState } from 'react'
import { createPortal } from 'react-dom'

const SUMMARY_FIELDS: { key: string; label: string }[] = [
  { key: 'tom_tat_qua_trinh_dien_bien', label: 'Quá trình bệnh lý và diễn biến lâm sàng' },
  { key: 'tien_su_benh',                label: 'Tiền sử bệnh' },
  { key: 'dau_hieu_chinh',              label: 'Dấu hiệu lâm sàng chính' },
  { key: 'tom_tat_ket_qua',             label: 'Kết quả xét nghiệm / cận lâm sàng' },
  { key: 'pttt',                        label: 'Phẫu thuật / thủ thuật' },
  { key: 'tinh_trang_ra_vien',          label: 'Tình trạng ra viện' },
  { key: 'huongdieutri_out',            label: 'Hướng điều trị tiếp theo' },
  { key: 'chandoan_in_icd10',           label: 'Mã ICD-10 vào viện' },
  { key: 'chandoan_out_main_icd10',     label: 'Mã ICD-10 ra viện' },
]

function parseSummaryJson(s: string): Record<string, string> | null {
  try {
    const parsed = JSON.parse(s)
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as Record<string, string>
    }
  } catch {}
  return null
}

interface SummaryVersion {
  text: string
  src: string
  time: string
}

function formatTime(): string {
  const d = new Date()
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function truncate(s: string, n = 36): string {
  return s.length > n ? s.slice(0, n) + '…' : s
}

export default function PatientSummaryPanel({ patientId }: { patientId?: string }) {
  const [versions, setVersions] = useState<SummaryVersion[]>([])
  const [vIndex, setVIndex] = useState(-1)
  const [refineInput, setRefineInput] = useState('')
  const [refineHistory, setRefineHistory] = useState<{ instruction: string; result_summary: string }[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [isRefining, setIsRefining] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [isPreviewing, setIsPreviewing] = useState(false)
  const [previewHtml, setPreviewHtml] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null)
  const [showReason, setShowReason] = useState(false)
  const [reason, setReason] = useState('')
  const [feedbackSent, setFeedbackSent] = useState(false)

  const curVersion = vIndex >= 0 ? versions[vIndex] : null
  const summary = curVersion?.text ?? ''

  function pushVersion(text: string, src: string) {
    const v: SummaryVersion = { text, src, time: formatTime() }
    setVersions(prev => {
      const next = [...prev, v]
      setVIndex(next.length - 1)
      return next
    })
    setFeedback(null)
    setShowReason(false)
    setReason('')
    setFeedbackSent(false)
  }

  function editSummary(val: string) {
    setVersions(prev => prev.map((v, i) => i === vIndex ? { ...v, text: val } : v))
  }

  async function handleGenerate() {
    if (!patientId?.trim()) return
    setIsGenerating(true)
    setError('')
    try {
      const res = await fetch('/api/summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ma_bn_an: (patientId ?? '').trim() }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        setError(detail.detail ?? `Lỗi ${res.status}`)
        return
      }
      const data = await res.json()
      pushVersion(data.summary ?? '', 'AI tạo mới')
      setRefineHistory([])
    } catch {
      setError('Lỗi mạng — máy chủ có đang chạy không?')
    } finally {
      setIsGenerating(false)
    }
  }

  async function handleRefine() {
    if (!refineInput.trim() || !summary) return
    const prompt = refineInput.trim()
    setRefineInput('')
    setIsRefining(true)
    setError('')
    try {
      const res = await fetch('/api/refine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, summary, ma_bn_an: (patientId ?? '').trim(), history: refineHistory }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        setError(detail.detail ?? `Lỗi ${res.status}`)
        return
      }
      const data = await res.json()
      const refined = data.summary ?? summary
      setRefineHistory(h => [...h, { instruction: prompt, result_summary: refined }])
      pushVersion(refined, `Tinh chỉnh: "${truncate(prompt)}"`)
    } catch {
      setError('Lỗi mạng — máy chủ có đang chạy không?')
    } finally {
      setIsRefining(false)
    }
  }

  async function handlePreview() {
    if (!summary || !(patientId ?? '').trim()) return
    setIsPreviewing(true)
    setError('')
    try {
      const res = await fetch('/api/preview-html', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ma_bn_an: (patientId ?? '').trim(), summary }),
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
    if (!summary || !(patientId ?? '').trim()) return
    setIsExporting(true)
    setError('')
    try {
      const res = await fetch('/api/export-docx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ma_bn_an: (patientId ?? '').trim(), summary }),
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
      a.download = `tom_tat_${(patientId ?? '').trim()}.docx`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('Lỗi mạng — máy chủ có đang chạy không?')
    } finally {
      setIsExporting(false)
    }
  }

  function handleFeedback(val: 'up' | 'down') {
    setFeedback(val)
    setShowReason(val === 'down')
    setFeedbackSent(false)
  }

  const [collapsed, setCollapsed] = useState(false)
  const hasSummary = versions.length > 0
  const isWorking = isGenerating || isRefining

  return (
    <>
      <div className="bg-white border border-outline-variant rounded-[14px] overflow-hidden shadow-card">
        <button
          onClick={() => setCollapsed(c => !c)}
          className="w-full flex items-center gap-[9px] px-[18px] py-[14px] border-b border-outline-variant cursor-pointer bg-transparent text-left"
          style={{ borderBottom: collapsed ? 'none' : undefined }}
        >
          <span className="w-[26px] h-[26px] rounded-[7px] bg-primary-container text-primary flex items-center justify-center flex-none">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l1.8 5.6L19.5 9l-5.7 1.4L12 16l-1.8-5.6L4.5 9l5.7-1.4L12 2z"/>
            </svg>
          </span>
          <h3 className="text-[14px] font-bold text-on-surface flex-1">Tóm tắt bệnh án</h3>
          <span className="material-symbols-outlined text-[18px] text-on-surface-variant transition-transform duration-200" style={{ transform: collapsed ? 'rotate(-90deg)' : 'rotate(0deg)' }}>
            expand_more
          </span>
        </button>

        {!collapsed && <div className="p-[18px] flex flex-col gap-[10px]">
          {/* Generate button */}
          <button
            onClick={handleGenerate}
            disabled={isWorking || !(patientId ?? '').trim()}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-primary text-white rounded-[10px] text-[14px] font-semibold cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed transition-opacity"
          >
            {isGenerating ? (
              <span className="w-[15px] h-[15px] border-2 border-white/40 border-t-white rounded-full inline-block animate-spin" />
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2l1.8 5.6L19.5 9l-5.7 1.4L12 16l-1.8-5.6L4.5 9l5.7-1.4L12 2z"/>
              </svg>
            )}
            {hasSummary ? 'Tạo lại tóm tắt' : 'Tạo tóm tắt bệnh án'}
          </button>

          {error && (
            <p className="text-xs text-[#b5544b] bg-[#fdf0ee] border border-[#f3d9d4] rounded-lg px-3 py-2">{error}</p>
          )}

          {/* Version control */}
          {(hasSummary || isWorking) && (
            <div className="flex flex-col items-center gap-[6px] bg-[#f6f9fe] border border-[#e9eff8] rounded-[9px] px-[9px] py-[10px]">
              <div className="flex items-center gap-[7px]">
                <button
                  onClick={() => setVIndex(i => Math.max(0, i - 1))}
                  disabled={vIndex <= 0}
                  className="w-[26px] h-[26px] inline-flex items-center justify-center border border-outline-variant rounded-[7px] bg-white disabled:text-[#c8d1de] text-[#3c5573] disabled:cursor-default cursor-pointer"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M15 18l-6-6 6-6"/>
                  </svg>
                </button>
                <span className="text-[12px] font-semibold text-[#3c5573] whitespace-nowrap">
                  Phiên bản {vIndex + 1}/{versions.length}
                </span>
                <button
                  onClick={() => setVIndex(i => Math.min(versions.length - 1, i + 1))}
                  disabled={vIndex >= versions.length - 1}
                  className="w-[26px] h-[26px] inline-flex items-center justify-center border border-outline-variant rounded-[7px] bg-white disabled:text-[#c8d1de] text-[#3c5573] disabled:cursor-default cursor-pointer"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 18l6-6-6-6"/>
                  </svg>
                </button>
              </div>
              {curVersion && (
                <span className="text-[11px] text-on-surface-variant text-center">
                  {curVersion.src} · {curVersion.time}
                </span>
              )}
            </div>
          )}

          {/* Summary display */}
          {(() => {
            const parsed = summary ? parseSummaryJson(summary) : null
            if (parsed) {
              return (
                <div className="w-full border border-outline-variant rounded-[10px] bg-surface-container-low p-3 flex flex-col gap-[10px] min-h-[184px] overflow-y-auto max-h-[400px]">
                  {SUMMARY_FIELDS.map(({ key, label }) => {
                    const val = parsed[key]
                    if (!val) return null
                    return (
                      <div key={key}>
                        <div className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wide mb-[2px]">
                          {label}
                        </div>
                        <div className="text-[12px] leading-[1.55] text-on-surface whitespace-pre-wrap">
                          {val}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )
            }
            return (
              <textarea
                value={summary}
                onChange={(e) => editSummary(e.target.value)}
                placeholder="Tóm tắt được tạo sẽ hiển thị ở đây…"
                className="w-full h-[184px] p-3 border border-outline-variant rounded-[10px] text-[13px] leading-[1.55] text-on-surface resize-none outline-none font-[inherit] bg-surface-container-low focus:border-primary transition-colors"
              />
            )
          })()}

          {/* Refine */}
          {hasSummary && (
            <div className="flex gap-2">
              <input
                type="text"
                value={refineInput}
                onChange={(e) => setRefineInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleRefine()}
                placeholder="Yêu cầu AI chỉnh sửa (tạo phiên bản mới)…"
                className="flex-1 px-3 py-[10px] border border-outline-variant rounded-[9px] text-[13px] outline-none font-[inherit] text-on-surface bg-white focus:border-primary transition-colors"
              />
              <button
                onClick={handleRefine}
                disabled={isWorking || !summary}
                className="w-[40px] flex-none flex items-center justify-center bg-primary text-white rounded-[9px] border-none cursor-pointer disabled:opacity-50"
              >
                {isRefining ? (
                  <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full inline-block animate-spin" />
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 2 11 13"/>
                    <path d="M22 2 15 22l-4-9-9-4 20-7z"/>
                  </svg>
                )}
              </button>
            </div>
          )}

          {/* Feedback */}
          {hasSummary && !isWorking && (
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-on-surface-variant">Phiên bản này hữu ích?</span>
                <button
                  onClick={() => handleFeedback('up')}
                  className="w-[28px] h-[28px] inline-flex items-center justify-center rounded-lg border transition-colors"
                  style={{
                    border: `1px solid ${feedback === 'up' ? '#cfe0fc' : '#e4eaf2'}`,
                    background: feedback === 'up' ? '#eef4fe' : '#fff',
                    color: feedback === 'up' ? '#2f6fed' : '#9aa7ba',
                  }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M2 20h2.5V10H2v10zm20-9.2c0-.9-.8-1.6-1.7-1.6h-5.3l.8-3.9.1-.4c0-.4-.2-.8-.4-1L14.4 3 8.6 8.9c-.4.3-.6.8-.6 1.3V18c0 .9.7 1.6 1.7 1.6h7.5c.7 0 1.3-.4 1.5-1l2.5-5.9c.1-.2.1-.4.1-.6v-1.3z"/>
                  </svg>
                </button>
                <button
                  onClick={() => handleFeedback('down')}
                  className="w-[28px] h-[28px] inline-flex items-center justify-center rounded-lg border transition-colors"
                  style={{
                    border: `1px solid ${feedback === 'down' ? '#f0c9c4' : '#e4eaf2'}`,
                    background: feedback === 'down' ? '#fdf0ee' : '#fff',
                    color: feedback === 'down' ? '#d8584f' : '#9aa7ba',
                  }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style={{ transform: 'scaleY(-1)' }}>
                    <path d="M2 20h2.5V10H2v10zm20-9.2c0-.9-.8-1.6-1.7-1.6h-5.3l.8-3.9.1-.4c0-.4-.2-.8-.4-1L14.4 3 8.6 8.9c-.4.3-.6.8-.6 1.3V18c0 .9.7 1.6 1.7 1.6h7.5c.7 0 1.3-.4 1.5-1l2.5-5.9c.1-.2.1-.4.1-.6v-1.3z"/>
                  </svg>
                </button>
                {feedbackSent && (
                  <span className="text-[11px] text-[#1d9a6c] font-medium">✓ Cảm ơn phản hồi</span>
                )}
              </div>
              {showReason && !feedbackSent && (
                <div className="mt-2 bg-[#fdf3f1] border border-[#f3d9d4] rounded-[10px] p-[10px] animate-[fadeUp_.2s_ease]">
                  <div className="text-[11px] text-[#b5544b] font-semibold mb-[6px]">Điều gì chưa chính xác? (không bắt buộc)</div>
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Ví dụ: thiếu kết quả xét nghiệm, sai mốc thời gian…"
                    className="w-full h-[54px] text-[12px] border border-[#f0d3cd] rounded-lg p-2 resize-none outline-none font-[inherit] bg-white text-on-surface"
                  />
                  <button
                    onClick={() => { setFeedbackSent(true); setShowReason(false) }}
                    className="mt-[6px] px-[14px] py-[6px] bg-[#d8584f] text-white text-[12px] font-semibold rounded-lg border-none cursor-pointer font-[inherit]"
                  >
                    Gửi phản hồi
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-[10px] mt-1">
            <button
              onClick={handlePreview}
              disabled={isPreviewing || !summary}
              className="flex-1 flex items-center justify-center gap-[7px] py-[10px] border border-[#cfdbec] rounded-[9px] bg-white text-[#3c5573] text-[13px] font-semibold cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-container-low transition-colors font-[inherit]"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              {isPreviewing ? 'Đang tải…' : 'Xem trước'}
            </button>
            <button
              onClick={handleExport}
              disabled={isExporting || !summary}
              className="flex-1 flex items-center justify-center gap-[7px] py-[10px] border-none rounded-[9px] bg-primary-container text-primary text-[13px] font-semibold cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity font-[inherit]"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 3v12"/>
                <path d="M7 11l5 5 5-5"/>
                <path d="M5 21h14"/>
              </svg>
              {isExporting ? 'Đang xuất…' : 'Xuất DOCX'}
            </button>
          </div>
        </div>}
      </div>

      {previewHtml && createPortal(
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={() => setPreviewHtml(null)}
        >
          <div
            className="bg-white rounded-xl shadow-2xl w-full max-w-4xl h-[96vh] flex flex-col"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-6 py-3 border-b border-outline-variant shrink-0">
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
            <div className="flex items-center gap-sm px-6 py-3 border-t border-outline-variant shrink-0">
              <button
                onClick={() => setPreviewHtml(null)}
                className="ml-auto px-4 py-2 bg-primary text-white rounded-lg text-xs font-bold hover:opacity-90 transition-opacity uppercase tracking-wider"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  )
}
