import { useChatApp } from './chat/useChatApp'
import SearchPhase from './chat/SearchPhase'
import PatientInfoPhase from './chat/PatientInfoPhase'
import ReportPhase from './chat/ReportPhase'
import SymptomsPhase from './chat/SymptomsPhase'
import './App.css'

export default function ChatApp() {
  const app = useChatApp()

  if (app.phase === 'search') {
    return (
      <SearchPhase
        user={app.user}
        onLogout={app.logout}
        searchRef={app.searchRef}
        searchQuery={app.searchQuery}
        searching={app.searching}
        showSearchResults={app.showSearchResults}
        searchResults={app.searchResults}
        onSearchChange={app.handleSearchChange}
        onFocusResults={() => app.searchResults.length > 0 && app.setShowSearchResults(true)}
        onBlurResults={() => setTimeout(() => app.setShowSearchResults(false), 200)}
        onSelect={app.selectPatient}
        onNewPatient={app.startNewPatient}
      />
    )
  }

  if (app.phase === 'patient_info') {
    return (
      <PatientInfoPhase
        user={app.user}
        onLogout={app.logout}
        patientInfoMode={app.patientInfoMode}
        patientInfo={app.patientInfo}
        formStep={app.formStep}
        setFormStep={app.setFormStep}
        fieldGroups={app.fieldGroups}
        allFieldKeys={app.allFieldKeys}
        sessionFieldKeys={app.sessionFieldKeys}
        sectionRefs={app.sectionRefs}
        messages={app.messages}
        endRef={app.endRef}
        isSending={app.isSending}
        onFieldChange={app.handlePatientFieldChange}
        onSubmit={app.submitPatientForm}
      />
    )
  }

  if (app.phase === 'report' && app.reportHtml) {
    return (
      <ReportPhase
        user={app.user}
        onLogout={app.logout}
        reportHtml={app.reportHtml}
        onBack={app.backToSymptoms}
        onReset={app.resetAll}
      />
    )
  }

  return (
    <SymptomsPhase
      user={app.user}
      onLogout={app.logout}
      patientInfo={app.patientInfo}
      messages={app.messages}
      input={app.input}
      setInput={app.setInput}
      isSending={app.isSending}
      isGeneratingReport={app.isGeneratingReport}
      currentSymptoms={app.currentSymptoms}
      suggestedSymptoms={app.suggestedSymptoms}
      selectedDiagnosis={app.selectedDiagnosis}
      doctorReview={app.doctorReview}
      endRef={app.endRef}
      onSend={app.handleSend}
      onSuggestion={app.handleSuggestion}
      onSelectDiagnosis={app.handleSelectDiagnosis}
      onGenerateReport={app.generateReport}
      onToggleDiagnosisConfirmation={app.toggleDiagnosisConfirmation}
      onToggleDiagnosisRejection={app.toggleDiagnosisRejection}
      onAddManualDiagnosis={app.addManualDiagnosis}
      onRemoveManualDiagnosis={app.removeManualDiagnosis}
      onToggleMedicine={app.toggleMedicineSelection}
      onUpdateDose={app.updateMedicineDose}
      onSetDoctorNotes={app.setDoctorNotes}
      confidenceColor={app.confidenceColor}
      severityColor={app.severityColor}
    />
  )
}