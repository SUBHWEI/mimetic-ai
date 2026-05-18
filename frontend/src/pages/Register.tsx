import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { user, register } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to="/" replace />

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await register(email, name, password)
    } catch (err: any) {
      setError(err.message)
    }
    setSubmitting(false)
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Mimetic AI</h1>
          <p>Sistema de apoyo al diagnóstico médico</p>
        </div>
        <form onSubmit={handleSubmit}>
          <h2>Registro de paciente</h2>
          <p className="auth-hint">Crea tu cuenta para consultar tus diagnósticos e historias clínicas</p>
          {error && <div className="auth-error">{error}</div>}
          <div className="auth-field">
            <label>Nombre completo</label>
            <input
              type="text"
              placeholder="Ej: Juan Pérez"
              value={name}
              onChange={e => setName(e.target.value)}
              required
            />
          </div>
          <div className="auth-field">
            <label>Correo electrónico</label>
            <input
              type="email"
              placeholder="paciente@correo.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="auth-field">
            <label>Contraseña</label>
            <input
              type="password"
              placeholder="Mínimo 6 caracteres"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>
          <button type="submit" className="auth-btn" disabled={submitting}>
            {submitting ? 'Creando cuenta...' : 'Crear cuenta'}
          </button>
        </form>
        <p className="auth-footer">
          ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
        </p>
        <p className="auth-footer">
          ¿Eres personal del hospital? Solicita tu cuenta al administrador
        </p>
      </div>
    </div>
  )
}
