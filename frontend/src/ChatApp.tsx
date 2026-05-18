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

const FIELD_GROUPS = [
  {
    title: 'Identificación del Paciente',
    fields: [
      { key: 'name', label: 'Nombre completo', placeholder: 'Ej: Juan Pérez' },
      { key: 'document_type', label: 'Tipo de documento', placeholder: 'CC / TI / CE / RC' },
      { key: 'id_document', label: 'Número de documento', placeholder: 'Ej: 123456789' },
      { key: 'birth_date', label: 'Fecha de nacimiento', placeholder: 'DD/MM/AAAA' },
      { key: 'age', label: 'Edad', placeholder: 'Ej: 45' },
      { key: 'gender', label: 'Género', placeholder: 'M / F / Otro' },
      { key: 'occupation', label: 'Ocupación', placeholder: 'Ej: Ingeniero' },
      { key: 'phone', label: 'Teléfono', placeholder: 'Ej: 3001234567' },
      { key: 'location', label: 'Ciudad de residencia', placeholder: 'Ej: Bogotá' },
    ],
  },
  {
    title: 'Anamnesis',
    fields: [
      { key: 'consultation_reason', label: 'Motivo de consulta', placeholder: 'Breve descripción del paciente' },
      { key: 'symptom_evolution', label: 'Tiempo de evolución', placeholder: 'Ej: 3 días' },
    ],
  },
  {
    title: 'Antecedentes Personales',
    fields: [
      { key: 'tobacco', label: 'Consumo de tabaco', placeholder: 'Sí / No / Frecuencia' },
      { key: 'alcohol', label: 'Consumo de alcohol', placeholder: 'Sí / No / Frecuencia' },
      { key: 'substances', label: 'Uso de sustancias', placeholder: 'Sí / No / Especificar' },
      { key: 'physical_activity', label: 'Actividad física', placeholder: 'Activo / Sedentario' },
      { key: 'medical_history', label: 'Antecedentes médicos', placeholder: 'Diabetes, HTA, etc.' },
      { key: 'surgical_history', label: 'Antecedentes quirúrgicos', placeholder: 'Cirugías previas' },
      { key: 'pharmacological_history', label: 'Antecedentes farmacológicos', placeholder: 'Medicamentos actuales' },
      { key: 'allergies', label: 'Alergias conocidas', placeholder: 'Medicamentos, alimentos, etc.' },
    ],
  },
  {
    title: 'Signos Vitales',
    fields: [
      { key: 'blood_pressure', label: 'Presión arterial (mmHg)', placeholder: 'Ej: 120/80' },
      { key: 'heart_rate', label: 'Frecuencia cardíaca (lpm)', placeholder: 'Ej: 72' },
      { key: 'respiratory_rate', label: 'Frecuencia respiratoria (rpm)', placeholder: 'Ej: 16' },
      { key: 'temperature', label: 'Temperatura (°C)', placeholder: 'Ej: 36.5' },
      { key: 'weight', label: 'Peso (kg)', placeholder: 'Ej: 70' },
      { key: 'height', label: 'Estatura (cm)', placeholder: 'Ej: 170' },
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
  const [selectedDiagnosis, setSelectedDiagnosis] = useState<string | null>(null)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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
    return (
      <div className="app">
        <header className="header">
          <h1>Mimetic AI</h1>
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
            <h3>Registro del Paciente</h3>
            {FIELD_GROUPS.map((group, gi) => (
              <div key={gi} className="patient-section">
                <h4 className="patient-section-title">{group.title}</h4>
                {group.fields.map(f => (
                  <div key={f.key} className="patient-field">
                    <label>{f.label}</label>
                    <input
                      type="text"
                      placeholder={f.placeholder}
                      value={patientInfo[f.key as keyof PatientInfo] || ''}
                      onChange={e => handlePatientFieldChange(f.key, e.target.value)}
                      onKeyDown={e => {
                        if (e.key === 'Enter') {
                          const filled = FIELD_GROUPS.some(g => g.fields.some(f => patientInfo[f.key as keyof PatientInfo]?.trim()))
                          if (filled) submitPatientInfo()
                        }
                      }}
                      disabled={loading}
                    />
                  </div>
                ))}
              </div>
            ))}
            <button
              className="patient-submit"
              onClick={submitPatientInfo}
              disabled={loading}
            >
              {loading ? 'Registrando...' : 'Registrar paciente y comenzar'}
            </button>
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
          <button onClick={() => { setPhase('patient_info'); setReportHtml(null); setCurrentSymptoms([]); setPatientInfo({}); setSelectedDiagnosis(null); setMissingFields(FIELD_GROUPS.flatMap(g => g.fields.map(f => f.key))); setMessages([
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
