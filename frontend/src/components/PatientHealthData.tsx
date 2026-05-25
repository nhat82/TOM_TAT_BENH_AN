import { useState } from 'react'
import type { Vitals, LabResult, Medication } from '../types'

const initialVitals: Vitals = {
  bloodPressure: '118/76',
  heartRate: '72',
  temp: '98.6',
}

const initialLabs: LabResult[] = [
  { id: '1', testName: 'Glucose (Fasting)', value: '94', date: '2 days ago' },
  { id: '2', testName: 'Cholesterol (Total)', value: '210', date: '14 days ago', isAbnormal: true },
]

const initialMeds: Medication[] = [
  { id: '1', name: 'Lisinopril 10mg', frequency: 'QD, Oral Administration' },
  { id: '2', name: 'Metformin 500mg', frequency: 'BID, with Meals' },
]

function FieldInput({
  label,
  value,
  onChange,
  className = '',
}: {
  label?: string
  value: string
  onChange: (v: string) => void
  className?: string
}) {
  return (
    <div className="flex flex-col gap-xs">
      {label && (
        <label className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-widest">
          {label}
        </label>
      )}
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full bg-transparent border-b border-outline-variant focus:border-primary px-0 py-1 text-sm focus:ring-0 outline-none ${className}`}
      />
    </div>
  )
}

export default function PatientHealthData() {
  const [vitals, setVitals] = useState<Vitals>(initialVitals)
  const [labs, setLabs] = useState<LabResult[]>(initialLabs)
  const [meds, setMeds] = useState<Medication[]>(initialMeds)

  function updateLab(id: string, field: keyof LabResult, value: string) {
    setLabs((prev) => prev.map((l) => (l.id === id ? { ...l, [field]: value } : l)))
  }

  function updateMed(id: string, field: keyof Medication, value: string) {
    setMeds((prev) => prev.map((m) => (m.id === id ? { ...m, [field]: value } : m)))
  }

  return (
    <section className="col-span-12 lg:col-span-8 flex flex-col gap-lg">
      {/* Section Header */}
      <div className="flex justify-between items-center mb-sm">
        <div>
          <h3 className="text-headline-md font-semibold text-on-surface">Patient Health Data</h3>
          <p className="text-body-sm text-on-surface-variant">Last updated: Today, 08:45 AM</p>
        </div>
        <button className="text-on-surface-variant hover:text-primary flex items-center gap-xs opacity-70 hover:opacity-100 transition-opacity text-[11px] font-semibold uppercase tracking-widest">
          <span className="material-symbols-outlined text-[16px]">edit_note</span>
          Edit Records
        </button>
      </div>

      <div className="space-y-lg">
        <div className="border-t border-outline-variant pt-md">

          {/* Vitals */}
          <div className="mb-lg">
            <h4 className="text-[11px] font-semibold text-on-surface-variant uppercase tracking-widest mb-md flex items-center gap-xs">
              <span className="material-symbols-outlined text-[16px]">monitor_heart</span>
              Vitals
            </h4>
            <div className="grid grid-cols-3 gap-lg">
              <FieldInput
                label="Blood Pressure"
                value={vitals.bloodPressure}
                onChange={(v) => setVitals((p) => ({ ...p, bloodPressure: v }))}
                className="font-medium"
              />
              <FieldInput
                label="Heart Rate"
                value={vitals.heartRate}
                onChange={(v) => setVitals((p) => ({ ...p, heartRate: v }))}
                className="font-medium"
              />
              <FieldInput
                label="Temp (F)"
                value={vitals.temp}
                onChange={(v) => setVitals((p) => ({ ...p, temp: v }))}
                className="font-medium"
              />
            </div>
          </div>

          {/* Lab Results */}
          <div className="mb-lg">
            <h4 className="text-[11px] font-semibold text-on-surface-variant uppercase tracking-widest mb-md flex items-center gap-xs">
              <span className="material-symbols-outlined text-[16px]">biotech</span>
              Lab Results
            </h4>
            <div className="space-y-md">
              {labs.map((lab, idx) => (
                <div key={lab.id} className="grid grid-cols-12 gap-md items-end">
                  <div className="col-span-5">
                    {idx === 0 && (
                      <label className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-widest">
                        Test Name
                      </label>
                    )}
                    <input
                      type="text"
                      value={lab.testName}
                      onChange={(e) => updateLab(lab.id, 'testName', e.target.value)}
                      className="w-full bg-transparent border-b border-outline-variant focus:border-primary px-0 py-1 text-sm focus:ring-0 outline-none"
                    />
                  </div>
                  <div className="col-span-3">
                    {idx === 0 && (
                      <label className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-widest">
                        Value (mg/dL)
                      </label>
                    )}
                    <input
                      type="text"
                      value={lab.value}
                      onChange={(e) => updateLab(lab.id, 'value', e.target.value)}
                      className={`w-full bg-transparent border-b border-outline-variant focus:border-primary px-0 py-1 font-medium text-sm focus:ring-0 outline-none ${lab.isAbnormal ? 'text-error' : ''}`}
                    />
                  </div>
                  <div className="col-span-4">
                    {idx === 0 && (
                      <label className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-widest">
                        Date
                      </label>
                    )}
                    <input
                      type="text"
                      value={lab.date}
                      onChange={(e) => updateLab(lab.id, 'date', e.target.value)}
                      className="w-full bg-transparent border-b border-outline-variant focus:border-primary px-0 py-1 text-xs text-on-surface-variant focus:ring-0 outline-none"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Current Regimen */}
          <div>
            <h4 className="text-[11px] font-semibold text-on-surface-variant uppercase tracking-widest mb-md flex items-center gap-xs">
              <span className="material-symbols-outlined text-[16px]">pill</span>
              Current Regimen
            </h4>
            <div className="space-y-md">
              {meds.map((med, idx) => (
                <div key={med.id} className="grid grid-cols-12 gap-md items-end">
                  <div className="col-span-6">
                    {idx === 0 && (
                      <label className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-widest">
                        Medication
                      </label>
                    )}
                    <input
                      type="text"
                      value={med.name}
                      onChange={(e) => updateMed(med.id, 'name', e.target.value)}
                      className="w-full bg-transparent border-b border-outline-variant focus:border-primary px-0 py-1 text-sm font-semibold focus:ring-0 outline-none"
                    />
                  </div>
                  <div className="col-span-6">
                    {idx === 0 && (
                      <label className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-widest">
                        Frequency
                      </label>
                    )}
                    <input
                      type="text"
                      value={med.frequency}
                      onChange={(e) => updateMed(med.id, 'frequency', e.target.value)}
                      className="w-full bg-transparent border-b border-outline-variant focus:border-primary px-0 py-1 text-xs italic text-on-surface-variant focus:ring-0 outline-none"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
