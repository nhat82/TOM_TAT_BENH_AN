import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import PatientPage from './pages/PatientPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/patient/:patientId" element={<PatientPage />} />
    </Routes>
  )
}
