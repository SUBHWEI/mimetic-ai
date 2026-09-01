import { type RefObject } from 'react'
import type { Diagnosis, Message, PatientInfo, Treatment } from './types'

type Props = {
  user: { name?: string } | null
  onLogout: () => void
  patientInfo: PatientInfo
  messages: Message[]
  input: string
  setInput: (v: string) => void
  isSending: boolean
  isGeneratingReport: boolean
  currentSymptoms: string[]
  suggestedSymptoms: string[]
  selectedDiagnosis: string | null
  endRef: RefObject<HTMLDivElement>
  onSend: (textOverride?: string) => void
  onSuggestion: (symptom: string) => void
  onSelectDiagnosis: (disease: string) => void
  onGenerateReport: () => void
  confidenceColor: (c: number) => string
  severityColor: (s: string) => string
}

function DiagnosisCard({
  d, selected, onSelect, confidenceColor, severityColor,
}: {
  d: Diagnosis
  selected: boolean
  onSelect: (disease: string) => void
  confidenceColor: (c: number) => string
  severityColor: (s: string) => string
}) {
  return (
    <div
      className={`diagnosis-card ${selected ? 'selected' : ''}`}
      onClick={() => onSelect(d.disease_name)}
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
  )
}

function TreatmentBlock({ treatment }: { treatment: Treatment }) {
  return (
    <div className="treatment">
      <strong>Tratamiento para {treatment.disease_name}:</strong>

      {treatment.available && treatment.available.length > 0 && (
        <>
          <h4 className="tx-subtitle">Medicamentos Recomendados</h4>
          <table>
            <thead>
              <tr>
                <th>Medicamento</th>
                <th>Dosis</th>
                <th>Vía</th>
                <th>Frecuencia</th>
                <th>Duración</th>
                <th>Monitoreo</th>
              </tr>
            </thead>
            <tbody>
              {treatment.available.map((m, i) => (
                <tr key={i}>
                  <td>
                    <strong>{m.name}</strong>
                    {m.reasons && m.reasons.length > 0 && (
                      <div className="tx-contra">{m.reasons.join('; ')}</div>
                    )}
                    {m.patient_summary && <div className="tx-summary">{m.patient_summary}</div>}
                  </td>
                  <td>
                    {m.calculated_dosage ? <span className="tx-calc">{m.calculated_dosage}</span> : m.dosage}
                    {m.max_daily_dose && <div className="tx-max">Máx: {m.max_daily_dose}</div>}
                    {m.dosage_mg_kg && <div className="tx-kg">{m.dosage_mg_kg}</div>}
                  </td>
                  <td>{m.route || 'Oral'}</td>
                  <td>{m.frequency}</td>
                  <td>{m.duration}</td>
                  <td>{m.monitoring || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {treatment.available.some(m => m.adjustments) && (
            <div className="tx-details">
              {treatment.available.map((m, i) => (
                m.adjustments && Object.values(m.adjustments).some(v => v) && (
                  <details key={i} className="tx-detail-card">
                    <summary>Ajustes para {m.name}</summary>
                    {m.adjustments?.renal && <p><strong>Renal:</strong> {m.adjustments.renal}</p>}
                    {m.adjustments?.hepatic && <p><strong>Hepático:</strong> {m.adjustments.hepatic}</p>}
                    {m.adjustments?.pediatric && <p><strong>Pediátrico:</strong> {m.adjustments.pediatric}</p>}
                    {m.adjustments?.geriatric && <p><strong>Geriatría:</strong> {m.adjustments.geriatric}</p>}
                    {m.adjustments?.pregnancy && <p><strong>Embarazo:</strong> {m.adjustments.pregnancy}</p>}
                    {m.interactions_warning && <p className="tx-warn"><strong>Interacciones:</strong> {m.interactions_warning}</p>}
                    {m.contraindications && (m.contraindications.conditions?.length > 0 || m.contraindications.allergies?.length > 0) && (
                      <p className="tx-contra-block">
                        <strong>Contraindicaciones:</strong>{' '}
                        {[...(m.contraindications.conditions || []), ...(m.contraindications.allergies || [])].join(', ')}
                      </p>
                    )}
                  </details>
                )
              ))}
            </div>
          )}

          {treatment.not_recommended && treatment.not_recommended.length > 0 && (
            <div className="tx-not-rec">
              <h4 className="tx-subtitle warn">Medicamentos No Recomendados</h4>
              {treatment.not_recommended.map((m, i) => (
                <div key={i} className="tx-excl">
                  <strong>{m.name}</strong> — {m.reasons?.join(', ') || 'Contraindicado'}
                  {m.patient_summary && <div className="tx-summary">{m.patient_summary}</div>}
                </div>
              ))}
            </div>
          )}

          {treatment.alternatives && treatment.alternatives.length > 0 && (
            <div className="tx-alt">
              <h4 className="tx-subtitle">Medicamentos Alternativos</h4>
              <table>
                <thead>
                  <tr>
                    <th>Alternativa</th>
                    <th>Dosis</th>
                    <th>Vía</th>
                    <th>Frecuencia</th>
                    <th>Duración</th>
                  </tr>
                </thead>
                <tbody>
                  {treatment.alternatives.map((m, i) => (
                    <tr key={i}>
                      <td>
                        <strong>{m.name}</strong>
                        {m.patient_summary && <div className="tx-summary">{m.patient_summary}</div>}
                      </td>
                      <td>{m.dosage}{m.max_daily_dose ? <div className="tx-max">Máx: {m.max_daily_dose}</div> : ''}</td>
                      <td>{m.route || 'Oral'}</td>
                      <td>{m.frequency}</td>
                      <td>{m.duration}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {treatment.non_pharmacological && treatment.non_pharmacological.length > 0 && (
            <div className="tx-non-pharm">
              <h4 className="tx-subtitle">Tratamientos No Farmacológicos</h4>
              <ul>
                {treatment.non_pharmacological.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {treatment.medicines && (
        <>
          {treatment.medicines.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Medicamento</th>
                  <th>Dosis</th>
                  <th>Vía</th>
                  <th>Frecuencia</th>
                  <th>Duración</th>
                </tr>
              </thead>
              <tbody>
                {treatment.medicines.map((m, i) => (
                  <tr key={i}>
                    <td>
                      {m.name}
                      {m.patient_summary && <div className="tx-summary">{m.patient_summary}</div>}
                    </td>
                    <td>{m.dosage}{m.max_daily_dose ? <div className="tx-max">Máx: {m.max_daily_dose}</div> : ''}</td>
                    <td>{m.route || 'Oral'}</td>
                    <td>{m.frequency}</td>
                    <td>{m.duration}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="no-meds">No requiere medicamentos</p>
          )}
        </>
      )}

      {treatment.general_recommendations && (
        <div className="recommendations">
          <strong>Recomendaciones:</strong>
          <p>{treatment.general_recommendations}</p>
        </div>
      )}
    </div>
  )
}

function MessageBubble({
  msg, selectedDiagnosis, onSuggestion, onSelectDiagnosis, confidenceColor, severityColor,
}: {
  msg: Message
  selectedDiagnosis: string | null
  onSuggestion: (symptom: string) => void
  onSelectDiagnosis: (disease: string) => void
  confidenceColor: (c: number) => string
  severityColor: (s: string) => string
}) {
  return (
    <div className="bubble">
      <div className="role-label">{msg.role === 'user' ? 'Doctor' : 'Mimetic AI'}</div>
      <p>{msg.text}</p>

      {msg.suggestions && msg.suggestions.length > 0 && (
        <div className="suggestions">
          <strong>Sugerencias:</strong>
          <div className="suggestion-tags">
            {msg.suggestions.map((s) => (
              <button key={s} className="tag" onClick={() => onSuggestion(s)}>
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
            <DiagnosisCard
              key={d.disease_name}
              d={d}
              selected={selectedDiagnosis === d.disease_name}
              onSelect={onSelectDiagnosis}
              confidenceColor={confidenceColor}
              severityColor={severityColor}
            />
          ))}
          <p className="hint">Escribe o haz clic en el nombre del diagnóstico para ver el tratamiento</p>
        </div>
      )}

      {msg.treatment && <TreatmentBlock treatment={msg.treatment} />}
    </div>
  )
}

export default function SymptomsPhase({
  user, onLogout, patientInfo, messages, input, setInput, isSending, isGeneratingReport,
  currentSymptoms, suggestedSymptoms, selectedDiagnosis, endRef, onSend, onSuggestion,
  onSelectDiagnosis, onGenerateReport, confidenceColor, severityColor,
}: Props) {
  return (
    <div className="app">
      <header className="header">
        <h1>Mimetic AI</h1>
        <span className="subtitle">Diagnóstico conversacional</span>
        <div className="header-right">
          <span className="user-badge">{user?.name}</span>
          <button className="logout-btn" onClick={onLogout}>Cerrar sesión</button>
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
            <MessageBubble
              msg={msg}
              selectedDiagnosis={selectedDiagnosis}
              onSuggestion={onSuggestion}
              onSelectDiagnosis={onSelectDiagnosis}
              confidenceColor={confidenceColor}
              severityColor={severityColor}
            />
          </div>
        ))}

        {isSending && (
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

      {currentSymptoms.length > 0 && !isSending && (
        <div className="quick-symptoms">
          {suggestedSymptoms.map((s) => (
            <button key={s} className="quick-chip" onClick={() => onSuggestion(s)}>
              + {s}
            </button>
          ))}
          <button className="quick-chip report" onClick={() => onSend('listo')}>
            Ver diagnósticos
          </button>
        </div>
      )}

      {selectedDiagnosis && (
        <div className="report-bar">
          <button className="generate-report-btn" onClick={onGenerateReport} disabled={isGeneratingReport}>
            {isGeneratingReport ? 'Generando...' : 'Generar historia clínica y receta'}
          </button>
        </div>
      )}

      <div className="input-bar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onSend()}
          placeholder="Describe el síntoma..."
          disabled={isSending}
        />
        <button onClick={() => onSend()} disabled={isSending || !input.trim()}>
          Enviar
        </button>
      </div>
    </div>
  )
}