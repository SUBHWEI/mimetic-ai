export type Message = {
  id: string
  role: 'user' | 'assistant'
  text: string
  suggestions?: string[]
  diagnoses?: Diagnosis[]
  treatment?: Treatment
}

export type Diagnosis = {
  disease_name: string
  description: string
  severity: string
  confidence: number
  matched_symptoms: number
  total_input_symptoms: number
}

export type ManualDiagnosis = {
  id: string
  disease_name: string
  notes?: string
}

export type DoctorReview = {
  confirmedDiagnoses: string[]
  rejectedDiagnoses: string[]
  manualDiagnoses: ManualDiagnosis[]
  selectedMedicines: string[]
  modifiedDoses: Record<string, string>
  doctorNotes: string
}

export type MedicineDetail = {
  name: string
  dosage?: string
  dosage_mg_kg?: string | null
  max_daily_dose?: string
  frequency?: string
  duration?: string
  route?: string
  calculated_dosage?: string
  reasons?: string[]
  contraindications?: {
    conditions: string[]
    allergies: string[]
    comorbidities: string[]
  }
  adjustments?: {
    renal: string
    hepatic: string
    pediatric: string
    geriatric: string
    pregnancy: string
  }
  interactions_warning?: string
  monitoring?: string
  patient_summary?: string
}

export type Treatment = {
  disease_name: string
  medicines?: MedicineDetail[]
  general_recommendations: string
  available?: MedicineDetail[]
  not_recommended?: MedicineDetail[]
  alternatives?: MedicineDetail[]
  non_pharmacological?: string[]
}

export type PatientInfo = {
  first_name?: string
  last_name?: string
  name?: string
  document_type?: string
  id_document?: string
  birth_date?: string
  age?: string
  gender?: string
  occupation?: string
  phone?: string
  location?: string
  country?: string
  department?: string
  city?: string
  consultation_reason?: string
  symptom_evolution?: string
  tobacco?: string
  alcohol?: string
  substances?: string
  physical_activity?: string
  pregnancy?: string
  medical_history?: string
  surgical_history?: string
  pharmacological_history?: string
  allergies?: string
  blood_pressure?: string
  heart_rate?: string
  respiratory_rate?: string
  temperature?: string
  weight?: string
  height?: string
}

export type FieldConfig = {
  key: string
  label: string
  placeholder?: string
  type?: 'text' | 'select'
  options?: { value: string; label: string }[]
  suffix?: string
  condition?: (info: PatientInfo) => boolean
}

export type SearchResult = {
  document_number: string
  first_name: string
  last_name: string
  document_type: string
  source: string
  has_clinical_history: boolean
  has_user_account: boolean
  base_data: Record<string, string>
}

export type Phase = 'search' | 'patient_info' | 'symptoms' | 'report'
export type PatientInfoMode = 'full' | 'session_only'

export const INITIAL_DOCTOR_REVIEW: DoctorReview = {
  confirmedDiagnoses: [],
  rejectedDiagnoses: [],
  manualDiagnoses: [],
  selectedMedicines: [],
  modifiedDoses: {},
  doctorNotes: '',
}