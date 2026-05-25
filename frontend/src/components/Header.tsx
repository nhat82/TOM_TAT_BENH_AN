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
    <header className="flex justify-between items-center w-full px-xl h-16 border-b border-outline-variant bg-white sticky top-0 z-30">
      <div className="flex items-center gap-xl flex-1">
        <h2 className="text-headline-md font-semibold text-on-surface">Hồ sơ Bệnh nhân</h2>
      </div>
      <nav className="flex items-center gap-lg">
        <div className="flex items-center gap-sm bg-surface-container-low px-md py-1.5 rounded-lg border border-outline-variant focus-within:border-primary/50 transition-all w-[240px]">
          <span className="material-symbols-outlined text-on-surface-variant text-[18px]">search</span>
          <input
            className="flex-1 bg-transparent border-none focus:ring-0 text-body-sm py-0 placeholder:text-on-surface-variant/50"
            placeholder="Nhập mã bệnh nhân..."
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={handleSearch}
          />
        </div>
        <div className="flex flex-col text-right">
          <span className="text-body-sm font-semibold">BS. Nguyễn Văn A</span>
          <span className="text-[11px] text-on-surface-variant uppercase tracking-wider">Nội khoa</span>
        </div>
      </nav>
    </header>
  )
}
