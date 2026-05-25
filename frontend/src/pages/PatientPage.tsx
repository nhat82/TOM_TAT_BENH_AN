import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import Header from '../components/Header'
import Footer from '../components/Footer'
import PatientData from '../components/PatientData'
import PatientSummaryPanel from '../components/PatientSummaryPanel'
import ClinicalInsightsPanel from '../components/ClinicalInsightsPanel'
import '../App.css'

export default function PatientPage() {
  const { patientId } = useParams<{ patientId: string }>()
  const [data, setData] = useState<Record<string, string> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!patientId) return
    setLoading(true)
    setError('')
    setData(null)
    async function load() {
      try {
        const r = await fetch(`/api/patient/${patientId}`)
        if (!r.ok) {
          const e = await r.json().catch(() => ({ detail: `Lỗi ${r.status}` }))
          throw new Error(e.detail ?? `Lỗi ${r.status}`)
        }
        const d = await r.json()
        setData(d.data)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Lỗi không xác định')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [patientId])

  return (
    <main className="flex flex-col min-h-screen">
      <Header />

      <div className="p-xl grid grid-cols-12 gap-gutter max-w-container-max mx-auto w-full flex-1">
        <PatientData data={data} loading={loading} error={error} patientId={patientId} />

        <section className="col-span-12 lg:col-span-4">
          <PatientSummaryPanel patientId={patientId} />
          <ClinicalInsightsPanel patientId={patientId} />
        </section>
      </div>

      <Footer />
    </main>
  )
}
