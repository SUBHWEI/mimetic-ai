import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import Login from './pages/Login'
import Register from './pages/Register'
import ChatApp from './ChatApp'
import PatientDashboard from './pages/PatientDashboard'
import AdminPanel from './pages/AdminPanel'

const GOOGLE_CLIENT_ID = '736518024017-67rrlj9a6smuvon5ppcne06vbq07g13c.apps.googleusercontent.com'

function RoleRedirect() {
  const { user } = useAuth()
  if (user?.role === 'paciente') return <Navigate to="/paciente" replace />
  if (user?.role === 'admin') return <Navigate to="/admin" replace />
  return <ChatApp />
}

export default function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <RoleRedirect />
                </ProtectedRoute>
              }
            />
            <Route
              path="/paciente"
              element={
                <ProtectedRoute requiredRole="paciente">
                  <PatientDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AdminPanel />
                </ProtectedRoute>
              }
            />
            <Route
              path="/chat"
              element={
                <ProtectedRoute requiredRole="medico">
                  <ChatApp />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </GoogleOAuthProvider>
  )
}
