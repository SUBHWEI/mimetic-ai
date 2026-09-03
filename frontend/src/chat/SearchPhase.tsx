import { type RefObject } from 'react'
import type { SearchResult } from '../chat/types'

type Props = {
  user: { name?: string } | null
  onLogout: () => void
  searchRef: RefObject<HTMLInputElement>
  searchQuery: string
  searching: boolean
  showSearchResults: boolean
  searchResults: SearchResult[]
  onSearchChange: (value: string) => void
  onFocusResults: () => void
  onBlurResults: () => void
  onSelect: (result: SearchResult) => void
  onNewPatient: () => void
}

export default function SearchPhase({
  user, onLogout, searchRef, searchQuery, searching, showSearchResults,
  searchResults, onSearchChange, onFocusResults, onBlurResults, onSelect, onNewPatient,
}: Props) {
  return (
    <div className="app">
      <header className="header">
        <img src="/logo.png" alt="Mimetic AI" className="header-logo-lg" />
        <span className="subtitle">Buscar paciente</span>
        <div className="header-right">
          <span className="user-badge">{user?.name}</span>
          <button className="logout-btn" onClick={onLogout}>Cerrar sesión</button>
        </div>
      </header>

      <div className="chat">
        <div className="search-section">
          <h3>Buscar paciente por número de documento</h3>
          <p className="search-hint">Escribe el número de documento para buscar coincidencias</p>

          <div className="search-input-wrap">
            <input
              ref={searchRef}
              type="text"
              className="search-input"
              placeholder="Ingrese el documento de identidad"
              value={searchQuery}
              onChange={e => onSearchChange(e.target.value)}
              onFocus={onFocusResults}
              onBlur={onBlurResults}
            />
            {searching && <span className="search-spinner" />}
          </div>

          {showSearchResults && searchResults.length > 0 && (
            <div className="search-results">
              {searchResults.map((r) => (
                <div
                  key={r.document_number}
                  className="search-result-item"
                  onMouseDown={() => onSelect(r)}
                >
                  <div className="search-result-info">
                    <span className="search-result-name">
                      {r.first_name} {r.last_name}
                    </span>
                    <span className="search-result-doc">{r.document_number}</span>
                  </div>
                  <div className="search-result-badges">
                    {r.has_clinical_history && <span className="badge badge-history">Historia Clínica</span>}
                    {r.has_user_account && <span className="badge badge-user">Cuenta Pública</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {showSearchResults && searchResults.length === 0 && searchQuery.length >= 1 && !searching && (
            <div className="search-no-results">
              <p>No se encontraron pacientes con ese documento.</p>
            </div>
          )}

          <div className="search-no-results" style={{ paddingTop: searchQuery ? '0.5rem' : '1rem' }}>
            <button className="patient-submit" onClick={onNewPatient}>
              + Registrar nuevo paciente
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}