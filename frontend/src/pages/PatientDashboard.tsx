import { useAuth } from '../context/AuthContext'

export default function PatientDashboard() {
  const { user, logout } = useAuth()

  return (
    <div className="app">
      <header className="header">
        <h1>Mimetic AI</h1>
        <span className="subtitle">Portal del Paciente</span>
        <div className="header-right">
          <span className="user-badge">{user?.name}</span>
          <button className="logout-btn" onClick={logout}>Cerrar sesión</button>
        </div>
      </header>

      <div className="placeholder-content">
        <div className="placeholder-icon">🩺</div>
        <h2>Bienvenido, {user?.name}</h2>
        <p>Aquí podrás consultar tus diagnósticos, historias clínicas y planes de tratamiento.</p>
        <div className="placeholder-cards">
          <div className="placeholder-card">
            <h3>Diagnósticos</h3>
            <p>Consulta tus diagnósticos anteriores</p>
          </div>
          <div className="placeholder-card">
            <h3>Historia Clínica</h3>
            <p>Descarga tu historia clínica</p>
          </div>
          <div className="placeholder-card">
            <h3>Tratamientos</h3>
            <p>Revisa tus planes de tratamiento</p>
          </div>
        </div>
        <p className="placeholder-note">Estas funciones estarán disponibles próximamente.</p>
      </div>
    </div>
  )
}
