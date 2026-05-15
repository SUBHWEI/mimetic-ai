import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "mimetic_ai"

symptoms = [
    {"name": "fiebre", "description": "Temperatura corporal elevada (>38°C)", "category": "generales"},
    {"name": "tos", "description": "Tos seca o productiva", "category": "respiratorio"},
    {"name": "dolor de cabeza", "description": "Cefalea o dolor craneal", "category": "neurologico"},
    {"name": "fatiga", "description": "Cansancio o debilidad general", "category": "generales"},
    {"name": "dificultad para respirar", "description": "Disnea o falta de aire", "category": "respiratorio"},
    {"name": "dolor de garganta", "description": "odinofagia o dolor faríngeo", "category": "respiratorio"},
    {"name": "congestión nasal", "description": "Nariz tapada o mucosidad", "category": "respiratorio"},
    {"name": "escalofríos", "description": "Sensación de frío con temblores", "category": "generales"},
    {"name": "dolor muscular", "description": "Mialgias o dolores corporales", "category": "musculoesqueletico"},
    {"name": "pérdida del gusto", "description": "Ageusia o pérdida del sentido del gusto", "category": "neurologico"},
    {"name": "pérdida del olfato", "description": "Anosmia o pérdida del olfato", "category": "neurologico"},
    {"name": "náuseas", "description": "Náuseas o ganas de vomitar", "category": "digestivo"},
    {"name": "vómito", "description": "Vómito o emesis", "category": "digestivo"},
    {"name": "diarrea", "description": "Heces sueltas o líquidas frecuentes", "category": "digestivo"},
    {"name": "dolor abdominal", "description": "Dolor en la región del abdomen", "category": "digestivo"},
    {"name": "deshidratación", "description": "Pérdida excesiva de líquidos corporales", "category": "generales"},
    {"name": "sarpullido", "description": "Erupción cutánea o rash", "category": "dermatologico"},
    {"name": "dolor en el pecho", "description": "Dolor torácico", "category": "cardiovascular"},
    {"name": "presión arterial alta", "description": "Hipertensión o PA elevada", "category": "cardiovascular"},
    {"name": "mareos", "description": "Vértigo o sensación de desmayo", "category": "neurologico"},
    {"name": "dolor de oído", "description": "Otalgia o dolor auricular", "category": "otologico"},
    {"name": "secreción del oído", "description": "Otorrea o líquido del oído", "category": "otologico"},
    {"name": "ardor al orinar", "description": "Disuria o dolor miccional", "category": "urinario"},
    {"name": "frecuencia urinaria", "description": "Polaquiuria u orinar con frecuencia", "category": "urinario"},
    {"name": "dolor lumbar", "description": "Dolor en la región baja de la espalda", "category": "musculoesqueletico"},
    {"name": "fiebre alta persistente", "description": "Fiebre >39°C que no cede", "category": "generales"},
    {"name": "confusión", "description": "Estado de confusión o desorientación", "category": "neurologico"},
    {"name": "rigidez de cuello", "description": "Rigidez nucal o cuello tieso", "category": "neurologico"},
    {"name": "dolor articular", "description": "Artralgia o dolor en las articulaciones", "category": "musculoesqueletico"},
    {"name": "hinchazón", "description": "Edema o inflamación de tejidos", "category": "generales"},
    {"name": "ictericia", "description": "Coloración amarillenta de piel/ojos", "category": "digestivo"},
    {"name": "pérdida de apetito", "description": "Anorexia o inapetencia", "category": "digestivo"},
    {"name": "heces con sangre", "description": "Rectorragia o sangre en heces", "category": "digestivo"},
    {"name": "tos con sangre", "description": "Hemoptisis o expectoración con sangre", "category": "respiratorio"},
    {"name": "sudoración nocturna", "description": "Hiperhidrosis nocturna", "category": "generales"},
    {"name": "pérdida de peso", "description": "Pérdida de peso involuntaria", "category": "generales"},
    {"name": "comezón", "description": "Prurito o picazón en la piel", "category": "dermatologico"},
    {"name": "ojos rojos", "description": "Hiperemia conjuntival", "category": "oftalmologico"},
    {"name": "sensibilidad a la luz", "description": "Fotofobia", "category": "neurologico"},
    {"name": "dolor detrás de los ojos", "description": "Dolor retroorbitario", "category": "oftalmologico"},
]

diseases = [
    {
        "name": "Influenza (Gripe)",
        "description": "Infección viral respiratoria aguda causada por el virus de la influenza",
        "symptoms": ["fiebre", "tos", "dolor de cabeza", "fatiga", "dolor de garganta", "congestión nasal", "escalofríos", "dolor muscular"],
        "severity": "moderate",
    },
    {
        "name": "Resfriado Común",
        "description": "Infección viral leve del tracto respiratorio superior",
        "symptoms": ["tos", "dolor de garganta", "congestión nasal", "dolor de cabeza", "fatiga"],
        "severity": "mild",
    },
    {
        "name": "COVID-19",
        "description": "Enfermedad infecciosa causada por el coronavirus SARS-CoV-2",
        "symptoms": ["fiebre", "tos", "fatiga", "pérdida del gusto", "pérdida del olfato", "dolor de cabeza", "dolor de garganta", "dificultad para respirar"],
        "severity": "high",
    },
    {
        "name": "Gastroenteritis Aguda",
        "description": "Inflamación del estómago e intestinos, comúnmente por infección viral o bacteriana",
        "symptoms": ["diarrea", "náuseas", "vómito", "dolor abdominal", "fiebre", "fatiga", "deshidratación"],
        "severity": "moderate",
    },
    {
        "name": "Neumonía",
        "description": "Infección pulmonar que inflama los alvéolos, puede ser bacteriana o viral",
        "symptoms": ["fiebre", "tos", "dificultad para respirar", "dolor en el pecho", "escalofríos", "fatiga"],
        "severity": "high",
    },
    {
        "name": "Otitis Media",
        "description": "Infección del oído medio, común en niños",
        "symptoms": ["dolor de oído", "fiebre", "secreción del oído", "dolor de cabeza"],
        "severity": "moderate",
    },
    {
        "name": "Infección Urinaria",
        "description": "Infección del tracto urinario, generalmente bacteriana",
        "symptoms": ["ardor al orinar", "frecuencia urinaria", "dolor abdominal", "fiebre", "dolor lumbar"],
        "severity": "moderate",
    },
    {
        "name": "Dengue",
        "description": "Enfermedad viral transmitida por mosquitos Aedes",
        "symptoms": ["fiebre alta persistente", "dolor de cabeza", "dolor muscular", "dolor articular", "dolor detrás de los ojos", "sarpullido", "náuseas"],
        "severity": "high",
    },
    {
        "name": "Meningitis",
        "description": "Inflamación de las membranas que recubren el cerebro y la médula espinal",
        "symptoms": ["fiebre", "dolor de cabeza", "rigidez de cuello", "confusión", "náuseas", "vómito", "sensibilidad a la luz"],
        "severity": "critical",
    },
    {
        "name": "Hepatitis A",
        "description": "Infección viral del hígado transmitida por alimentos o agua contaminados",
        "symptoms": ["fatiga", "pérdida de apetito", "ictericia", "dolor abdominal", "náuseas", "fiebre"],
        "severity": "moderate",
    },
    {
        "name": "Bronquitis Aguda",
        "description": "Inflamación de los bronquios, generalmente por infección viral",
        "symptoms": ["tos", "fatiga", "dificultad para respirar", "dolor en el pecho", "fiebre", "dolor de garganta"],
        "severity": "moderate",
    },
    {
        "name": "Amigdalitis",
        "description": "Infección e inflamación de las amígdalas",
        "symptoms": ["dolor de garganta", "fiebre", "dolor de cabeza", "fatiga"],
        "severity": "moderate",
    },
    {
        "name": "Rinitis Alérgica",
        "description": "Reacción alérgica que causa inflamación nasal",
        "symptoms": ["congestión nasal", "estornudos", "ojos rojos", "comezón"],
        "severity": "mild",
    },
    {
        "name": "Intoxicación Alimentaria",
        "description": "Enfermedad causada por consumir alimentos contaminados",
        "symptoms": ["diarrea", "vómito", "dolor abdominal", "náuseas", "fiebre", "deshidratación"],
        "severity": "moderate",
    },
    {
        "name": "Tuberculosis",
        "description": "Infección bacteriana pulmonar grave causada por Mycobacterium tuberculosis",
        "symptoms": ["tos con sangre", "sudoración nocturna", "pérdida de peso", "fiebre", "fatiga", "dolor en el pecho"],
        "severity": "critical",
    },
    {
        "name": "Shigelosis (Disentería)",
        "description": "Infección bacteriana intestinal que causa diarrea con sangre",
        "symptoms": ["diarrea", "heces con sangre", "fiebre", "dolor abdominal", "náuseas", "deshidratación"],
        "severity": "high",
    },
]

treatments = [
    {
        "disease_name": "Influenza (Gripe)",
        "medicines": [
            {"name": "Paracetamol 500mg", "dosage": "500mg", "frequency": "Cada 8 horas", "duration": "5 días"},
            {"name": "Oseltamivir 75mg", "dosage": "75mg", "frequency": "Cada 12 horas", "duration": "5 días"},
            {"name": "Loratadina 10mg", "dosage": "10mg", "frequency": "Cada 24 horas", "duration": "5 días"},
        ],
        "general_recommendations": "Reposo, hidratación abundante, evitar cambios bruscos de temperatura. Acudir a urgencias si hay dificultad para respirar.",
    },
    {
        "disease_name": "Resfriado Común",
        "medicines": [
            {"name": "Paracetamol 500mg", "dosage": "500mg", "frequency": "Cada 8 horas", "duration": "3-5 días"},
            {"name": "Descongestionante nasal (Pseudoefedrina)", "dosage": "30mg", "frequency": "Cada 12 horas", "duration": "3 días"},
            {"name": "Vitamina C 500mg", "dosage": "500mg", "frequency": "Cada 24 horas", "duration": "7 días"},
        ],
        "general_recommendations": "Reposo, hidratación, miel con limón para la garganta. No requiere antibióticos.",
    },
    {
        "disease_name": "COVID-19",
        "medicines": [
            {"name": "Paracetamol 500mg", "dosage": "500mg", "frequency": "Cada 6-8 horas", "duration": "Según síntomas"},
            {"name": "Paxlovid (Nirmatrelvir/Ritonavir)", "dosage": "300mg/100mg", "frequency": "Cada 12 horas", "duration": "5 días"},
            {"name": "Dexametasona 6mg", "dosage": "6mg", "frequency": "Cada 24 horas", "duration": "10 días"},
            {"name": "Enoxaparina 40mg", "dosage": "40mg", "frequency": "Cada 24 horas SQ", "duration": "Durante hospitalización"},
        ],
        "general_recommendations": "Aislamiento obligatorio. Monitoreo de saturación de oxígeno. Acudir a urgencias si saturación <90% o dificultad respiratoria severa.",
    },
    {
        "disease_name": "Gastroenteritis Aguda",
        "medicines": [
            {"name": "Solución de rehidratación oral", "dosage": "1L", "frequency": "A demanda, pequeños sorbos", "duration": "Durante cuadro"},
            {"name": "Lactobacillus (probiótico)", "dosage": "1 sobre", "frequency": "Cada 12 horas", "duration": "7 días"},
            {"name": "Loperamida 2mg", "dosage": "2mg", "frequency": "Después de cada evacuación (máx 8mg/día)", "duration": "Máx 2 días"},
        ],
        "general_recommendations": "Dieta blanda (arroz, manzana, zanahoria reposo GI). Suspender lácteos temporalmente. Signos de alarma: fiebre >39°C o heces con sangre.",
    },
    {
        "disease_name": "Neumonía",
        "medicines": [
            {"name": "Amoxicilina 500mg", "dosage": "500mg", "frequency": "Cada 8 horas", "duration": "10 días"},
            {"name": "Paracetamol 500mg", "dosage": "500mg", "frequency": "Cada 8 horas", "duration": "5 días"},
            {"name": "Salbutamol inhalador", "dosage": "2 inhalaciones", "frequency": "Cada 6-8 horas PRN", "duration": "Según síntomas"},
        ],
        "general_recommendations": "REQUIERE HOSPITALIZACIÓN si saturación <92%. Fisioterapia respiratoria. Oxígeno suplementario si es necesario.",
    },
    {
        "disease_name": "Otitis Media",
        "medicines": [
            {"name": "Amoxicilina 250-500mg", "dosage": "250-500mg", "frequency": "Cada 8 horas", "duration": "7-10 días"},
            {"name": "Ibuprofeno 400mg", "dosage": "400mg", "frequency": "Cada 8 horas", "duration": "5 días"},
            {"name": "Gotas óticas (antimicrobianas)", "dosage": "3 gotas", "frequency": "Cada 8 horas", "duration": "7 días"},
        ],
        "general_recommendations": "Evitar entrada de agua en el oído. No introducir objetos. Evaluar por ORL si recurrente.",
    },
    {
        "disease_name": "Infección Urinaria",
        "medicines": [
            {"name": "Fosfomicina trometamol 3g", "dosage": "3g", "frequency": "Dosis única", "duration": "1 dosis"},
            {"name": "Ibuprofeno 400mg", "dosage": "400mg", "frequency": "Cada 8 horas PRN", "duration": "3 días"},
        ],
        "general_recommendations": "Aumentar ingesta de agua (>2L/día). Urocultivo si es recurrente. Evaluar por urología si más de 3 infecciones al año.",
    },
    {
        "disease_name": "Dengue",
        "medicines": [
            {"name": "Acetaminofén 500mg", "dosage": "500mg", "frequency": "Cada 6 horas", "duration": "5 días"},
            {"name": "Solución de rehidratación oral", "dosage": "1-2L", "frequency": "A demanda", "duration": "Durante cuadro"},
        ],
        "general_recommendations": "NO USAR AINES (ibuprofeno, aspirina) por riesgo de sangrado. Reposo absoluto. Monitorear signos de alarma: dolor abdominal intenso, vómitos persistentes, sangrado de encías. Acudir a urgencias de inmediato si presenta signos de alarma.",
    },
    {
        "disease_name": "Meningitis",
        "medicines": [
            {"name": "Ceftriaxona 2g IV", "dosage": "2g", "frequency": "Cada 12 horas IV", "duration": "14 días"},
            {"name": "Dexametasona 0.15mg/kg IV", "dosage": "0.15mg/kg", "frequency": "Cada 6 horas IV", "duration": "4 días"},
            {"name": "Paracetamol 500mg", "dosage": "500mg", "frequency": "Cada 6 horas PRN", "duration": "Según síntomas"},
        ],
        "general_recommendations": "EMERGENCIA MÉDICA - Hospitalización inmediata. Punción lumbar para diagnóstico. Aislamiento respiratorio. Monitoreo neurológico estricto.",
    },
    {
        "disease_name": "Hepatitis A",
        "medicines": [],
        "general_recommendations": "Reposo absoluto. Dieta baja en grasas. Evitar alcohol por 6 meses. Hidratación. La mayoría se resuelve sola en 2-4 semanas. No hay tratamiento antiviral específico. Vacunación para contactos.",
    },
    {
        "disease_name": "Bronquitis Aguda",
        "medicines": [
            {"name": "Paracetamol 500mg", "dosage": "500mg", "frequency": "Cada 8 horas", "duration": "5 días"},
            {"name": "Salbutamol inhalador", "dosage": "2 inhalaciones", "frequency": "Cada 6-8 horas PRN", "duration": "Según síntomas"},
            {"name": "Acetilcisteína 600mg", "dosage": "600mg", "frequency": "Cada 24 horas", "duration": "7 días"},
        ],
        "general_recommendations": "No requiere antibióticos a menos que se sospeche infección bacteriana. Nebulizaciones con solución salina. Evitar irritantes como humo de tabaco.",
    },
    {
        "disease_name": "Amigdalitis",
        "medicines": [
            {"name": "Amoxicilina 500mg", "dosage": "500mg", "frequency": "Cada 8 horas", "duration": "7-10 días"},
            {"name": "Ibuprofeno 400mg", "dosage": "400mg", "frequency": "Cada 8 horas", "duration": "5 días"},
            {"name": "Gárgaras con solución salina", "dosage": "Vaso de agua tibia + sal", "frequency": "Cada 6 horas", "duration": "5 días"},
        ],
        "general_recommendations": "Reposo vocal. Hidratación con líquidos fríos o tibios. Evaluar si hay absceso periamigdalino. Considerar amigdalectomía si es recurrente (>5 episodios/año).",
    },
    {
        "disease_name": "Rinitis Alérgica",
        "medicines": [
            {"name": "Loratadina 10mg", "dosage": "10mg", "frequency": "Cada 24 horas", "duration": "Según temporada"},
            {"name": "Budesonida nasal", "dosage": "2 atomizaciones", "frequency": "Cada 12 horas", "duration": "Durante exposición"},
        ],
        "general_recommendations": "Identificar y evitar alérgenos. Lavados nasales con solución salina. Considerar inmunoterapia si es severa.",
    },
    {
        "disease_name": "Intoxicación Alimentaria",
        "medicines": [
            {"name": "Solución de rehidratación oral", "dosage": "1L", "frequency": "A demanda", "duration": "Durante cuadro"},
            {"name": "Lactobacillus (probiótico)", "dosage": "1 sobre", "frequency": "Cada 12 horas", "duration": "7 días"},
        ],
        "general_recommendations": "Hidratación abundante. Dieta blanda. Carbón activado solo si fue hace <1 hora. Signos de alarma: fiebre >38.5°C, heces con sangre, signos de deshidratación severa.",
    },
    {
        "disease_name": "Tuberculosis",
        "medicines": [
            {"name": "Rifampicina 600mg", "dosage": "600mg", "frequency": "Cada 24 horas", "duration": "6 meses"},
            {"name": "Isoniacida 300mg", "dosage": "300mg", "frequency": "Cada 24 horas", "duration": "6 meses"},
            {"name": "Pirazinamida 1500mg", "dosage": "1500mg", "frequency": "Cada 24 horas", "duration": "2 meses"},
            {"name": "Etambutol 800mg", "dosage": "800mg", "frequency": "Cada 24 horas", "duration": "2 meses"},
        ],
        "general_recommendations": "TRATAMIENTO SUPERVISADO (DOTS). Notificación obligatoria a salud pública. Aislamiento respiratorio las primeras 2 semanas de tratamiento. Monitoreo de función hepática por hepatotoxicidad de los fármacos.",
    },
    {
        "disease_name": "Shigelosis (Disentería)",
        "medicines": [
            {"name": "Ciprofloxacina 500mg", "dosage": "500mg", "frequency": "Cada 12 horas", "duration": "5 días"},
            {"name": "Solución de rehidratación oral", "dosage": "1-2L", "frequency": "A demanda", "duration": "Durante cuadro"},
            {"name": "Lactobacillus (probiótico)", "dosage": "1 sobre", "frequency": "Cada 12 horas", "duration": "7 días"},
        ],
        "general_recommendations": "Aislamiento entérico. Higiene de manos estricta. No usar loperamida (riesgo de megacolon tóxico). Reporte a salud pública obligatorio.",
    },
]


async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    collections = await db.list_collection_names()
    if "symptoms" in collections:
        await db.symptoms.drop()
        print("Dropped existing symptoms collection")
    if "diseases" in collections:
        await db.diseases.drop()
        print("Dropped existing diseases collection")
    if "treatments" in collections:
        await db.treatments.drop()
        print("Dropped existing treatments collection")

    await db.symptoms.insert_many(symptoms)
    print(f"Inserted {len(symptoms)} symptoms")

    await db.diseases.insert_many(diseases)
    print(f"Inserted {len(diseases)} diseases")

    await db.treatments.insert_many(treatments)
    print(f"Inserted {len(treatments)} treatments")

    client.close()
    print("Seed completed!")


if __name__ == "__main__":
    asyncio.run(seed())
