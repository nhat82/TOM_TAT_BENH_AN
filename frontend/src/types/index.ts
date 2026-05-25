export interface Vitals {
  bloodPressure: string
  heartRate: string
  temp: string
}

export interface LabResult {
  id: string
  testName: string
  value: string
  date: string
  isAbnormal?: boolean
}

export interface Medication {
  id: string
  name: string
  frequency: string
}

export interface ChatMessage {
  id: string
  sender: 'doctor' | 'assistant'
  senderName: string
  content: string
}
