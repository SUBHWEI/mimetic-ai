import { useState, useRef, useEffect } from 'react'
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
  name?: string
  document_type?: string
  id_document?: string
  birth_date?: string
  age?: string
  gender?: string
  occupation?: string
  phone?: string
  location?: string
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

const FIELD_GROUPS: { title: string; fields: FieldConfig[] }[] = [
  {
    title: 'Identificación del Paciente',
    fields: [
      { key: 'name', label: 'Nombre completo', placeholder: 'Ej: Juan Pérez' },
      { key: 'document_type', label: 'Tipo de documento', type: 'select', options: [
        { value: 'CC', label: 'Cédula de Ciudadanía (CC)' },
        { value: 'TI', label: 'Tarjeta de Identidad (TI)' },
        { value: 'CE', label: 'Cédula de Extranjería (CE)' },
        { value: 'RC', label: 'Registro Civil (RC)' },
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
      { key: 'location', label: 'Ciudad de residencia', placeholder: 'Ej: Bogotá' },
    ],
  },
  {
    title: 'Anamnesis',
    fields: [
      { key: 'consultation_reason', label: 'Motivo de consulta', placeholder: 'Describe brevemente el motivo' },
      { key: 'symptom_evolution', label: 'Tiempo de evolución', placeholder: 'Ej: 3 días', suffix: 'días/semanas' },
    ],
  },
  {
    title: 'Antecedentes Personales',
    fields: [
      { key: 'tobacco', label: 'Consumo de tabaco', placeholder: 'Sí / No / Frecuencia' },
      { key: 'alcohol', label: 'Consumo de alcohol', placeholder: 'Sí / No / Frecuencia' },
      { key: 'substances', label: 'Uso de sustancias', placeholder: 'Sí / No / Especificar' },
      { key: 'physical_activity', label: 'Actividad física', type: 'select', options: [
        { value: 'Activo', label: 'Activo (ejercicio regular)' },
        { value: 'Sedentario', label: 'Sedentario (poco o ningún ejercicio)' },
      ]},
      { key: 'medical_history', label: 'Antecedentes médicos', placeholder: 'Diabetes, HTA, etc.' },
      { key: 'surgical_history', label: 'Antecedentes quirúrgicos', placeholder: 'Cirugías previas' },
      { key: 'pharmacological_history', label: 'Antecedentes farmacológicos', placeholder: 'Medicamentos actuales' },
      { key: 'allergies', label: 'Alergias conocidas', placeholder: 'Medicamentos, alimentos, etc.' },
    ],
  },
  {
    title: 'Signos Vitales',
    fields: [
      { key: 'blood_pressure', label: 'Presión arterial (PA)', placeholder: 'Ej: 120/80', suffix: 'mmHg' },
      { key: 'heart_rate', label: 'Frecuencia cardíaca (FC)', placeholder: 'Ej: 72', suffix: 'lpm' },
      { key: 'respiratory_rate', label: 'Frecuencia respiratoria (FR)', placeholder: 'Ej: 16', suffix: 'rpm' },
      { key: 'temperature', label: 'Temperatura', placeholder: 'Ej: 36.5', suffix: '°C' },
      { key: 'weight', label: 'Peso', placeholder: 'Ej: 70', suffix: 'kg' },
      { key: 'height', label: 'Estatura', placeholder: 'Ej: 170', suffix: 'cm' },
    ],
  },
]

export default function ChatApp() {
  const { user, logout } = useAuth()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      role: 'assistant',
      text: 'Hola, soy Mimetic AI. Antes de comenzar, necesito los datos del paciente.',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [currentSymptoms, setCurrentSymptoms] = useState<string[]>([])
  const [patientInfo, setPatientInfo] = useState<PatientInfo>({})
  const [phase, setPhase] = useState<'patient_info' | 'symptoms' | 'report'>('patient_info')
  const allFieldKeys = FIELD_GROUPS.flatMap(g => g.fields.map(f => f.key))
  const [_missingFields, setMissingFields] = useState<string[]>(allFieldKeys)
  const [reportHtml, setReportHtml] = useState<string | null>(null)
  const [formStep, setFormStep] = useState(0)
  const [selectedDiagnosis, setSelectedDiagnosis] = useState<string | null>(null)
  const endRef = useRef<HTMLDivElement>(null)

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

  const sectionRefs = useRef<(HTMLDivElement | null)[]>([])

  const handlePatientFieldChange = (key: string, value: string) => {
    setPatientInfo(prev => ({ ...prev, [key]: value }))
  }

  const submitPatientInfo = async () => {
    setLoading(true)
    try {
      const res = await fetch(API + '/api/patient', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_info: patientInfo }),
      })
      const data = await res.json()

      setPatientInfo(data.patient_info)
      setMissingFields(data.missing_fields)

      const msg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        text: data.reply,
      }
      setMessages(m => [...m, msg])

      if (data.complete) {
        setPhase('symptoms')
      }
    } catch {
      setMessages(m => [...m, { id: crypto.randomUUID(), role: 'assistant', text: 'Error de conexión.' }])
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

  // Patient info form
  if (phase === 'patient_info') {
    const filledCount = Object.values(patientInfo).filter(v => v?.toString().trim()).length
    const progress = Math.round((filledCount / allFieldKeys.length) * 100)
    const sectionIcons = ['📋', '💬', '📄', '🩺']
    const visibleGroup = FIELD_GROUPS[formStep]

    return (
      <div className="app">
        <header className="header">
          <img src="/logo.png" alt="Mimetic AI" className="header-logo-lg" />
          <span className="subtitle">Datos del paciente</span>
          <div className="header-right">
            <span className="user-badge">{user?.name}</span>
            <button className="logout-btn" onClick={logout}>Cerrar sesión</button>
          </div>
        </header>

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
              <h3>Registro del Paciente</h3>
              <span className="patient-step-count">{formStep + 1} / {FIELD_GROUPS.length}</span>
            </div>

            <div className="patient-progress-bar">
              <div className="patient-progress-fill" style={{ width: `${progress}%` }} />
            </div>

            <div className="patient-steps">
              {FIELD_GROUPS.map((group, gi) => {
                const isActive = gi === formStep
                const isDone = group.fields.every(f => patientInfo[f.key as keyof PatientInfo]?.trim())
                return (
                  <div key={gi} className={`patient-step ${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`}>
                    <div className={`patient-step-num ${isDone ? 'done' : ''}`}>
                      {isDone ? '✓' : sectionIcons[gi]}
                    </div>
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
              {formStep < FIELD_GROUPS.length - 1 && (
                <button
                  className="patient-nav-btn primary"
                  onClick={() => setFormStep(s => Math.min(s + 1, FIELD_GROUPS.length - 1))}
                >
                  Siguiente →
                </button>
              )}
            </div>

            {/* Summary + Submit at the bottom */}
            {formStep === FIELD_GROUPS.length - 1 && (
              <div className="patient-summary">
                <h4 className="patient-section-title">📋 Resumen del Paciente</h4>
                <div className="patient-summary-grid">
                  {FIELD_GROUPS.map((g, gi) => (
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
                  onClick={submitPatientInfo}
                  disabled={loading}
                >
                  {loading ? 'Registrando...' : '✓ Finalizar y comenzar consulta'}
                </button>
              </div>
            )}
          </div>

          <div ref={endRef} />
        </div>
      </div>
    )
  }

  // Report view
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
          <button onClick={() => { setPhase('patient_info'); setFormStep(0); setReportHtml(null); setCurrentSymptoms([]); setPatientInfo({}); setSelectedDiagnosis(null); setMissingFields(FIELD_GROUPS.flatMap(g => g.fields.map(f => f.key))); setMessages([
            { id: '0', role: 'assistant', text: 'Hola, soy Mimetic AI. Antes de comenzar, necesito los datos del paciente.' },
          ]) }}>
            Nueva consulta
          </button>
        </div>
      </div>
    )
  }

  // Main chat (symptoms phase)
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

      {/* Patient info sidebar */}
      {Object.keys(patientInfo).length > 0 && (
        <div className="patient-bar">
          <strong>Paciente:</strong> {patientInfo.name || '—'} | {patientInfo.age ? `${patientInfo.age} años` : ''} {patientInfo.weight ? `| ${patientInfo.weight} kg` : ''} {patientInfo.height ? `| ${patientInfo.height} cm` : ''}
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

      {/* Report button when a diagnosis is selected and treatment shown */}
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
          placeholder={phase === 'symptoms' ? "Describe el síntoma..." : "Escribe un mensaje..."}
          disabled={loading}
        />
        <button onClick={() => handleSend()} disabled={loading || !input.trim()}>
          Enviar
        </button>
      </div>
    </div>
  )
}
