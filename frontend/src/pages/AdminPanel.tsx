import { useAuth } from '../context/AuthContext'

export default function AdminPanel() {
  const { user, logout } = useAuth()

  return (
    <div className="app">
      <header className="header">
        <h1><img src="/logo.png" alt="" className="header-logo" />Mimetic AI</h1>
        <span className="subtitle">Panel de Administración</span>
        <div className="header-right">
          <span className="user-badge">{user?.name}</span>
          <button className="logout-btn" onClick={logout}>Cerrar sesión</button>
        </div>
      </header>

      <div className="placeholder-content">
        <div className="placeholder-icon">⚙️</div>
        <h2>Panel de Administración</h2>
        <p>Gestiona los usuarios del hospital, roles y configuración del sistema.</p>
        <div className="placeholder-cards">
          <div className="placeholder-card">
            <h3>Gestión de Usuarios</h3>
            <p>Crea y administra médicos, enfermeros y personal del hospital</p>
          </div>
          <div className="placeholder-card">
            <h3>Configuración</h3>
            <p>Ajustes generales del sistema</p>
          </div>
        </div>
        <p className="placeholder-note">Estas funciones estarán disponibles próximamente.</p>
      </div>
    </div>
  )
}
