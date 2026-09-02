type Props = {
  user: { name?: string } | null
  onLogout: () => void
  reportHtml: string
  onBack: () => void
  onReset: () => void
}

export default function ReportPhase({ user, onLogout, reportHtml, onBack, onReset }: Props) {
  return (
    <div className="app">
      <header className="header">
        <h1>Historia Clínica</h1>
        <span className="subtitle">Mimetic AI - Reporte generado</span>
        <div className="header-right">
          <span className="user-badge">{user?.name}</span>
          <button className="logout-btn" onClick={onLogout}>Cerrar sesión</button>
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
        <button onClick={onBack}>
          Volver al diagnóstico
        </button>
        <button onClick={onReset}>
          Nueva consulta
        </button>
      </div>
    </div>
  )
}