import { useState, type RefObject } from 'react'
import type { Diagnosis, DoctorReview, Message, PatientInfo, Treatment } from './types'

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
  doctorReview: DoctorReview
  endRef: RefObject<HTMLDivElement>
  onSend: (textOverride?: string) => void
  onSuggestion: (symptom: string) => void
  onSelectDiagnosis: (disease: string) => void
  onGenerateReport: () => void
  onToggleDiagnosisConfirmation: (disease: string) => void
  onToggleDiagnosisRejection: (disease: string) => void
  onAddManualDiagnosis: (diseaseName: string, notes?: string) => void
  onRemoveManualDiagnosis: (id: string) => void
  onToggleMedicine: (medicineName: string) => void
  onUpdateDose: (medicineName: string, newDose: string) => void
  onSetDoctorNotes: (notes: string) => void
  confidenceColor: (c: number) => string
  severityColor: (s: string) => string
}

function DiagnosisCard({
  d, selected, onSelect, confidenceColor, severityColor,
  confirmed, rejected, onConfirm, onReject,
}: {
  d: Diagnosis
  selected: boolean
  onSelect: (disease: string) => void
  confidenceColor: (c: number) => string
  severityColor: (s: string) => string
  confirmed: boolean
  rejected: boolean
  onConfirm: (disease: string) => void
  onReject: (disease: string) => void
}) {
  return (
    <div
      className={`diagnosis-card ${selected ? 'selected' : ''} ${confirmed ? 'confirmed' : ''} ${rejected ? 'rejected' : ''}`}
    >
      <div className="diagnosis-header">
        <div className="diagnosis-title-group">
          <input
            type="checkbox"
            className="diagnosis-check"
            checked={confirmed}
            onClick={(e) => e.stopPropagation()}
            onChange={() => onConfirm(d.disease_name)}
            title="Confirmar diagnóstico"
          />
          <span className="diagnosis-name" onClick={() => onSelect(d.disease_name)}>{d.disease_name}</span>
        </div>
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
        <button
          className={`diag-reject-btn ${rejected ? 'active' : ''}`}
          onClick={(e) => { e.stopPropagation(); onReject(d.disease_name) }}
        >
          {rejected ? '✓ Descartado' : 'Descartar'}
        </button>
      </div>
    </div>
  )
}

function TreatmentBlock({
  treatment, doctorReview, onToggleMedicine, onUpdateDose,
}: {
  treatment: Treatment
  doctorReview: DoctorReview
  onToggleMedicine: (medicineName: string) => void
  onUpdateDose: (medicineName: string, newDose: string) => void
}) {
  const newMedicines = treatment.available && treatment.available.length > 0
    ? treatment.available
    : (treatment.medicines || [])

  const isSelected = (name: string) => doctorReview.selectedMedicines.includes(name)

  return (
    <div className="treatment">
      <strong>Tratamiento para {treatment.disease_name}:</strong>

      {newMedicines.length > 0 && (
        <>
          <h4 className="tx-subtitle">Medicamentos Recomendados</h4>
          <table>
            <thead>
              <tr>
                <th>Incluir</th>
                <th>Medicamento</th>
                <th>Dosis</th>
                <th>Vía</th>
                <th>Frecuencia</th>
                <th>Duración</th>
                <th>Monitoreo</th>
              </tr>
            </thead>
            <tbody>
              {newMedicines.map((m, i) => {
                const medName = m.name
                return (
                  <tr key={i} className={isSelected(medName) ? 'med-selected' : 'med-unselected'}>
                    <td>
                      <input
                        type="checkbox"
                        checked={isSelected(medName)}
                        onChange={() => onToggleMedicine(medName)}
                        title="Incluir en receta"
                      />
                    </td>
                    <td>
                      <strong>{medName}</strong>
                      {m.reasons && m.reasons.length > 0 && (
                        <div className="tx-contra">{m.reasons.join('; ')}</div>
                      )}
                      {m.patient_summary && <div className="tx-summary">{m.patient_summary}</div>}
                    </td>
                    <td>
                      {m.calculated_dosage ? <span className="tx-calc">{m.calculated_dosage}</span> : m.dosage}
                      {m.max_daily_dose && <div className="tx-max">Máx: {m.max_daily_dose}</div>}
                      {m.dosage_mg_kg && <div className="tx-kg">{m.dosage_mg_kg}</div>}
                      <input
                        className="dose-edit"
                        value={doctorReview.modifiedDoses[medName] ?? ''}
                        placeholder="Ajustar dosis..."
                        onChange={(e) => onUpdateDose(medName, e.target.value)}
                      />
                    </td>
                    <td>{m.route || 'Oral'}</td>
                    <td>{m.frequency}</td>
                    <td>{m.duration}</td>
                    <td>{m.monitoring || '—'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </>
      )}

      {treatment.available && treatment.available.length > 0 && treatment.available.some(m => m.adjustments) && (
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
                <th>Incluir</th>
                <th>Alternativa</th>
                <th>Dosis</th>
                <th>Vía</th>
                <th>Frecuencia</th>
                <th>Duración</th>
              </tr>
            </thead>
            <tbody>
              {treatment.alternatives.map((m, i) => (
                <tr key={i} className={isSelected(m.name) ? 'med-selected' : 'med-unselected'}>
                  <td>
                    <input
                      type="checkbox"
                      checked={isSelected(m.name)}
                      onChange={() => onToggleMedicine(m.name)}
                    />
                  </td>
                  <td>
                    <strong>{m.name}</strong>
                    {m.patient_summary && <div className="tx-summary">{m.patient_summary}</div>}
                  </td>
                  <td>
                    {m.dosage}{m.max_daily_dose ? <div className="tx-max">Máx: {m.max_daily_dose}</div> : ''}
                    <input
                      className="dose-edit"
                      value={doctorReview.modifiedDoses[m.name] ?? ''}
                      placeholder="Ajustar dosis..."
                      onChange={(e) => onUpdateDose(m.name, e.target.value)}
                    />
                  </td>
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
  doctorReview, onToggleDiagnosisConfirmation, onToggleDiagnosisRejection,
  onToggleMedicine, onUpdateDose,
}: {
  msg: Message
  selectedDiagnosis: string | null
  onSuggestion: (symptom: string) => void
  onSelectDiagnosis: (disease: string) => void
  confidenceColor: (c: number) => string
  severityColor: (s: string) => string
  doctorReview: DoctorReview
  onToggleDiagnosisConfirmation: (disease: string) => void
  onToggleDiagnosisRejection: (disease: string) => void
  onToggleMedicine: (medicineName: string) => void
  onUpdateDose: (medicineName: string, newDose: string) => void
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
          <strong>Diagnósticos (marca los que confirmas):</strong>
          {msg.diagnoses.map((d) => (
            <DiagnosisCard
              key={d.disease_name}
              d={d}
              selected={selectedDiagnosis === d.disease_name}
              onSelect={onSelectDiagnosis}
              confidenceColor={confidenceColor}
              severityColor={severityColor}
              confirmed={doctorReview.confirmedDiagnoses.includes(d.disease_name)}
              rejected={doctorReview.rejectedDiagnoses.includes(d.disease_name)}
              onConfirm={onToggleDiagnosisConfirmation}
              onReject={onToggleDiagnosisRejection}
            />
          ))}
          <p className="hint">Escribe o haz clic en el nombre del diagnóstico para ver el tratamiento</p>
        </div>
      )}

      {msg.treatment && (
        <TreatmentBlock
          treatment={msg.treatment}
          doctorReview={doctorReview}
          onToggleMedicine={onToggleMedicine}
          onUpdateDose={onUpdateDose}
        />
      )}
    </div>
  )
}

export default function SymptomsPhase({
  user, onLogout, patientInfo, messages, input, setInput, isSending, isGeneratingReport,
  currentSymptoms, suggestedSymptoms, selectedDiagnosis, doctorReview, endRef, onSend, onSuggestion,
  onSelectDiagnosis, onGenerateReport, onToggleDiagnosisConfirmation, onToggleDiagnosisRejection,
  onAddManualDiagnosis, onRemoveManualDiagnosis, onToggleMedicine, onUpdateDose, onSetDoctorNotes,
  confidenceColor, severityColor,
}: Props) {
  const [manualDiagInput, setManualDiagInput] = useState('')

  const handleAddManualDiagnosis = () => {
    if (manualDiagInput.trim()) {
      onAddManualDiagnosis(manualDiagInput.trim())
      setManualDiagInput('')
    }
  }

  const hasConfirmedDiagnosis = doctorReview.confirmedDiagnoses.length > 0
    || doctorReview.manualDiagnoses.length > 0

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
          {doctorReview.confirmedDiagnoses.length > 0 && (
            <span className="doctor-review-badge">
              ✓ {doctorReview.confirmedDiagnoses.length + doctorReview.manualDiagnoses.length} diagnóstico(s) confirmado(s)
            </span>
          )}
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
              doctorReview={doctorReview}
              onToggleDiagnosisConfirmation={onToggleDiagnosisConfirmation}
              onToggleDiagnosisRejection={onToggleDiagnosisRejection}
              onToggleMedicine={onToggleMedicine}
              onUpdateDose={onUpdateDose}
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

      <div className="manual-diagnoses">
        <div className="add-manual-diagnosis">
          <input
            value={manualDiagInput}
            onChange={(e) => setManualDiagInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddManualDiagnosis()}
            placeholder="Agregar diagnóstico manual del doctor..."
          />
          <button onClick={handleAddManualDiagnosis}>+ Agregar</button>
        </div>

        {doctorReview.manualDiagnoses.length > 0 && (
          <>
            <strong>Diagnósticos agregados por el doctor:</strong>
            {doctorReview.manualDiagnoses.map((d) => (
              <div key={d.id} className="manual-diagnosis-item">
                <span>{d.disease_name}</span>
                {d.notes && <em>{d.notes}</em>}
                <button onClick={() => onRemoveManualDiagnosis(d.id)}>×</button>
              </div>
            ))}
          </>
        )}
      </div>

      {hasConfirmedDiagnosis && (
        <div className="notes-section">
          <label htmlFor="doctor-notes">Notas del doctor:</label>
          <textarea
            id="doctor-notes"
            value={doctorReview.doctorNotes}
            onChange={(e) => onSetDoctorNotes(e.target.value)}
            placeholder="Agrega observaciones, ajustes de dosis, recomendaciones específicas..."
            rows={3}
          />
        </div>
      )}

      {hasConfirmedDiagnosis && (
        <div className="report-bar">
          <button className="generate-report-btn" onClick={onGenerateReport} disabled={isGeneratingReport}>
            {isGeneratingReport ? 'Generando...' : 'Confirmar y generar historia clínica'}
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