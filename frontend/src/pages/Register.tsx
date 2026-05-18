import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const API = import.meta.env.VITE_API_URL || ''

export default function Register() {
  const { user } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [step, setStep] = useState<'form' | 'verify'>('form')
  const [code, setCode] = useState('')
  const [verifying, setVerifying] = useState(false)

  if (user) return <Navigate to="/" replace />

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const res = await fetch(API + '/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name, password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Registration failed')
      setStep('verify')
    } catch (err: any) {
      setError(err.message)
    }
    setSubmitting(false)
  }

  const handleVerify = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setVerifying(true)
    try {
      const res = await fetch(API + '/api/auth/verify-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Verification failed')
      localStorage.setItem('token', data.access_token)
      window.location.href = '/'
    } catch (err: any) {
      setError(err.message)
    }
    setVerifying(false)
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Mimetic AI</h1>
          <p>Sistema de apoyo al diagnóstico médico</p>
        </div>

        {step === 'form' ? (
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
              {submitting ? 'Enviando...' : 'Crear cuenta'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerify}>
            <h2>Verifica tu correo</h2>
            <p className="auth-hint">
              Hemos enviado un código de verificación a <strong>{email}</strong>
            </p>
            {error && <div className="auth-error">{error}</div>}
            <div className="auth-field">
              <label>Código de verificación</label>
              <input
                type="text"
                placeholder="Ingresa el código de 6 dígitos"
                value={code}
                onChange={e => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                required
                maxLength={6}
              />
            </div>
            <button type="submit" className="auth-btn" disabled={verifying || code.length !== 6}>
              {verifying ? 'Verificando...' : 'Verificar'}
            </button>
          </form>
        )}

        <p className="auth-footer">
          ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
        </p>
        {step === 'form' && (
          <p className="auth-footer">
            ¿Eres personal del hospital? Solicita tu cuenta al administrador
          </p>
        )}
      </div>
    </div>
  )
}
