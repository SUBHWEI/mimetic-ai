import { useState, useRef, useEffect, useCallback } from 'react'
import { useAuth } from './context/AuthContext'
import './App.css'

const API = import.meta.env.VITE_API_URL || ''

type Message = {
  id: string
  role: 'user' | 'assistant'
  text: string
  suggestions?: string[]
  diagnoses?: Diagnosis[]
  treatment?: Treatment
}

type Diagnosis = {
  disease_name: string
  description: string
  severity: string
  confidence: number
  matched_symptoms: number
  total_input_symptoms: number
}

type Treatment = {
  disease_name: string
  medicines: { name: string; dosage: string; frequency: string; duration: string }[]
  general_recommendations: string
}

type PatientInfo = {
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

type FieldConfig = {
  key: string
  label: string
  placeholder?: string
  type?: 'text' | 'select'
  options?: { value: string; label: string }[]
  suffix?: string
}

type SearchResult = {
  document_number: string
  first_name: string
  last_name: string
  document_type: string
  source: string
  has_clinical_history: boolean
  has_user_account: boolean
  base_data: Record<string, string>
}

type Phase = 'search' | 'patient_info' | 'symptoms' | 'report'
type PatientInfoMode = 'full' | 'session_only'

const IDENTIFICATION_FIELDS: FieldConfig[] = [
  { key: 'first_name', label: 'Nombres', placeholder: 'Ej: Juan Andrés' },
  { key: 'last_name', label: 'Apellidos', placeholder: 'Ej: Pérez García' },
  { key: 'document_type', label: 'Tipo de documento', type: 'select', options: [
    { value: 'CC', label: 'Cédula de Ciudadanía (CC)' },
    { value: 'TI', label: 'Tarjeta de Identidad (TI)' },
    { value: 'CE', label: 'Cédula de Extranjería (CE)' },
    { value: 'RC', label: 'Registro Civil (RC)' },
    { value: 'Pasaporte', label: 'Pasaporte' },
  ]},
  { key: 'id_document', label: 'Número de documento', placeholder: 'Ej: 123456789' },
  { key: 'birth_date', label: 'Fecha de nacimiento', placeholder: 'DD/MM/AAAA' },
  { key: 'age', label: 'Edad', placeholder: 'Ej: 45', suffix: 'años' },
  { key: 'gender', label: 'Género', type: 'select', options: [
    { value: 'M', label: 'Masculino' },
    { value: 'F', label: 'Femenino' },
    { value: 'Otro', label: 'Otro' },
  ]},
  { key: 'occupation', label: 'Ocupación', placeholder: 'Ej: Ingeniero' },
  { key: 'phone', label: 'Teléfono', placeholder: 'Ej: 3001234567' },
  { key: 'country', label: 'País', placeholder: 'Ej: Colombia' },
  { key: 'department', label: 'Departamento', placeholder: 'Ej: Cundinamarca' },
  { key: 'city', label: 'Ciudad de residencia', placeholder: 'Ej: Bogotá' },
]

const ANAMNESIS_FIELDS: FieldConfig[] = [
  { key: 'consultation_reason', label: 'Motivo de consulta', placeholder: 'Describe brevemente el motivo' },
  { key: 'symptom_evolution', label: 'Tiempo de evolución', placeholder: 'Ej: 3 días', suffix: 'días/semanas' },
]

const ANTECEDENTES_FIELDS: FieldConfig[] = [
  { key: 'tobacco', label: 'Consumo de tabaco en los últimos 3 meses', placeholder: 'Ej: No ha fumado, Fuma ocasionalmente, Fuma a diario' },
  { key: 'alcohol', label: 'Consumo de alcohol en el último mes', placeholder: 'Ej: No consume, 1-2 veces/semana, A diario' },
  { key: 'substances', label: 'Uso de sustancias en el último año', placeholder: 'Ej: Ninguna, Cannabis, Ocasionalmente' },
  { key: 'physical_activity', label: 'Actividad física en el último mes', type: 'select', options: [
    { value: 'Sedentario', label: 'Sedentario (poco o ningún ejercicio)' },
    { value: '1-2 veces/semana', label: '1-2 veces por semana' },
    { value: '3+ veces/semana', label: '3 o más veces por semana' },
    { value: 'Diario', label: 'Ejercicio diario' },
  ]},
  { key: 'medical_history', label: 'Antecedentes médicos', placeholder: 'Diabetes, HTA, etc.' },
  { key: 'surgical_history', label: 'Antecedentes quirúrgicos', placeholder: 'Cirugías previas' },
  { key: 'pharmacological_history', label: 'Antecedentes farmacológicos', placeholder: 'Medicamentos actuales' },
  { key: 'allergies', label: 'Alergias conocidas', placeholder: 'Medicamentos, alimentos, etc.' },
]

const SIGNOS_FIELDS: FieldConfig[] = [
  { key: 'blood_pressure', label: 'Presión arterial (PA)', placeholder: 'Ej: 120/80', suffix: 'mmHg' },
  { key: 'heart_rate', label: 'Frecuencia cardíaca (FC)', placeholder: 'Ej: 72', suffix: 'lpm' },
  { key: 'respiratory_rate', label: 'Frecuencia respiratoria (FR)', placeholder: 'Ej: 16', suffix: 'rpm' },
  { key: 'temperature', label: 'Temperatura', placeholder: 'Ej: 36.5', suffix: '°C' },
  { key: 'weight', label: 'Peso', placeholder: 'Ej: 70', suffix: 'kg' },
  { key: 'height', label: 'Estatura', placeholder: 'Ej: 170', suffix: 'cm' },
]

const FULL_GROUPS = [
  { title: 'Identificación del Paciente', fields: IDENTIFICATION_FIELDS },
  { title: 'Anamnesis', fields: ANAMNESIS_FIELDS },
  { title: 'Antecedentes Personales', fields: ANTECEDENTES_FIELDS },
  { title: 'Signos Vitales', fields: SIGNOS_FIELDS },
]

const SESSION_GROUPS = [
  { title: 'Anamnesis', fields: ANAMNESIS_FIELDS },
  { title: 'Antecedentes Personales', fields: ANTECEDENTES_FIELDS },
  { title: 'Signos Vitales', fields: SIGNOS_FIELDS },
]

export default function ChatApp() {
  const { user, token: authToken, logout } = useAuth()
  const token = authToken || ''

  const [phase, setPhase] = useState<Phase>('search')
  const [patientInfoMode, setPatientInfoMode] = useState<PatientInfoMode>('full')
  const [messages, setMessages] = useState<Message[]>([
    { id: '0', role: 'assistant', text: 'Hola, soy Mimetic AI. Antes de comenzar, necesito los datos del paciente.' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [currentSymptoms, setCurrentSymptoms] = useState<string[]>([])
  const [patientInfo, setPatientInfo] = useState<PatientInfo>({})
  const allFieldKeys = FULL_GROUPS.flatMap(g => g.fields.map(f => f.key))
  const sessionFieldKeys = SESSION_GROUPS.flatMap(g => g.fields.map(f => f.key))
  const [reportHtml, setReportHtml] = useState<string | null>(null)
  const [formStep, setFormStep] = useState(0)
  const [selectedDiagnosis, setSelectedDiagnosis] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [selectedDocument, setSelectedDocument] = useState<string>('')
  const endRef = useRef<HTMLDivElement>(null)
  const sectionRefs = useRef<(HTMLDivElement | null)[]>([])
  const searchRef = useRef<HTMLInputElement>(null)

  // Search state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [showSearchResults, setShowSearchResults] = useState(false)
  const [searching, setSearching] = useState(false)
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const fieldGroups = patientInfoMode === 'full' ? FULL_GROUPS : SESSION_GROUPS

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (phase === 'patient_info') {
      const el = sectionRefs.current[formStep]
      if (el) {
        const first = el.querySelector('input, select') as HTMLElement
        if (first) setTimeout(() => first.focus(), 100)
      }
    }
  }, [formStep, phase])

  useEffect(() => {
    if (phase === 'search' && searchRef.current) {
      searchRef.current.focus()
    }
  }, [phase])

  const doSearch = useCallback(async (q: string) => {
    if (!q || q.length < 1) {
      setSearchResults([])
      setShowSearchResults(false)
      return
    }
    setSearching(true)
    try {
      const res = await fetch(`${API}/api/clinical-history/search?q=${encodeURIComponent(q)}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const data: SearchResult[] = await res.json()
        setSearchResults(data)
        setShowSearchResults(true)
      }
    } catch {
      // silent
    }
    setSearching(false)
  }, [token])

  const handleSearchChange = (value: string) => {
    const digits = value.replace(/\D/g, '')
    setSearchQuery(digits)
    setShowSearchResults(true)
    if (searchTimer.current) clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => doSearch(digits), 200)
  }

  const selectPatient = async (result: SearchResult) => {
    setShowSearchResults(false)
    setSelectedDocument(result.document_number)
    setSearchQuery(`${result.document_number} — ${result.first_name} ${result.last_name}`)

    if (result.has_clinical_history) {
      setPatientInfoMode('session_only')
      const base = result.base_data
      setPatientInfo({
        first_name: base.first_name || result.first_name,
        last_name: base.last_name || result.last_name,
        name: `${base.first_name || result.first_name} ${base.last_name || result.last_name}`.trim(),
        document_type: base.document_type || result.document_type,
        id_document: result.document_number,
        birth_date: base.birth_date || '',
        age: base.age || '',
        gender: base.gender || '',
        phone: base.phone || '',
        country: base.country || '',
        department: base.department || '',
        city: base.city || '',
        location: base.city || '',
      })
      setPhase('patient_info')
      setFormStep(0)
    } else if (result.has_user_account) {
      setPatientInfoMode('full')
      const base = result.base_data
      setPatientInfo({
        first_name: base.first_name || result.first_name,
        last_name: base.last_name || result.last_name,
        name: `${base.first_name || result.first_name} ${base.last_name || result.last_name}`.trim(),
        document_type: base.document_type || result.document_type,
        id_document: result.document_number,
        birth_date: base.birth_date || '',
        age: '',
        gender: '',
        occupation: '',
        phone: base.phone || '',
        country: base.country || '',
        department: base.department || '',
        city: base.city || '',
        location: base.city || '',
      })
      setPhase('patient_info')
      setFormStep(0)
    }
  }

  const startNewPatient = () => {
    setPatientInfoMode('full')
    setSelectedDocument('')
    setPatientInfo({})
    setSearchQuery('')
    setShowSearchResults(false)
    setPhase('patient_info')
    setFormStep(0)
  }

  const handlePatientFieldChange = (key: string, value: string) => {
    setPatientInfo(prev => {
      const updated = { ...prev, [key]: value }
      if (key === 'first_name' || key === 'last_name') {
        updated.name = `${updated.first_name || ''} ${updated.last_name || ''}`.trim()
      }
      if (key === 'city') {
        updated.location = value
      }
      return updated
    })
  }

  const submitPatientForm = async () => {
    setLoading(true)
    try {
      const docNum = patientInfo.id_document || selectedDocument
      if (!docNum) throw new Error('Número de documento requerido')

      const headers = {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      }

      let currentSessionId: string | null = null

      if (patientInfoMode === 'full') {
        // Create clinical history
        const histBody = {
          document_number: docNum,
          document_type: patientInfo.document_type || 'CC',
          first_name: patientInfo.first_name || '',
          last_name: patientInfo.last_name || '',
          birth_date: patientInfo.birth_date || '',
          age: patientInfo.age || '',
          gender: patientInfo.gender || '',
          occupation: patientInfo.occupation || '',
          phone: patientInfo.phone || '',
          country: patientInfo.country || '',
          department: patientInfo.department || '',
          city: patientInfo.city || '',
        }

        const histRes = await fetch(`${API}/api/clinical-history`, {
          method: 'POST',
          headers,
          body: JSON.stringify(histBody),
        })

        if (!histRes.ok) {
          const errData = await histRes.json().catch(() => ({}))
          throw new Error(errData.detail || 'Error al crear historia clínica')
        }
      }

      // Create session
      const sessBody: Record<string, string> = {
        consultation_reason: patientInfo.consultation_reason || '',
        symptom_evolution: patientInfo.symptom_evolution || '',
        tobacco: patientInfo.tobacco || '',
        alcohol: patientInfo.alcohol || '',
        substances: patientInfo.substances || '',
        physical_activity: patientInfo.physical_activity || '',
        medical_history: patientInfo.medical_history || '',
        surgical_history: patientInfo.surgical_history || '',
        pharmacological_history: patientInfo.pharmacological_history || '',
        allergies: patientInfo.allergies || '',
        blood_pressure: patientInfo.blood_pressure || '',
        heart_rate: patientInfo.heart_rate || '',
        respiratory_rate: patientInfo.respiratory_rate || '',
        temperature: patientInfo.temperature || '',
        weight: patientInfo.weight || '',
        height: patientInfo.height || '',
      }

      const sessRes = await fetch(`${API}/api/clinical-history/${docNum}/sessions`, {
        method: 'POST',
        headers,
        body: JSON.stringify(sessBody),
      })

      if (!sessRes.ok) {
        const errData = await sessRes.json().catch(() => ({}))
        throw new Error(errData.detail || 'Error al crear sesión')
      }

      const sessData = await sessRes.json()
      currentSessionId = sessData.id
      setSessionId(currentSessionId)

      setMessages(m => [...m, {
        id: crypto.randomUUID(),
        role: 'assistant',
        text: 'Paciente registrado correctamente. Ahora describe los síntomas que presenta.',
      }])

      setPhase('symptoms')
    } catch (err: any) {
      setMessages(m => [...m, { id: crypto.randomUUID(), role: 'assistant', text: `Error: ${err.message}` }])
    }
    setLoading(false)
  }

  const handleSend = async (textOverride?: string) => {
    const text = (textOverride || input).trim()
    if (!text || loading) return
    if (!textOverride) setInput('')

    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', text }
    setMessages(m => [...m, userMsg])

    setLoading(true)
    try {
      const res = await fetch(API + '/api/converse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          current_symptoms: currentSymptoms,
          patient_info: patientInfo,
        }),
      })
      const data = await res.json()

      if (data.normalized_symptoms && data.normalized_symptoms.length > 0) {
        setCurrentSymptoms(data.normalized_symptoms)
      }
      if (data.patient_info && Object.keys(data.patient_info).length > 0) {
        setPatientInfo(data.patient_info)
      }

      const msg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        text: data.reply,
        suggestions: data.suggestions || [],
        diagnoses: data.diagnoses || [],
        treatment: data.treatment || undefined,
      }
      setMessages(m => [...m, msg])
    } catch {
      setMessages(m => [...m, { id: crypto.randomUUID(), role: 'assistant', text: 'Error de conexión con el servidor.' }])
    }
    setLoading(false)
  }

  const handleSuggestion = (symptom: string) => {
    handleSend(symptom)
  }

  const handleSelectDiagnosis = async (disease: string) => {
    setSelectedDiagnosis(disease)
    handleSend(disease)
  }

  const generateReport = async () => {
    setLoading(true)
    try {
      const res = await fetch(API + '/api/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_info: patientInfo,
          symptoms: currentSymptoms,
          selected_diagnosis: selectedDiagnosis,
          session_id: sessionId,
          document_number: patientInfo.id_document || selectedDocument,
        }),
      })
      const data = await res.json()
      setReportHtml(data.html_report)
      setPhase('report')
    } catch {
      setMessages(m => [...m, { id: crypto.randomUUID(), role: 'assistant', text: 'Error generando el reporte.' }])
    }
    setLoading(false)
  }

  const resetAll = () => {
    setPhase('search')
    setPatientInfoMode('full')
    setFormStep(0)
    setReportHtml(null)
    setCurrentSymptoms([])
    setPatientInfo({})
    setSelectedDiagnosis(null)
    setSessionId(null)
    setSelectedDocument('')
    setSearchQuery('')
    setSearchResults([])
    setShowSearchResults(false)
    setMessages([
      { id: '0', role: 'assistant', text: 'Hola, soy Mimetic AI. Antes de comenzar, necesito los datos del paciente.' },
    ])
  }

  const confidenceColor = (c: number) => {
    if (c >= 0.7) return '#22c55e'
    if (c >= 0.4) return '#eab308'
    return '#ef4444'
  }

  const severityColor = (s: string) => {
    switch (s) {
      case 'mild': return '#22c55e'
      case 'moderate': return '#eab308'
      case 'high': return '#f97316'
      case 'critical': return '#ef4444'
      default: return '#6b7280'
    }
  }

  const suggestedSymptoms = messages
    .flatMap((m) => m.suggestions || [])
    .filter((s, i, arr) => arr.indexOf(s) === i)

  // ── SEARCH PHASE ────────────────────────────────────────────────

  if (phase === 'search') {
    return (
      <div className="app">
        <header className="header">
          <img src="/logo.png" alt="Mimetic AI" className="header-logo-lg" />
          <span className="subtitle">Buscar paciente</span>
          <div className="header-right">
            <span className="user-badge">{user?.name}</span>
            <button className="logout-btn" onClick={logout}>Cerrar sesión</button>
          </div>
        </header>

        <div className="chat">
          <div className="search-section">
            <h3>Buscar paciente por número de documento</h3>
            <p className="search-hint">Escribe el número de documento para buscar coincidencias</p>

            <div className="search-input-wrap">
              <input
                ref={searchRef}
                type="text"
                className="search-input"
                placeholder="Ingrese el documento de identidad"
                value={searchQuery}
                onChange={e => handleSearchChange(e.target.value)}
                onFocus={() => searchResults.length > 0 && setShowSearchResults(true)}
                onBlur={() => setTimeout(() => setShowSearchResults(false), 200)}
              />
              {searching && <span className="search-spinner" />}
            </div>

            {showSearchResults && searchResults.length > 0 && (
              <div className="search-results">
                {searchResults.map((r) => (
                  <div
                    key={r.document_number}
                    className="search-result-item"
                    onMouseDown={() => selectPatient(r)}
                  >
                    <div className="search-result-info">
                      <span className="search-result-name">
                        {r.first_name} {r.last_name}
                      </span>
                      <span className="search-result-doc">{r.document_number}</span>
                    </div>
                    <div className="search-result-badges">
                      {r.has_clinical_history && <span className="badge badge-history">Historia Clínica</span>}
                      {r.has_user_account && <span className="badge badge-user">Cuenta Pública</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {showSearchResults && searchResults.length === 0 && searchQuery.length >= 1 && !searching && (
              <div className="search-no-results">
                <p>No se encontraron pacientes con ese documento.</p>
              </div>
            )}

            <div className="search-no-results" style={{ paddingTop: searchQuery ? '0.5rem' : '1rem' }}>
              <button className="patient-submit" onClick={startNewPatient}>
                + Registrar nuevo paciente
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ── PATIENT INFO PHASE ──────────────────────────────────────────

  if (phase === 'patient_info') {
    const filledCount = Object.values(patientInfo).filter(v => v?.toString().trim()).length
    const totalKeys = patientInfoMode === 'full' ? allFieldKeys.length : sessionFieldKeys.length
    const progress = Math.round((filledCount / totalKeys) * 100)
    const sectionIcons = ['📋', '💬', '📄', '🩺']
    const visibleGroup = fieldGroups[formStep]

    return (
      <div className="app">
        <header className="header">
          <img src="/logo.png" alt="Mimetic AI" className="header-logo-lg" />
          <span className="subtitle">
            {patientInfoMode === 'session_only' ? 'Nueva consulta — Datos de la sesión' : 'Datos del paciente'}
          </span>
          <div className="header-right">
            <span className="user-badge">{user?.name}</span>
            <button className="logout-btn" onClick={logout}>Cerrar sesión</button>
          </div>
        </header>

        {patientInfoMode === 'session_only' && (
          <div className="patient-bar">
            <strong>Paciente:</strong> {patientInfo.name || '—'} | {patientInfo.id_document || ''} {patientInfo.age ? `| ${patientInfo.age} años` : ''}
          </div>
        )}

        <div className="chat">
          {messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.role}`}>
              <div className="bubble">
                <div className="role-label">{msg.role === 'user' ? 'Doctor' : 'Mimetic AI'}</div>
                <p>{msg.text}</p>
              </div>
            </div>
          ))}

          <div className="patient-form">
            <div className="patient-form-header">
              <h3>{patientInfoMode === 'session_only' ? 'Datos de la Consulta' : 'Registro del Paciente'}</h3>
              <span className="patient-step-count">{formStep + 1} / {fieldGroups.length}</span>
            </div>

            <div className="patient-progress-bar">
              <div className="patient-progress-fill" style={{ width: `${progress}%` }} />
            </div>

            <div className="patient-steps">
              {fieldGroups.map((group, gi) => {
                const isActive = gi === formStep
                const isDone = group.fields.every(f => patientInfo[f.key as keyof PatientInfo]?.trim())
                return (
                  <div
                    key={gi}
                    className={`patient-step ${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`}
                    onClick={() => gi <= formStep + 1 && setFormStep(gi)}
                    style={gi <= formStep + 1 ? { cursor: 'pointer' } : {}}
                  >
                    <div className={`patient-step-num ${isDone ? 'done' : ''}`}>
                      {isDone ? '✓' : sectionIcons[gi]}
                    </div>
                    <span className="patient-step-label">{group.title}</span>
                  </div>
                )
              })}
            </div>

            <div className="patient-section visible" ref={el => sectionRefs.current[formStep] = el}>
              <h4 className="patient-section-title">
                {sectionIcons[formStep]} {visibleGroup.title}
              </h4>
              <div className="patient-fields-grid">
                {visibleGroup.fields.map((f) => {
                  const val = patientInfo[f.key as keyof PatientInfo] || ''
                  const filled = !!val.trim()
                  return (
                    <div key={f.key} className={`patient-field ${filled ? 'filled' : ''}`}>
                      <div className="patient-field-label-row">
                        <label>{f.label}</label>
                        {filled && <span className="patient-field-check">✓</span>}
                      </div>
                      <div className="patient-field-input-wrap">
                        {f.type === 'select' ? (
                          <select
                            value={val}
                            onChange={e => handlePatientFieldChange(f.key, e.target.value)}
                            disabled={loading}
                          >
                            <option value="">-- Seleccionar --</option>
                            {f.options?.map(o => (
                              <option key={o.value} value={o.value}>{o.label}</option>
                            ))}
                          </select>
                        ) : (
                          <input
                            type="text"
                            placeholder={f.placeholder}
                            value={val}
                            onChange={e => handlePatientFieldChange(f.key, e.target.value)}
                            onKeyDown={e => {
                              if (e.key === 'Enter') {
                                const inputs = document.querySelectorAll('.patient-section.visible input, .patient-section.visible select')
                                const current = Array.from(inputs).indexOf(e.target as HTMLElement)
                                const next = inputs[current + 1] as HTMLElement
                                if (next) next.focus()
                              }
                            }}
                            disabled={loading}
                          />
                        )}
                        {f.suffix && <span className="patient-field-suffix">{f.suffix}</span>}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="patient-nav">
              {formStep > 0 && (
                <button className="patient-nav-btn" onClick={() => setFormStep(s => s - 1)}>
                  ← Anterior
                </button>
              )}
              {formStep < fieldGroups.length - 1 && (
                <button
                  className="patient-nav-btn primary"
                  onClick={() => setFormStep(s => Math.min(s + 1, fieldGroups.length - 1))}
                >
                  Siguiente →
                </button>
              )}
            </div>

            {formStep === fieldGroups.length - 1 && (
              <div className="patient-summary">
                <h4 className="patient-section-title">📋 Resumen</h4>
                <div className="patient-summary-grid">
                  {fieldGroups.map((g, gi) => (
                    <div key={gi} className="patient-summary-group">
                      <strong>{g.title}</strong>
                      {g.fields.map(f => {
                        const val = patientInfo[f.key as keyof PatientInfo]
                        if (!val?.trim()) return null
                        return <span key={f.key} className="patient-summary-item"><em>{f.label}:</em> {val}</span>
                      })}
                    </div>
                  ))}
                </div>
                <button
                  className="patient-submit"
                  onClick={submitPatientForm}
                  disabled={loading}
                >
                  {loading ? 'Guardando...' : '✓ Finalizar y comenzar consulta'}
                </button>
              </div>
            )}
          </div>

          <div ref={endRef} />
        </div>
      </div>
    )
  }

  // ── REPORT PHASE ────────────────────────────────────────────────

  if (phase === 'report' && reportHtml) {
    return (
      <div className="app">
        <header className="header">
          <h1>Historia Clínica</h1>
          <span className="subtitle">Mimetic AI - Reporte generado</span>
          <div className="header-right">
            <span className="user-badge">{user?.name}</span>
            <button className="logout-btn" onClick={logout}>Cerrar sesión</button>
          </div>
        </header>

        <div className="report-container">
          <iframe
            srcDoc={reportHtml}
            title="Reporte Clínico"
            className="report-frame"
          />
        </div>

        <div className="report-actions">
          <button onClick={() => { setPhase('symptoms'); setReportHtml(null) }}>
            Volver al diagnóstico
          </button>
          <button onClick={resetAll}>
            Nueva consulta
          </button>
        </div>
      </div>
    )
  }

  // ── SYMPTOMS PHASE ──────────────────────────────────────────────

  return (
    <div className="app">
      <header className="header">
        <h1>Mimetic AI</h1>
        <span className="subtitle">Diagnóstico conversacional</span>
        <div className="header-right">
          <span className="user-badge">{user?.name}</span>
          <button className="logout-btn" onClick={logout}>Cerrar sesión</button>
        </div>
      </header>

      {Object.keys(patientInfo).length > 0 && (
        <div className="patient-bar">
          <strong>Paciente:</strong> {patientInfo.name || '—'} | {patientInfo.id_document || ''} {patientInfo.age ? `| ${patientInfo.age} años` : ''} {patientInfo.weight ? `| ${patientInfo.weight} kg` : ''} {patientInfo.height ? `| ${patientInfo.height} cm` : ''}
        </div>
      )}

      <div className="chat">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <div className="bubble">
              <div className="role-label">{msg.role === 'user' ? 'Doctor' : 'Mimetic AI'}</div>
              <p>{msg.text}</p>

              {msg.suggestions && msg.suggestions.length > 0 && (
                <div className="suggestions">
                  <strong>Sugerencias:</strong>
                  <div className="suggestion-tags">
                    {msg.suggestions.map((s) => (
                      <button key={s} className="tag" onClick={() => handleSuggestion(s)}>
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {msg.diagnoses && msg.diagnoses.length > 0 && (
                <div className="diagnoses">
                  <strong>Diagnósticos:</strong>
                  {msg.diagnoses.map((d) => (
                    <div
                      key={d.disease_name}
                      className={`diagnosis-card ${selectedDiagnosis === d.disease_name ? 'selected' : ''}`}
                      onClick={() => handleSelectDiagnosis(d.disease_name)}
                    >
                      <div className="diagnosis-header">
                        <span className="diagnosis-name">{d.disease_name}</span>
                        <span className="confidence" style={{ color: confidenceColor(d.confidence) }}>
                          {Math.round(d.confidence * 100)}%
                        </span>
                      </div>
                      <div className="diagnosis-body">
                        <p>{d.description}</p>
                        <div className="diagnosis-meta">
                          <span className="severity" style={{ background: severityColor(d.severity) }}>
                            {d.severity}
                          </span>
                          <span>{d.matched_symptoms}/{d.total_input_symptoms} síntomas</span>
                        </div>
                      </div>
                    </div>
                  ))}
                  <p className="hint">Escribe o haz clic en el nombre del diagnóstico para ver el tratamiento</p>
                </div>
              )}

              {msg.treatment && (
                <div className="treatment">
                  <strong>Tratamiento recomendado:</strong>
                  {msg.treatment.medicines.length > 0 ? (
                    <table>
                      <thead>
                        <tr>
                          <th>Medicamento</th>
                          <th>Dosis</th>
                          <th>Frecuencia</th>
                          <th>Duración</th>
                        </tr>
                      </thead>
                      <tbody>
                        {msg.treatment.medicines.map((m, i) => (
                          <tr key={i}>
                            <td>{m.name}</td>
                            <td>{m.dosage}</td>
                            <td>{m.frequency}</td>
                            <td>{m.duration}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p className="no-meds">No requiere medicamentos</p>
                  )}
                  {msg.treatment.general_recommendations && (
                    <div className="recommendations">
                      <strong>Recomendaciones:</strong>
                      <p>{msg.treatment.general_recommendations}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="bubble typing">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>

      {currentSymptoms.length > 0 && !loading && (
        <div className="quick-symptoms">
          {suggestedSymptoms.map((s) => (
            <button key={s} className="quick-chip" onClick={() => handleSuggestion(s)}>
              + {s}
            </button>
          ))}
          <button className="quick-chip report" onClick={() => handleSend('listo')}>
            Ver diagnósticos
          </button>
        </div>
      )}

      {selectedDiagnosis && (
        <div className="report-bar">
          <button className="generate-report-btn" onClick={generateReport} disabled={loading}>
            {loading ? 'Generando...' : 'Generar historia clínica y receta'}
          </button>
        </div>
      )}

      <div className="input-bar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Describe el síntoma..."
          disabled={loading}
        />
        <button onClick={() => handleSend()} disabled={loading || !input.trim()}>
          Enviar
        </button>
      </div>
    </div>
  )
}
