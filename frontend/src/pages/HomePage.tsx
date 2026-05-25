import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import Footer from '../components/Footer'

export default function HomePage() {
  const [patientId, setPatientId] = useState('')
  const navigate = useNavigate()

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (patientId.trim()) navigate(`/patient/${patientId.trim()}`)
  }

  return (
    <main className="flex flex-col min-h-screen">
      <Header />
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-xl max-w-md px-xl">
          <span className="material-symbols-outlined text-primary text-[64px]">local_hospital</span>
          <div className="space-y-sm">
            <h1 className="text-headline-lg font-bold text-on-surface">Hệ thống Hồ sơ Bệnh nhân</h1>
            <p className="text-body-md text-on-surface-variant">Nhập mã bệnh nhân để xem hồ sơ và tạo tóm tắt bệnh án</p>
          </div>
          <form onSubmit={handleSubmit} className="flex gap-sm">
            <input
              type="text"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              placeholder="Mã bệnh nhân (vd. BN0052)"
              className="flex-1 bg-white border border-outline-variant rounded-lg px-md py-3 text-sm focus:ring-1 focus:ring-primary focus:border-primary outline-none"
            />
            <button
              type="submit"
              disabled={!patientId.trim()}
              className="px-lg py-3 bg-primary text-white rounded-lg text-title-sm font-semibold hover:bg-primary/90 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              Xem hồ sơ
            </button>
          </form>
        </div>
      </div>
      <Footer />
    </main>
  )
}
