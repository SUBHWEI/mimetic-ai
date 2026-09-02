from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
import html as html_lib
from app.expert_system.engine import diagnose, get_treatment, recommend_treatment
from app.database.mongodb import get_db
from app.auth.permissions import require_roles
from datetime import datetime

router = APIRouter()


class ReportRequest(BaseModel):
    patient_info: dict
    symptoms: list[str]
    selected_diagnosis: str | None = None
    doctor_review: dict | None = None
    session_id: Optional[str] = None
    document_number: Optional[str] = None


class ReportResponse(BaseModel):
    report: str
    html_report: str
    has_treatment: bool = False
    treatment: dict | None = None


# Helper: escape user-provided value before inserting into HTML (prevents XSS)
def esc(value):
    if value is None:
        return ""
    return html_lib.escape(str(value), quote=True)


# Helper: checkmark for boolean-style fields (escaped for HTML)
def val(pi, key, default=""):
    v = pi.get(key, "")
    return esc(v) if v else esc(default)


# Helper: raw value without HTML escaping (for plain-text output)
def raw_val(pi, key, default=""):
    v = pi.get(key, "")
    return v if v else default


def section(title, content):
    return f"<h2>{esc(title)}</h2>\n{content}" if content.strip() else ""


def field_row(label, value):
    return f"<tr><td class='label'>{esc(label)}</td><td class='value'>{value}</td></tr>" if value else ""


@router.post("/report", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    current_user=Depends(require_roles("medico", "admin", "super_admin")),
):
    pi = request.patient_info
    dr = request.doctor_review or {}
    confirmed_diags = dr.get("confirmedDiagnoses", [])
    manual_diags = dr.get("manualDiagnoses", [])
    selected_medicines = dr.get("selectedMedicines", [])
    modified_doses = dr.get("modifiedDoses", {})
    doctor_notes = dr.get("doctorNotes", "")
    now = datetime.now()
    date_str = now.strftime("%d / %m / %Y")
    time_str = now.strftime("%I:%M %p")
    hour_start_raw = pi.get("consultation_start", time_str)
    hour_start = esc(hour_start_raw)
    hour_end = time_str

    results = await diagnose(request.symptoms) if request.symptoms else []
    tx = None
    if request.selected_diagnosis:
        tx = await recommend_treatment(request.selected_diagnosis, request.patient_info)
        if not tx or not tx.get("available"):
            tx = await get_treatment(request.selected_diagnosis)

    # ── 1. Información General y Control de Tiempo ──
    info_general = f"""
    <table class='info-table'>
        {field_row("Fecha de la Consulta", date_str)}
        {field_row("Hora de Inicio", hour_start)}
        {field_row("Hora de Cierre", hour_end)}
    </table>"""

    # ── 2. Identificación del Paciente ──
    doc_type = val(pi, "document_type", "CC")
    doc_num = val(pi, "id_document")
    doc_full = f"{doc_type} N° {doc_num}" if doc_num else ""
    gender = val(pi, "gender")
    gender_map = {"m": "Masculino", "f": "Femenino", "otro": "Otro"}
    gender_display = gender_map.get(gender.lower(), gender) if gender else ""

    id_paciente = f"""
    <table class='info-table'>
        {field_row("Nombre Completo", val(pi, "name"))}
        {field_row("Documento de Identidad", doc_full)}
        {field_row("Fecha de Nacimiento", val(pi, "birth_date"))}
        {field_row("Edad", val(pi, "age") + " años" if val(pi, "age") else "")}
        {field_row("Género", gender_display)}
        {field_row("Ocupación", val(pi, "occupation"))}
        {field_row("Teléfono", val(pi, "phone"))}
        {field_row("Ciudad de Residencia", val(pi, "location"))}
    </table>"""

    # ── 3. Anamnesis (Motivo de Consulta y Síntomas) ──
    symptoms_list = "".join(f"<li>{esc(s)}</li>" for s in request.symptoms) if request.symptoms else "<li class='none'>No reportados</li>"
    anamnesis = f"""
    <table class='info-table'>
        {field_row("Motivo de Consulta", val(pi, "consultation_reason"))}
        {field_row("Tiempo de Evolución", val(pi, "symptom_evolution"))}
    </table>
    <h3>Síntomas Reportados</h3>
    <ul>{symptoms_list}</ul>"""

    # ── 4. Antecedentes Personales ──
    def si_no(v):
        if not v:
            return ""
        v_lower = v.lower()
        if v_lower in ("si", "sí", "true", "activo"):
            return f"<span class='tag-yes'>Sí</span>"
        if v_lower in ("no", "false", "ninguno", "ninguna", "sedentario", "n/a"):
            return f"<span class='tag-no'>No</span>"
        return v

    antecedentes = f"""
    <table class='info-table'>
        {field_row("Consumo de Tabaco", si_no(val(pi, "tobacco")))}
        {field_row("Consumo de Alcohol", si_no(val(pi, "alcohol")))}
        {field_row("Uso de Sustancias", si_no(val(pi, "substances")))}
        {field_row("Actividad Física", si_no(val(pi, "physical_activity")))}
        {field_row("Embarazo", si_no(val(pi, "pregnancy")))}
    </table>
    <h3>Antecedentes Clínicos</h3>
    <table class='info-table'>
        {field_row("Médicos / Patológicos", val(pi, "medical_history"))}
        {field_row("Quirúrgicos", val(pi, "surgical_history"))}
        {field_row("Farmacológicos", val(pi, "pharmacological_history"))}
        {field_row("Alergias Conocidas", val(pi, "allergies"))}
    </table>"""

    # ── 5. Examen Físico y Signos Vitales ──
    signos = f"""
    <table class='info-table'>
        {field_row("Presión Arterial (PA)", val(pi, "blood_pressure") + " mmHg" if val(pi, "blood_pressure") else "")}
        {field_row("Frecuencia Cardíaca (FC)", val(pi, "heart_rate") + " lpm" if val(pi, "heart_rate") else "")}
        {field_row("Frecuencia Respiratoria (FR)", val(pi, "respiratory_rate") + " rpm" if val(pi, "respiratory_rate") else "")}
        {field_row("Temperatura", val(pi, "temperature") + " °C" if val(pi, "temperature") else "")}
        {field_row("Peso", val(pi, "weight") + " kg" if val(pi, "weight") else "")}
        {field_row("Estatura", val(pi, "height") + " cm" if val(pi, "height") else "")}
    </table>"""

    # ── 6. Diagnósticos Diferenciales ──
    if confirmed_diags or manual_diags:
        confirmed_rows = "".join(
            f"<tr><td>{esc(name)}</td><td>Confirmado</td><td>—</td></tr>"
            for name in confirmed_diags
        )
        manual_rows = "".join(
            f"<tr><td>{esc(d.get('disease_name', ''))}</td><td>Manual del médico</td><td>{esc(d.get('notes', ''))}</td></tr>"
            for d in manual_diags
        )
        diagnosticos = f"""
        <h3>Diagnósticos Confirmados por el Médico</h3>
        <table class='info-table'>
            <tr class='header-row'><th>Enfermedad</th><th>Origen</th><th>Notas</th></tr>
            {confirmed_rows}
            {manual_rows}
        </table>"""
        if results:
            diff_rows = "".join(
                f"<tr><td>{esc(d['disease_name'])}</td><td>{esc(d.get('severity', ''))}</td>"
                f"<td>{d['confidence']:.0%}</td><td>{esc(d.get('description', ''))[:80]}</td></tr>"
                for d in results if d['disease_name'] not in confirmed_diags
            )
            if diff_rows:
                diagnosticos += f"""
        <h3>Diagnósticos Diferenciales Sugeridos por la IA</h3>
        <table class='info-table'>
            <tr class='header-row'><th>Enfermedad</th><th>Severidad</th><th>Confianza</th><th>Descripción</th></tr>
            {diff_rows}
        </table>"""
    elif results:
        diag_rows = "".join(
            f"<tr><td>{esc(d['disease_name'])}</td><td>{esc(d.get('severity', ''))}</td>"
            f"<td>{d['confidence']:.0%}</td><td>{esc(d.get('description', ''))[:80]}</td></tr>"
            for d in results
        )
        diagnosticos = f"""
        <table class='info-table'>
            <tr class='header-row'><th>Enfermedad</th><th>Severidad</th><th>Confianza</th><th>Descripción</th></tr>
            {diag_rows}
        </table>"""
    else:
        diagnosticos = "<p class='none'>No se realizaron diagnósticos diferenciales.</p>"

    # ── 7. Receta Médica ──
    has_tx = False
    receta = ""
    if tx:
        has_tx = True
        is_new = "available" in tx
        diag_confirmado = tx.get("disease_name", "")
        receta += f"""
        <p><strong>Diagnóstico confirmado:</strong> {esc(diag_confirmado)}</p>"""

        def _med_row(m):
            name = m.get("name", "")
            dose_key = f"{name}"
            dosage = modified_doses.get(dose_key) or m.get("dosage", "")
            freq = m.get("frequency", "")
            duration = m.get("duration", "")
            via = m.get("route", "Oral")
            monitoring = m.get("monitoring", "")
            summary = m.get("patient_summary", "")
            summary_html = f"<div class='summary-note'>{esc(summary)}</div>" if summary else ""
            modified_tag = f'<div style="color:#991b1b;font-size:7.5pt;font-style:italic;">Dosis ajustada por médico: {esc(dosage)}</div>' if dose_key in modified_doses else ""
            return f"""
                <tr>
                    <td>{esc(name)}{summary_html}</td>
                    <td>{esc(dosage)}{modified_tag}</td>
                    <td><span class='tag'>{esc(via)}</span></td>
                    <td>{esc(freq)}</td>
                    <td>{esc(duration)}</td>
                    <td>{esc(monitoring)}</td>
                </tr>"""

        def _med_notes(m):
            notes = ""
            contra = m.get("contraindications", {})
            if contra:
                items = []
                if contra.get("allergies"):
                    items.append("Alergias: " + ", ".join(esc(a) for a in contra["allergies"]))
                if contra.get("conditions"):
                    items.append("Contraindicado en: " + ", ".join(esc(c) for c in contra["conditions"]))
                if items:
                    notes += f"""<tr><td colspan="6" class="contra-block">{" | ".join(items)}</td></tr>"""
            adj = m.get("adjustments", {})
            if adj:
                adj_items = []
                for key in ("renal", "hepatic", "pediatric", "geriatric", "pregnancy"):
                    v = adj.get(key)
                    if v:
                        adj_items.append(f"<strong>{esc(key.capitalize())}:</strong> {esc(v)}")
                if adj_items:
                    notes += f"""<tr><td colspan="6" class="contra-block">{" | ".join(adj_items)}</td></tr>"""
            int_warn = m.get("interactions_warning")
            if int_warn:
                notes += f"""<tr><td colspan="6" class="warning-block">ADVERTENCIA: {esc(int_warn)}</td></tr>"""
            return notes

        if is_new:
            meds = tx.get("available", [])
            not_rec = tx.get("not_recommended", [])
            alt_meds = tx.get("alternatives", [])
            non_pharm = tx.get("non_pharmacological", [])
        else:
            meds = tx.get("medicines", [])
            not_rec = []
            alt_meds = tx.get("alternative_medicines", [])
            non_pharm = tx.get("non_pharmacological_treatments", [])

        # If the doctor selected specific medicines, honor that selection
        if selected_medicines:
            def _keep(m):
                return m.get("name") in selected_medicines
            meds = [m for m in meds if _keep(m)]
            alt_meds = [m for m in alt_meds if _keep(m)]

        if meds or not_rec:
            receta += """
        <h3>Medicamentos Prescritos</h3>
        <table class='info-table'>
            <tr class='header-row'><th>Medicamento</th><th>Concentración</th><th>Vía</th><th>Frecuencia</th><th>Duración</th><th>Monitoreo</th></tr>"""
            for m in meds:
                receta += _med_row(m)
                receta += _med_notes(m)
            for m in not_rec:
                receta += _med_row(m)
                receta += _med_notes(m)
            receta += "</table>"
        else:
            receta += "<p class='none'>No requiere medicamentos.</p>"

        if alt_meds:
            receta += """
        <h3>Medicamentos Alternativos</h3>
        <table class='info-table'>
            <tr class='header-row'><th>Medicamento</th><th>Concentración</th><th>Vía</th><th>Frecuencia</th><th>Duración</th><th>Monitoreo</th></tr>"""
            for m in alt_meds:
                receta += _med_row(m)
                receta += _med_notes(m)
            receta += "</table>"

        if non_pharm:
            bullets = "".join(f"<li>{esc(t)}</li>" for t in non_pharm if isinstance(t, str))
            receta += f"""
        <h3>Tratamientos No Farmacológicos</h3>
        <ul>{bullets}</ul>"""

    # ── 8. Recomendaciones Médicas ──
    recomendaciones = ""
    if tx and tx.get("general_recommendations"):
        recs = tx["general_recommendations"]
        # Split by period or newline into bullet points
        bullets = "".join(f"<li>{esc(r.strip())}</li>" for r in recs.split(".") if r.strip())
        recomendaciones = f"<ul>{bullets}</ul>"

    # ── 9. Notas del Médico ──
    notas_medico = ""
    if doctor_notes:
        notas_medico = f"<p>{esc(doctor_notes)}</p>"

    # ── Build Full HTML ──
    html_report = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Historia Clínica - MIMETIC</title>
<style>
  @page {{ size: letter; margin: 15mm; }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', 'Calibri', Arial, sans-serif;
    max-width: 210mm; margin: 0 auto; padding: 15px;
    background: #fff; color: #1e293b;
    font-size: 10pt; line-height: 1.5;
  }}
  .header {{
    text-align: center; margin-bottom: 16px;
    border-bottom: 3px solid #1e3a5f; padding-bottom: 10px;
  }}
  .header h1 {{ font-size: 16pt; color: #1e3a5f; margin: 0; }}
  .header p {{ font-size: 8pt; color: #64748b; margin: 2px 0; }}
  h2 {{
    font-size: 12pt; color: #1e3a5f; margin: 14px 0 6px;
    border-bottom: 1px solid #cbd5e1; padding-bottom: 3px;
  }}
  h3 {{ font-size: 10pt; color: #334155; margin: 10px 0 4px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 4px 0; }}
  td, th {{ padding: 3px 6px; border: 1px solid #e2e8f0; font-size: 9pt; }}
  td.label {{ width: 180px; font-weight: 600; color: #475569; background: #f8fafc; }}
  td.value {{ color: #1e293b; }}
  tr.header-row th {{ background: #1e3a5f; color: #fff; font-weight: 600; text-align: left; }}
  ul {{ margin: 4px 0; padding-left: 20px; }}
  li {{ margin: 1px 0; }}
  li.none, p.none {{ color: #94a3b8; font-style: italic; }}
  .tag {{
    display: inline-block; padding: 1px 6px; border-radius: 3px;
    font-size: 8pt; font-weight: 600;
    background: #e2e8f0; color: #334155;
  }}
  .tag-yes {{ background: #dcfce7; color: #166534; padding: 1px 6px; border-radius: 3px; font-size: 8pt; font-weight: 600; }}
  .tag-no {{ background: #fee2e2; color: #991b1b; padding: 1px 6px; border-radius: 3px; font-size: 8pt; font-weight: 600; }}
  .contra-block {{ background: #fff3cd; color: #856404; padding: 2px 8px; font-size: 8.5pt; border-left: 3px solid #ffc107; }}
  .warning-block {{ background: #f8d7da; color: #721c24; padding: 2px 8px; font-size: 8.5pt; border-left: 3px solid #dc3545; }}
  .monitoring-block {{ background: #d1ecf1; color: #0c5460; padding: 2px 8px; font-size: 8.5pt; border-left: 3px solid #17a2b8; }}
  .summary-note {{ color: #166534; font-style: italic; font-size: 8pt; margin-top: 2px; }}
  .footer {{
    margin-top: 20px; border-top: 1px solid #cbd5e1; padding-top: 8px;
    font-size: 7.5pt; color: #94a3b8; text-align: center;
  }}
  .section-num {{ font-weight: 700; color: #1e3a5f; }}
  @media print {{
    body {{ padding: 0; }}
    .no-print {{ display: none; }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>MIMETIC — Historia Clínica</h1>
  <p>Sistema de Apoyo al Diagnóstico Médico</p>
  <p>Reporte generado: {date_str} {time_str}</p>
</div>

<section>
<h2>1. Información General y Control de Tiempo</h2>
{info_general}
</section>

<section>
<h2>2. Identificación del Paciente</h2>
{id_paciente}
</section>

<section>
<h2>3. Anamnesis (Motivo de Consulta y Síntomas)</h2>
{anamnesis}
</section>

<section>
<h2>4. Antecedentes Personales</h2>
{antecedentes}
</section>

<section>
<h2>5. Examen Físico y Signos Vitales</h2>
{signos}
</section>

<section>
<h2>6. Diagnósticos Diferenciales</h2>
{diagnosticos}
</section>

<section>
<h2>7. Receta Médica (Plan Farmacológico)</h2>
{receta}
</section>

<section>
<h2>8. Recomendaciones Médicas e Indicaciones No Farmacológicas</h2>
{recomendaciones if recomendaciones else "<p class='none'>No se registraron recomendaciones adicionales.</p>"}
</section>

{'''
<section>
<h2>9. Observaciones del Médico</h2>
''' + (notas_medico if notas_medico else "<p class='none'>Sin observaciones registradas por el médico.</p>") + '''
</section>
''' if doctor_notes else ''}

<div class="footer">
  <p>Este reporte es generado por MIMETIC como herramienta de apoyo al diagnóstico.</p>
  <p>No sustituye el criterio de un profesional de la salud. Ley 23 de 1981 — Colombia.</p>
</div>

</body>
</html>"""

    # Plain text (uses raw, unescaped values)
    text_doc_type = raw_val(pi, "document_type", "CC")
    text_doc_num = raw_val(pi, "id_document")
    text_doc_full = f"{text_doc_type} N° {text_doc_num}" if text_doc_num else ""
    text_gender = raw_val(pi, "gender")
    text_gender_display = gender_map.get(text_gender.lower(), text_gender) if text_gender else ""

    text = f"""=== HISTORIA CLÍNICA ===
MIMETIC - Sistema de Apoyo al Diagnóstico Médico
Fecha: {date_str} - {time_str}

--- 1. Información General ---
Fecha: {date_str} | Inicio: {hour_start_raw} | Cierre: {hour_end}

--- 2. Identificación del Paciente ---
Nombre: {raw_val(pi, "name")}
Documento: {text_doc_full}
Edad: {raw_val(pi, "age")} | Género: {text_gender_display}
Ocupación: {raw_val(pi, "occupation")} | Teléfono: {raw_val(pi, "phone")}
Ciudad: {raw_val(pi, "location")}

--- 3. Anamnesis ---
Motivo: {raw_val(pi, "consultation_reason")}
Evolución: {raw_val(pi, "symptom_evolution")}
Síntomas: {', '.join(request.symptoms) if request.symptoms else 'No reportados'}

--- 4. Antecedentes ---
Tabaco: {raw_val(pi, "tobacco")} | Alcohol: {raw_val(pi, "alcohol")}
Sustancias: {raw_val(pi, "substances")} | Actividad: {raw_val(pi, "physical_activity")}
Médicos: {raw_val(pi, "medical_history")}
Quirúrgicos: {raw_val(pi, "surgical_history")}
Farmacológicos: {raw_val(pi, "pharmacological_history")}
Alergias: {raw_val(pi, "allergies")}

--- 5. Signos Vitales ---
PA: {raw_val(pi, "blood_pressure")} | FC: {raw_val(pi, "heart_rate")} | FR: {raw_val(pi, "respiratory_rate")}
Temp: {raw_val(pi, "temperature")} | Peso: {raw_val(pi, "weight")} | Estatura: {raw_val(pi, "height")}

--- 6. Diagnósticos ---
"""

    if results:
        for d in results:
            text += f"- {d['disease_name']} ({d['confidence']:.0%}) - {d.get('severity', '')}\n"

    if tx:
        text += f"\n--- 7. Receta Médica ---\nDiagnóstico: {tx.get('disease_name', '')}\n"
        meds_list = tx.get("available", tx.get("medicines", []))
        for m in meds_list:
            text += f"{m['name']} - {m.get('dosage', '')} - {m.get('frequency', '')} - {m.get('duration', '')}\n"
        alt_list = tx.get("alternatives", tx.get("alternative_medicines", []))
        if alt_list:
            text += "\nAlternativos:\n"
            for m in alt_list:
                text += f"{m['name']} - {m.get('dosage', '')} - {m.get('frequency', '')} - {m.get('duration', '')}\n"
        if tx.get("general_recommendations"):
            text += f"\n--- 8. Recomendaciones ---\n{tx['general_recommendations']}\n"

    if doctor_notes:
        text += f"\n--- 9. Observaciones del Médico ---\n{doctor_notes}\n"

    text += "\n=== Fin del Reporte ==="

    # Persist session data if session_id and document_number provided
    if request.session_id and request.document_number:
        db = get_db()
        if db is not None:
            update = {"symptoms": request.symptoms}
            if dr:
                update["doctor_review"] = dr
            if results:
                update["diagnoses"] = results
            if tx:
                update["treatment"] = tx
            if html_report:
                update["report_html"] = html_report

            try:
                await db.sessions.update_one(
                    {"_id": ObjectId(request.session_id), "document_number": request.document_number},
                    {"$set": update},
                )
                await db.clinical_histories.update_one(
                    {"document_number": request.document_number},
                    {"$set": {"updated_at": datetime.utcnow()}},
                )
            except Exception:
                pass  # Non-critical: report still returns

    return ReportResponse(
        report=text,
        html_report=html_report,
        has_treatment=has_tx,
        treatment=tx,
    )
