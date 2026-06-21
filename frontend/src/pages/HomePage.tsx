import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import Footer from '../components/Footer'

type PatientKey = 'active' | 'stable'
type FilterKey = 'all' | PatientKey

interface Patient {
  code: string
  name: string
  gender: string
  age: number
  diagnosis: string
  dept: string
  visit: string
  status: string
  key: PatientKey
}

interface RawPatient {
  ma_bn_an: string
  birthdayyear: string
  departmentid: string
  medicalrecorddate_in: string
  medicalrecorddate_out: string
  chandoan_out_main: string
  chandoan_in: string
}

const STATUS_STYLES: Record<PatientKey, { statusBg: string; statusFg: string; avatarBg: string; avatarFg: string }> = {
  active: { statusBg: '#EAF0FE', statusFg: '#3B63E0', avatarBg: '#E7EDFD', avatarFg: '#3B63E0' },
  stable: { statusBg: '#E9F6EE', statusFg: '#2E8B57', avatarBg: '#DEF1E6', avatarFg: '#2E8B57' },
}

const FILTERS: { key: FilterKey; label: string; dot: string }[] = [
  { key: 'all', label: 'Tất cả', dot: '#9AA3B8' },
  { key: 'active', label: 'Đang điều trị', dot: '#3B63E0' },
  { key: 'stable', label: 'Đã ra viện', dot: '#2E8B57' },
]

const CURRENT_YEAR = new Date().getFullYear()

function relativeDate(dateStr: string): string {
  if (!dateStr) return 'Không rõ'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  const diffMs = Date.now() - d.getTime()
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffDays === 0) return 'Hôm nay'
  if (diffDays === 1) return 'Hôm qua'
  if (diffDays < 7) return `${diffDays} ngày trước`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} tuần trước`
  return `${Math.floor(diffDays / 30)} tháng trước`
}

function mapRawPatient(r: RawPatient): Patient {
  const discharged = !!r.medicalrecorddate_out
  return {
    code: r.ma_bn_an,
    name: r.ma_bn_an,
    gender: '',
    age: r.birthdayyear ? CURRENT_YEAR - parseInt(r.birthdayyear, 10) : 0,
    diagnosis: r.chandoan_out_main || r.chandoan_in || 'Chưa có chẩn đoán',
    dept: r.departmentid || 'N/A',
    visit: relativeDate(r.medicalrecorddate_in),
    status: discharged ? 'Đã ra viện' : 'Đang điều trị',
    key: discharged ? 'stable' : 'active',
  }
}

function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return '?'
  return ((parts[0][0] ?? '') + (parts[parts.length - 1]?.[0] ?? '')).toUpperCase()
}

export default function HomePage() {
  const [patientId, setPatientId] = useState('')
  const [activeFilter, setActiveFilter] = useState<FilterKey>('all')
  const [query] = useState('')
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const navigate = useNavigate()

  const PAGE_SIZE = 4

  useEffect(() => {
    fetch('/api/patients')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((data) => {
        setPatients((data.patients as RawPatient[]).map(mapRawPatient))
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (patientId.trim()) navigate(`/patient/${patientId.trim()}`)
  }

  const filtered = patients.filter((p) => {
    const q = query.trim().toLowerCase()
    const matchQ = !q || p.code.toLowerCase().includes(q) || p.name.toLowerCase().includes(q)
    const matchF = activeFilter === 'all' || p.key === activeFilter
    return matchQ && matchF
  })

  const totalCount = patients.length
  const activeCount = patients.filter((p) => p.key === 'active').length
  const stableCount = patients.filter((p) => p.key === 'stable').length

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const safePage = Math.min(page, totalPages)
  const paginated = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)

  const countLabel = `${filtered.length} hồ sơ${activeFilter !== 'all' || query ? ' (đã lọc)' : ''}`

  function goTo(p: number) {
    setPage(Math.max(1, Math.min(p, totalPages)))
    window.scrollTo({ top: document.getElementById('patient-list')?.offsetTop ?? 0, behavior: 'smooth' })
  }

  function changeFilter(f: FilterKey) {
    setActiveFilter(f)
    setPage(1)
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#F4F6FB]">
      <Header />

      <main className="flex-1 w-full max-w-[1240px] mx-auto px-10 py-12 pb-16">

        {/* HERO */}
        <section className="grid grid-cols-[1.05fr_0.95fr] gap-10 items-stretch mb-[52px]">
          <div>
            <div className="text-[12px] font-bold tracking-[0.16em] text-[#9AA3B8] mb-[18px] uppercase">
              Hệ thống AI Lâm sàng · Lead Consulting
            </div>
            <h1 className="text-[52px] leading-[1.04] font-extrabold tracking-[-0.02em] text-[#1B2440] m-0 mb-4">
              Tóm tắt<br />Bệnh án
            </h1>
            <div className="w-14 h-1 rounded-sm bg-primary mb-6" />
            <p className="text-[17px] leading-relaxed text-[#6A748D] max-w-[380px] mb-7">
              Nhập mã bệnh nhân để xem hồ sơ và tạo tóm tắt với AI, hoặc chọn từ danh sách bên dưới.
            </p>
            <form onSubmit={handleSubmit} className="flex gap-3 max-w-[480px]">
              <input
                type="text"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                placeholder="Mã bệnh nhân (vd. BN0052)"
                className="flex-1 px-[18px] py-[15px] border border-outline-variant rounded-[13px] bg-white text-[15px] text-on-surface placeholder:text-on-surface-variant outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-colors"
              />
              <button
                type="submit"
                className="px-[26px] py-[15px] border-none rounded-[13px] bg-primary text-white text-[15px] font-semibold cursor-pointer whitespace-nowrap shadow-[0_6px_16px_rgba(47,111,237,.32)] hover:bg-primary/90 transition-colors disabled:opacity-50"
                disabled={!patientId.trim()}
              >
                Xem hồ sơ
              </button>
            </form>
          </div>

          {/* Stats card */}
          <div className="bg-white border border-[#ECEFF6] rounded-[22px] p-[30px] flex flex-col gap-[22px] shadow-[0_10px_30px_rgba(27,36,64,.05)]">
            <div className="text-[13px] font-bold tracking-[0.04em] text-[#6A748D]">TỔNG QUAN HỒ SƠ</div>
            <div className="grid grid-cols-2 gap-[18px]">
              <div className="bg-[#F7F9FD] rounded-[15px] p-[18px]">
                <div className="text-[30px] font-extrabold tracking-[-0.02em]" style={{ color: '#3B63E0' }}>
                  {loading ? '—' : totalCount}
                </div>
                <div className="text-[13px] font-medium text-[#8A93A8] mt-1">Tổng hồ sơ</div>
              </div>
              <div className="bg-[#F7F9FD] rounded-[15px] p-[18px]">
                <div className="text-[30px] font-extrabold tracking-[-0.02em]" style={{ color: '#3B63E0' }}>
                  {loading ? '—' : activeCount}
                </div>
                <div className="text-[13px] font-medium text-[#8A93A8] mt-1">Đang điều trị</div>
              </div>
              <div className="bg-[#F7F9FD] rounded-[15px] p-[18px]">
                <div className="text-[30px] font-extrabold tracking-[-0.02em]" style={{ color: '#2E8B57' }}>
                  {loading ? '—' : stableCount}
                </div>
                <div className="text-[13px] font-medium text-[#8A93A8] mt-1">Đã ra viện</div>
              </div>
              <div className="bg-[#F7F9FD] rounded-[15px] p-[18px]">
                <div className="text-[30px] font-extrabold tracking-[-0.02em]" style={{ color: '#9AA3B8' }}>
                  {loading ? '—' : filtered.length}
                </div>
                <div className="text-[13px] font-medium text-[#8A93A8] mt-1">Đang hiển thị</div>
              </div>
            </div>
            <div className="mt-auto flex items-center gap-[10px] px-4 py-[14px] bg-[#EEF7F0] rounded-[13px]">
              <span className="w-2 h-2 rounded-full bg-[#2FA56A] flex-none" />
              <span className="text-[13.5px] font-medium text-[#2E7D52]">
                {loading ? 'Đang tải dữ liệu...' : `AI sẵn sàng tạo tóm tắt cho ${totalCount} hồ sơ`}
              </span>
            </div>
          </div>
        </section>

        {/* PATIENT LIST */}
        <section>
          <div className="flex items-end justify-between gap-6 mb-[22px] flex-wrap">
            <div>
              <h2 className="text-[24px] font-bold tracking-[-0.01em] text-[#1B2440] m-0 mb-1.5">Danh sách bệnh nhân</h2>
              <p className="text-[14.5px] text-[#8A93A8] m-0">{loading ? 'Đang tải...' : countLabel}</p>
            </div>
            <div className="flex gap-2 flex-wrap">
              {FILTERS.map((f) => {
                const on = activeFilter === f.key
                return (
                  <button
                    key={f.key}
                    onClick={() => changeFilter(f.key)}
                    className="flex items-center gap-[7px] px-4 py-[9px] rounded-full text-[13.5px] font-semibold border cursor-pointer transition-colors font-sans"
                    style={{
                      background: on ? '#1B2440' : '#fff',
                      color: on ? '#fff' : '#5A647C',
                      borderColor: on ? '#1B2440' : '#E4E8F2',
                    }}
                  >
                    <span className="w-[7px] h-[7px] rounded-full flex-none" style={{ background: f.dot }} />
                    {f.label}
                  </button>
                )
              })}
            </div>
          </div>

          {error && (
            <div className="mb-6 px-5 py-4 bg-[#FDECEC] border border-[#F5C6C6] rounded-[13px] text-[#D5443E] text-[14px]">
              Không thể tải danh sách bệnh nhân: {error}
            </div>
          )}

          {loading ? (
            <div className="grid grid-cols-2 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="border border-[#ECEFF6] bg-white rounded-[18px] p-5 animate-pulse flex gap-4">
                  <div className="w-[52px] h-[52px] rounded-[15px] bg-[#F0F3FA] flex-none" />
                  <div className="flex-1 space-y-2.5">
                    <div className="h-4 bg-[#F0F3FA] rounded w-3/4" />
                    <div className="h-3 bg-[#F0F3FA] rounded w-1/2" />
                    <div className="h-3 bg-[#F0F3FA] rounded w-2/3" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div id="patient-list" className="grid grid-cols-2 gap-4">
              {paginated.map((p) => {
                const s = STATUS_STYLES[p.key]
                return (
                  <button
                    key={p.code}
                    onClick={() => navigate(`/patient/${p.code}`)}
                    className="text-left border border-[#ECEFF6] bg-white rounded-[18px] p-5 cursor-pointer font-sans flex gap-4 items-start hover:border-[#C3D0F5] hover:shadow-[0_10px_26px_rgba(27,36,64,.08)] hover:-translate-y-0.5 transition-all duration-150"
                  >
                    <div
                      className="flex-none w-[52px] h-[52px] rounded-[15px] flex items-center justify-center text-[17px] font-bold"
                      style={{ background: s.avatarBg, color: s.avatarFg }}
                    >
                      {initials(p.name)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2.5">
                        <span className="text-[16.5px] font-bold tracking-[-0.01em] text-[#1B2440] truncate">{p.name}</span>
                        <span className="flex-none text-[12px] font-bold tracking-[0.04em] text-[#9AA3B8]">{p.code}</span>
                      </div>
                      <div className="text-[13.5px] text-[#8A93A8] mt-0.5 mb-3">
                        {[p.age > 0 ? `${p.age} tuổi` : null, p.dept].filter(Boolean).join(' · ')}
                      </div>
                      <div className="text-[14.5px] font-medium text-[#2A3454] mb-3.5 truncate">{p.diagnosis}</div>
                      <div className="flex items-center justify-between gap-2.5">
                        <span
                          className="inline-flex items-center gap-[7px] px-[11px] py-[5px] rounded-full text-[12.5px] font-semibold"
                          style={{ background: s.statusBg, color: s.statusFg }}
                        >
                          <span className="w-1.5 h-1.5 rounded-full flex-none" style={{ background: s.statusFg }} />
                          {p.status}
                        </span>
                        <span className="text-[12.5px] text-[#A7AFC2]">{p.visit}</span>
                      </div>
                    </div>
                  </button>
                )
              })}
              {paginated.length === 0 && (
                <div className="col-span-2 text-center py-16 text-[#9AA3B8] text-[15px]">
                  Không tìm thấy bệnh nhân phù hợp
                </div>
              )}
            </div>
          )}

          {!loading && totalPages > 1 && (
            <div className="flex items-center justify-between mt-8">
              <span className="text-[13.5px] text-[#9AA3B8]">
                Trang {safePage} / {totalPages} · {filtered.length} hồ sơ
              </span>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => goTo(safePage - 1)}
                  disabled={safePage === 1}
                  className="w-9 h-9 flex items-center justify-center rounded-[10px] border border-[#E4E8F2] bg-white text-[#5A647C] text-[13px] font-semibold cursor-pointer hover:border-[#C3D0F5] disabled:opacity-40 disabled:cursor-default transition-colors"
                >
                  ‹
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter((p) => p === 1 || p === totalPages || Math.abs(p - safePage) <= 1)
                  .reduce<(number | '…')[]>((acc, p, idx, arr) => {
                    if (idx > 0 && p - (arr[idx - 1] as number) > 1) acc.push('…')
                    acc.push(p)
                    return acc
                  }, [])
                  .map((p, idx) =>
                    p === '…' ? (
                      <span key={`ellipsis-${idx}`} className="w-9 h-9 flex items-center justify-center text-[#C0C8D8] text-[13px]">…</span>
                    ) : (
                      <button
                        key={p}
                        onClick={() => goTo(p)}
                        className="w-9 h-9 flex items-center justify-center rounded-[10px] border text-[13px] font-semibold cursor-pointer transition-colors"
                        style={{
                          background: p === safePage ? '#1B2440' : '#fff',
                          color: p === safePage ? '#fff' : '#5A647C',
                          borderColor: p === safePage ? '#1B2440' : '#E4E8F2',
                        }}
                      >
                        {p}
                      </button>
                    )
                  )}
                <button
                  onClick={() => goTo(safePage + 1)}
                  disabled={safePage === totalPages}
                  className="w-9 h-9 flex items-center justify-center rounded-[10px] border border-[#E4E8F2] bg-white text-[#5A647C] text-[13px] font-semibold cursor-pointer hover:border-[#C3D0F5] disabled:opacity-40 disabled:cursor-default transition-colors"
                >
                  ›
                </button>
              </div>
            </div>
          )}
        </section>
      </main>

      <Footer />
    </div>
  )
}
