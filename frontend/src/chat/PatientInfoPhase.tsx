import { type MutableRefObject, type RefObject } from 'react'
import { SECTION_ICONS } from './constants'
import type { Message, PatientInfo, PatientInfoMode, SearchResult } from './types'

type FieldGroup = { title: string; fields: { key: string; label: string; placeholder?: string; type?: 'text' | 'select'; options?: { value: string; label: string }[]; suffix?: string; condition?: (info: PatientInfo) => boolean }[] }

export type SearchResultType = SearchResult

type Props = {
  user: { name?: string } | null
  onLogout: () => void
  patientInfoMode: PatientInfoMode
  patientInfo: PatientInfo
  formStep: number
  setFormStep: (updater: number | ((s: number) => number)) => void
  fieldGroups: FieldGroup[]
  allFieldKeys: string[]
  sessionFieldKeys: string[]
  sectionRefs: MutableRefObject<(HTMLDivElement | null)[]>
  messages: Message[]
  endRef: RefObject<HTMLDivElement>
  isSending: boolean
  onFieldChange: (key: string, value: string) => void
  onSubmit: () => void
}

export default function PatientInfoPhase({
  user, onLogout, patientInfoMode, patientInfo, formStep, setFormStep, fieldGroups,
  allFieldKeys, sessionFieldKeys, sectionRefs, messages, endRef, isSending, onFieldChange, onSubmit,
}: Props) {
  const filledCount = Object.values(patientInfo).filter(v => v?.toString().trim()).length
  const totalKeys = patientInfoMode === 'full' ? allFieldKeys.length : sessionFieldKeys.length
  const progress = Math.round((filledCount / totalKeys) * 100)
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
          <button className="logout-btn" onClick={onLogout}>Cerrar sesión</button>
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
                    {isDone ? '✓' : SECTION_ICONS[gi]}
                  </div>
                  <span className="patient-step-label">{group.title}</span>
                </div>
              )
            })}
          </div>

          <div className="patient-section visible" ref={el => sectionRefs.current[formStep] = el}>
            <h4 className="patient-section-title">
              {SECTION_ICONS[formStep]} {visibleGroup.title}
            </h4>
            <div className="patient-fields-grid">
              {visibleGroup.fields.filter(f => !f.condition || f.condition(patientInfo)).map((f) => {
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
                          onChange={e => onFieldChange(f.key, e.target.value)}
                          disabled={isSending}
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
                          onChange={e => onFieldChange(f.key, e.target.value)}
                          onKeyDown={e => {
                            if (e.key === 'Enter') {
                              const inputs = document.querySelectorAll('.patient-section.visible input, .patient-section.visible select')
                              const current = Array.from(inputs).indexOf(e.target as HTMLElement)
                              const next = inputs[current + 1] as HTMLElement
                              if (next) next.focus()
                            }
                          }}
                          disabled={isSending}
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
                onClick={onSubmit}
                disabled={isSending}
              >
                {isSending ? 'Guardando...' : '✓ Finalizar y comenzar consulta'}
              </button>
            </div>
          )}
        </div>

        <div ref={endRef} />
      </div>
    </div>
  )
}