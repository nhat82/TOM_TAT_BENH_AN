import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Header() {
  const [search, setSearch] = useState('')
  const navigate = useNavigate()

  function handleSearch(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && search.trim()) {
      navigate(`/patient/${search.trim()}`)
      setSearch('')
    }
  }

  return (
    <header className="bg-white border-b border-outline-variant sticky top-0 z-30 flex items-center justify-between gap-8 px-10 py-[18px]">
      <div className="flex items-center gap-[14px] flex-none cursor-pointer" onClick={() => navigate('/')}>
        <div className="w-10 h-10 rounded-[11px] bg-primary flex items-center justify-center flex-none shadow-[0_4px_12px_rgba(47,111,237,.35)]">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M7 3h7l4 4v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" fill="white" fillOpacity=".25" stroke="white" strokeWidth="1.6" strokeLinejoin="round"/>
            <path d="M13 3v5h5" stroke="white" strokeWidth="1.6" strokeLinejoin="round"/>
          </svg>
        </div>
        <span className="text-[19px] font-bold tracking-[-0.01em] text-on-surface">Hồ sơ Bệnh nhân</span>
      </div>

      <div className="flex-1 max-w-[520px] relative flex items-center">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="absolute left-[18px] pointer-events-none">
          <circle cx="11" cy="11" r="7" stroke="#A7AFC2" strokeWidth="2"/>
          <path d="m20 20-3-3" stroke="#A7AFC2" strokeWidth="2" strokeLinecap="round"/>
        </svg>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={handleSearch}
          placeholder="Nhập mã bệnh nhân..."
          className="w-full pl-[46px] pr-[18px] py-[13px] border border-outline-variant rounded-[13px] bg-surface-container-low text-[15px] text-on-surface placeholder:text-on-surface-variant outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-colors"
        />
      </div>

      <div className="flex items-center gap-4 flex-none">
        <div className="text-right leading-[1.25]">
          <div className="text-[15px] font-bold text-on-surface">BS. Nguyễn Văn A</div>
          <div className="text-[11px] font-semibold tracking-[0.12em] text-on-surface-variant uppercase">Nội khoa</div>
        </div>
        <div className="w-11 h-11 rounded-[13px] bg-primary-container flex items-center justify-center flex-none">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="8" r="4" stroke="#7C93EC" strokeWidth="2"/>
            <path d="M5 20a7 7 0 0 1 14 0" stroke="#7C93EC" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
      </div>
    </header>
  )
}
