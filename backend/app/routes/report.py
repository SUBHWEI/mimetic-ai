from fastapi import APIRouter
from pydantic import BaseModel
from app.expert_system.engine import diagnose, get_treatment
from datetime import datetime

router = APIRouter()


class ReportRequest(BaseModel):
    patient_info: dict
    symptoms: list[str]
    selected_diagnosis: str | None = None


class ReportResponse(BaseModel):
    report: str
    html_report: str
    has_treatment: bool = False
    treatment: dict | None = None


# Helper: checkmark for boolean-style fields
def val(pi, key, default=""):
    v = pi.get(key, "")
    return v if v else default


def section(title, content):
    return f"<h2>{title}</h2>\n{content}" if content.strip() else ""


def field_row(label, value):
    return f"<tr><td class='label'>{label}</td><td class='value'>{value}</td></tr>" if value else ""


@router.post("/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    pi = request.patient_info
    now = datetime.now()
    date_str = now.strftime("%d / %m / %Y")
    time_str = now.strftime("%I:%M %p")
    hour_start = pi.get("consultation_start", time_str)
    hour_end = time_str

    results = await diagnose(request.symptoms) if request.symptoms else []
    tx = None
    if request.selected_diagnosis:
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
    symptoms_list = "".join(f"<li>{s}</li>" for s in request.symptoms) if request.symptoms else "<li class='none'>No reportados</li>"
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
        if v_lower in ("si", "sí", "activo"):
            return f"<span class='tag-yes'>Sí</span>"
        if v_lower in ("no", "ninguno", "ninguna", "sedentario", "n/a"):
            return f"<span class='tag-no'>No</span>"
        return v

    antecedentes = f"""
    <table class='info-table'>
        {field_row("Consumo de Tabaco", si_no(val(pi, "tobacco")))}
        {field_row("Consumo de Alcohol", si_no(val(pi, "alcohol")))}
        {field_row("Uso de Sustancias", si_no(val(pi, "substances")))}
        {field_row("Actividad Física", si_no(val(pi, "physical_activity")))}
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
    if results:
        diag_rows = "".join(
            f"<tr><td>{d['disease_name']}</td><td>{d.get('severity', '')}</td>"
            f"<td>{d['confidence']:.0%}</td><td>{d.get('description', '')[:80]}</td></tr>"
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
        diag_confirmado = tx["disease_name"]
        receta += f"""
        <p><strong>Diagnóstico confirmado:</strong> {diag_confirmado}</p>
        <h3>Medicamentos Prescritos</h3>"""
        meds = tx.get("medicines", [])
        if meds:
            receta += """
            <table class='info-table'>
                <tr class='header-row'><th>Medicamento</th><th>Concentración</th><th>Vía</th><th>Dosis / Frecuencia</th><th>Duración</th></tr>"""
            for m in meds:
                name = m.get("name", "")
                dosage = m.get("dosage", "")
                freq = m.get("frequency", "")
                duration = m.get("duration", "")
                via = m.get("route", "Oral")
                receta += f"""
                <tr>
                    <td>{name}</td>
                    <td>{dosage}</td>
                    <td><span class='tag'>{via}</span></td>
                    <td>{freq}</td>
                    <td>{duration}</td>
                </tr>"""
            receta += "</table>"
        else:
            receta += "<p class='none'>No requiere medicamentos. Seguir recomendaciones generales.</p>"

    # ── 8. Recomendaciones Médicas ──
    recomendaciones = ""
    if tx and tx.get("general_recommendations"):
        recs = tx["general_recommendations"]
        # Split by period or newline into bullet points
        bullets = "".join(f"<li>{r.strip()}</li>" for r in recs.split(".") if r.strip())
        recomendaciones = f"<ul>{bullets}</ul>"

    # ── Build Full HTML ──
    html_report = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Historia Clínica - Mimetic AI</title>
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
  <h1>Mimetic AI — Historia Clínica</h1>
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

<div class="footer">
  <p>Este reporte es generado por Mimetic AI como herramienta de apoyo al diagnóstico.</p>
  <p>No sustituye el criterio de un profesional de la salud. Ley 23 de 1981 — Colombia.</p>
</div>

</body>
</html>"""

    # Plain text
    text = f"""=== HISTORIA CLÍNICA ===
Mimetic AI - Sistema de Apoyo al Diagnóstico Médico
Fecha: {date_str} - {time_str}

--- 1. Información General ---
Fecha: {date_str} | Inicio: {hour_start} | Cierre: {hour_end}

--- 2. Identificación del Paciente ---
Nombre: {val(pi, "name")}
Documento: {doc_full}
Edad: {val(pi, "age")} | Género: {gender_display}
Ocupación: {val(pi, "occupation")} | Teléfono: {val(pi, "phone")}
Ciudad: {val(pi, "location")}

--- 3. Anamnesis ---
Motivo: {val(pi, "consultation_reason")}
Evolución: {val(pi, "symptom_evolution")}
Síntomas: {', '.join(request.symptoms) if request.symptoms else 'No reportados'}

--- 4. Antecedentes ---
Tabaco: {val(pi, "tobacco")} | Alcohol: {val(pi, "alcohol")}
Sustancias: {val(pi, "substances")} | Actividad: {val(pi, "physical_activity")}
Médicos: {val(pi, "medical_history")}
Quirúrgicos: {val(pi, "surgical_history")}
Farmacológicos: {val(pi, "pharmacological_history")}
Alergias: {val(pi, "allergies")}

--- 5. Signos Vitales ---
PA: {val(pi, "blood_pressure")} | FC: {val(pi, "heart_rate")} | FR: {val(pi, "respiratory_rate")}
Temp: {val(pi, "temperature")} | Peso: {val(pi, "weight")} | Estatura: {val(pi, "height")}

--- 6. Diagnósticos ---
"""

    if results:
        for d in results:
            text += f"- {d['disease_name']} ({d['confidence']:.0%}) - {d.get('severity', '')}\n"

    if tx:
        text += f"\n--- 7. Receta Médica ---\nDiagnóstico: {tx['disease_name']}\n"
        for m in tx.get("medicines", []):
            text += f"{m['name']} - {m.get('dosage', '')} - {m.get('frequency', '')} - {m.get('duration', '')}\n"
        if tx.get("general_recommendations"):
            text += f"\n--- 8. Recomendaciones ---\n{tx['general_recommendations']}\n"

    text += "\n=== Fin del Reporte ==="

    return ReportResponse(
        report=text,
        html_report=html_report,
        has_treatment=has_tx,
        treatment=tx,
    )
