"""
CREW HEALTH MONITOR - Dashboard
NASA Space Apps Challenge 2026

Para correrlo:   streamlit run app.py
Atajos en la dirección:  ?dia=21  (abre ese día)   ?lang=en  (abre en inglés)
"""

import json
import time
from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import generador as gen
import tema

st.set_page_config(page_title="Crew Health Monitor", page_icon="🛰️", layout="wide")
tema.aplicar()          # solo apariencia: colores, tipografías y animaciones

IDIOMA_POR_DEFECTO = "Español"

# ===========================================================================
# TEXTOS (ESPAÑOL / INGLÉS)
# ===========================================================================
T = {
    "Español": dict(
        titulo="Crew Health Monitor",
        subtitulo="Monitor de salud de la tripulación · misión simulada a Marte (fase de viaje) · tormentas solares reales de NASA DONKI",
        dia="Día de misión", tab_panel="🛰️ Panel de la misión", tab_bitacora="📜 Bitácora", tab_como="💡 Cómo funciona",
        tripulacion="Estado de la tripulación", preparacion="Preparación", apto="Apto para tareas críticas",
        apto_c="Apto", no_apto_c="No apto",
        no_apto="No apto para tareas críticas", alertas="Alertas de hoy",
        sin_alertas="Sin alertas: toda la tripulación está dentro de su normal.",
        tendencias="Tendencias", variable="Variable", radiacion="Radiación: ¿cuánto ayuda seguir la alerta?",
        rad_hoy="Radiación hoy", rad_acum="Dosis acumulada", del_limite="del límite de carrera de NASA (600 mSv)",
        co2="CO₂ de la cabina", co2_lim="límite NASA: 3 mmHg", temp_cab="Temperatura de la cabina", ambiente="Ambiente de la nave",
        tierra="Mensaje para el médico en la Tierra", retraso="Llega en ~{m} min (según NASA, el retraso de ida va de 0 a ~22 min). Lo urgente se resuelve a bordo.",
        nave="🛰️ Es la nave", persona="🧑‍🚀 Eres tú", afecta="Afecta a", accion="Qué hacer", datos="Datos",
        bordo="✅ Se resuelve a bordo", tierra_t="📡 Consultar con la Tierra",
        normal="diferencia vs. su normal", sin_ref="Sin refugio", con_ref="Con refugio (siguiendo la alerta)",
        ahorro="Radiación evitada gracias a las alertas", eventos_t="Eventos del guion",
        estado={"verde": "Bien", "amarillo": "Atención", "rojo": "Actuar ahora"},
        nota="Datos fisiológicos simulados con rangos de referencia de NASA y estudios publicados. Las fechas de las tormentas solares son reales (NASA DONKI).",
        bit_titulo="Todo lo que detectó la app durante la misión", bit_dia="Día", bit_nivel="Nivel", bit_alerta="Alerta",
        bit_origen="Origen", bit_afecta="Afecta a", bit_triaje="Triaje", bit_detalle="Datos",
        prep_titulo="Índice de preparación de cada astronauta (0–100)",
        sensor="🔧 Es el sensor", porque="¿Por qué?", regla="Regla", evidencia="Datos que la dispararon",
        fuentes="Fuente", su_normal="su normal", desv="desviaciones", limite="límite",
        donki="NASA DONKI registró una tormenta solar (SEP) este día",
        sintomas="{v} de {t} astronautas con síntomas de CO₂",
        apagon="Apagón de comunicaciones (conjunción solar)",
        apagon_ayuda="Cuando Marte queda detrás del Sol, no hay contacto con la Tierra durante dos a tres semanas (NASA).",
        apagon_aviso="📵 Sin contacto con la Tierra: todo se resuelve a bordo. Los informes quedan en cola.",
        en_cola="⏸️ En cola (sin contacto): resolver a bordo", cola="{n} mensaje(s) en cola: se enviarán al recuperar el contacto.",
        val_titulo="Validación: ¿la app detecta lo que pasó?",
        val_intro="Comparamos las alertas con el guion de la misión (lo que de verdad pasó).",
        val_eventos="Eventos detectados", val_primer="Detectados el primer día", val_dias="Días con evento detectados",
        val_falsas="Falsas alarmas", val_robust="Prueba de robustez: 30 misiones con distintas variaciones aleatorias",
        val_recall="Días con evento detectados (promedio)", val_prec="Alertas correctas (promedio)",
        val_falsas_prom="Falsas alarmas por misión (promedio)", val_todos="Misiones con los 8 eventos detectados",
        val_evento="Evento", val_afecta="Afecta a", val_dias_t="Días", val_det="Detectados", val_1="¿Primer día?",
        envivo="Sensor en vivo", envivo_sin="Esperando datos del sensor…",
        envivo_ayuda="Pulso y SpO₂ reales desde un MAX30102 + ESP32 (ver la carpeta hardware).",
    ),
    "English": dict(
        titulo="Crew Health Monitor",
        subtitulo="Crew health monitor · simulated Mars mission (transit phase) · real solar storms from NASA DONKI",
        dia="Mission day", tab_panel="🛰️ Mission dashboard", tab_bitacora="📜 Mission log", tab_como="💡 How it works",
        tripulacion="Crew status", preparacion="Readiness", apto="Cleared for critical tasks",
        apto_c="Cleared", no_apto_c="Not cleared",
        no_apto="Not cleared for critical tasks", alertas="Today's alerts",
        sin_alertas="No alerts: the whole crew is within their personal baseline.",
        tendencias="Trends", variable="Variable", radiacion="Radiation: how much does following the alert help?",
        rad_hoy="Radiation today", rad_acum="Cumulative dose", del_limite="of NASA career limit (600 mSv)",
        co2="Cabin CO₂", co2_lim="NASA limit: 3 mmHg", temp_cab="Cabin temperature", ambiente="Spacecraft environment",
        tierra="Message for the flight surgeon on Earth", retraso="Arrives in ~{m} min (per NASA, one-way delay ranges from 0 to ~22 min). Urgent issues are handled on board.",
        nave="🛰️ It's the spacecraft", persona="🧑‍🚀 It's you", afecta="Affects", accion="What to do", datos="Data",
        bordo="✅ Handled on board", tierra_t="📡 Consult Earth",
        normal="difference vs. personal baseline", sin_ref="Without shelter", con_ref="With shelter (following the alert)",
        ahorro="Radiation avoided thanks to alerts", eventos_t="Mission script events",
        estado={"verde": "OK", "amarillo": "Watch", "rojo": "Act now"},
        nota="Physiological data simulated from NASA reference values and published studies. Solar storm dates are real (NASA DONKI).",
        bit_titulo="Everything the app detected during the mission", bit_dia="Day", bit_nivel="Level", bit_alerta="Alert",
        bit_origen="Source", bit_afecta="Affects", bit_triaje="Triage", bit_detalle="Data",
        prep_titulo="Readiness index of each astronaut (0–100)",
        sensor="🔧 It's the sensor", porque="Why?", regla="Rule", evidencia="Data that triggered it",
        fuentes="Source", su_normal="baseline", desv="deviations", limite="limit",
        donki="NASA DONKI recorded a solar storm (SEP) on this day",
        sintomas="{v} of {t} astronauts with CO₂ symptoms",
        apagon="Communications blackout (solar conjunction)",
        apagon_ayuda="When Mars is behind the Sun, there is no contact with Earth for two to three weeks (NASA).",
        apagon_aviso="📵 No contact with Earth: everything is handled on board. Reports are queued.",
        en_cola="⏸️ Queued (no contact): handle on board", cola="{n} message(s) queued: they will be sent when contact returns.",
        val_titulo="Validation: does the app detect what happened?",
        val_intro="We compare the alerts with the mission script (what really happened).",
        val_eventos="Events detected", val_primer="Detected on the first day", val_dias="Event days detected",
        val_falsas="False alarms", val_robust="Robustness test: 30 missions with different random variation",
        val_recall="Event days detected (average)", val_prec="Correct alerts (average)",
        val_falsas_prom="False alarms per mission (average)", val_todos="Missions with all 8 events detected",
        val_evento="Event", val_afecta="Affects", val_dias_t="Days", val_det="Detected", val_1="First day?",
        envivo="Live sensor", envivo_sin="Waiting for sensor data…",
        envivo_ayuda="Real heart rate and SpO₂ from a MAX30102 + ESP32 (see the hardware folder).",
    ),
}

MENSAJES = {
    "Español": {
        "tormenta": ("Tormenta solar detectada", "Ir al refugio de la nave y suspender actividades fuera de él hasta que baje la radiación."),
        "co2": ("CO₂ alto en la cabina", "Toda la tripulación respira más rápido, tiene dolor de cabeza y reacciona más lento: el problema es la nave. Revisar el filtro de CO₂ y evitar ejercicio intenso."),
        "ambiente": ("Cambio en varios tripulantes a la vez", "Probable causa ambiental: revisar los sistemas de la cabina."),
        "infeccion": ("Posible infección", "Pulso y temperatura por encima de su normal. Descansar, hidratarse, separarse del resto y avisar al médico."),
        "fatiga": ("Fatiga / falta de sueño", "Durmió mucho menos de lo normal y su concentración bajó. Priorizar el descanso y evitar tareas críticas hoy."),
        "spo2": ("Oxigenación baja", "Repetir la medición y revisar el nivel de oxígeno de la cabina."),
        "renal": ("Riesgo de cálculo renal", "Orina por debajo de 1,5 L/día con pérdida ósea en curso: el calcio de los huesos puede formar cálculos. Tomar más agua (meta: 2,5–3 L de orina al día)."),
        "ejercicio": ("Sin ejercicio suficiente", "Sin ejercicio, la pérdida ósea se acelera. Recuperar la rutina (~2 h/día) apenas sea posible."),
        "individual": ("Fuera de su normal", "Repetir la medición y vigilar en las próximas horas."),
        "sensor_co2": ("Posible falla del sensor de CO₂", "El sensor marca CO₂ alto, pero nadie tiene síntomas. Verificar con un medidor portátil antes de actuar y no detener tareas por ahora."),
        "sensor_spo2": ("Posible falla del oxímetro", "La SpO₂ marcada es muy baja, pero el pulso y la respiración están normales. Reacomodar el sensor y repetir la medición."),
        "presion": ("Presión arterial fuera de rango", "Repetir la medición en reposo. Si sigue alta (≥ 140/90) o muy baja (< 90/60), consultar con el médico en la Tierra."),
        "glucosa": ("Glucosa fuera de rango", "Si está baja (< 70): comer algo con azúcar ya y volver a medir. Si está alta: más actividad física, revisar la dieta y repetir mañana en ayunas."),
        "animo": ("Ánimo bajo varios días", "Es normal en misiones largas. Descansar, hablar con la tripulación y agendar una conversación privada con el psicólogo en la Tierra."),
        "vision": ("Cambio en la visión", "Puede ser una señal de SANS. Repetir el test visual mañana y enviar las fotos del ojo al médico en la Tierra."),
    },
    "English": {
        "tormenta": ("Solar storm detected", "Go to the storm shelter and suspend activities outside it until radiation drops."),
        "co2": ("High cabin CO₂", "The whole crew is breathing faster, has headaches and reacts slower: the problem is the spacecraft. Check the CO₂ scrubber and avoid intense exercise."),
        "ambiente": ("Several crew members changed at once", "Likely environmental cause: check cabin systems."),
        "infeccion": ("Possible infection", "Heart rate and temperature above baseline. Rest, hydrate, isolate from the crew and notify the flight surgeon."),
        "fatiga": ("Fatigue / sleep loss", "Slept much less than usual and concentration dropped. Prioritize rest and avoid critical tasks today."),
        "spo2": ("Low oxygen saturation", "Repeat the measurement and check cabin oxygen levels."),
        "renal": ("Kidney stone risk", "Urine output below 1.5 L/day while bone loss is ongoing: calcium released from bone can form stones. Drink more water (target: 2.5–3 L of urine per day)."),
        "ejercicio": ("Not enough exercise", "Without exercise, bone loss speeds up. Resume the routine (~2 h/day) as soon as possible."),
        "individual": ("Outside personal baseline", "Repeat the measurement and monitor over the next hours."),
        "sensor_co2": ("Possible CO₂ sensor failure", "The sensor reads high CO₂, but nobody has symptoms. Check with a portable meter before acting; don't stop work for now."),
        "sensor_spo2": ("Possible pulse oximeter failure", "SpO₂ reads very low, but heart rate and breathing are normal. Reposition the sensor and measure again."),
        "presion": ("Blood pressure out of range", "Measure again at rest. If it stays high (≥ 140/90) or very low (< 90/60), consult the flight surgeon on Earth."),
        "glucosa": ("Blood sugar out of range", "If low (< 70): eat something sugary now and measure again. If high: more physical activity, check your diet and repeat tomorrow while fasting."),
        "animo": ("Low mood for several days", "This is common on long missions. Rest, talk with the crew and schedule a private conversation with the psychologist on Earth."),
        "vision": ("Change in vision", "It may be a sign of SANS. Repeat the vision test tomorrow and send the eye photos to the flight surgeon on Earth."),
    },
}

# Por qué se dispara cada alerta (la regla) y qué fuente de NASA la respalda
REGLAS = {
    "Español": {
        "tormenta": "NASA DONKI registró una tormenta solar ese día. Las tormentas dan picos de radiación que se reducen en el refugio.",
        "co2": "El CO₂ supera el límite de NASA (3 mmHg) y 2 o más astronautas tienen síntomas a la vez (respiración, dolor de cabeza o reacción): la causa es el aire de la nave.",
        "sensor_co2": "El sensor marca CO₂ alto, pero menos de 2 astronautas tienen síntomas. Si el aire estuviera mal, todos lo notarían: lo más probable es que falle el sensor.",
        "ambiente": "3 o más astronautas se salen de su normal en la misma variable el mismo día: probable causa ambiental.",
        "infeccion": "Pulso y temperatura por encima de su normal a la vez (o temperatura ≥ 38 °C), en una sola persona.",
        "fatiga": "Duerme mucho menos que su normal o reacciona más lento en la prueba PVT, sin una causa de la nave.",
        "spo2": "Oxigenación por debajo de su normal o de 95 %, con otros signos que la acompañan.",
        "sensor_spo2": "SpO₂ menor a 90 % sin ningún cambio en pulso ni respiración: una caída real de oxígeno afectaría también a esas variables.",
        "renal": "Orina por debajo de 1,5 L/día mientras sigue la pérdida ósea: el calcio de los huesos puede formar cálculos.",
        "ejercicio": "Menos de 60 minutos de ejercicio en el día: sin ejercicio la pérdida ósea pasa de ~1 % a ~1,5 % por mes.",
        "individual": "Una variable se aleja 3 o más desviaciones de su normal.",
        "presion": "Categorías de la American Heart Association: alta desde 130/80, etapa 2 desde 140/90; baja por debajo de 90/60. En el espacio la presión suele bajar ~10 mmHg.",
        "glucosa": "Glucosa en ayunas: normal 70–99 mg/dL, elevada 100–125, muy elevada ≥ 126, baja < 70. En el espacio aparece resistencia a la insulina, sobre todo con poca actividad.",
        "animo": "Ánimo 1 punto o más por debajo de su normal durante 3 días seguidos (o ≤ 2 en el check-in). Para NASA, el aislamiento y el encierro son el mayor riesgo conductual.",
        "vision": "El astronauta reporta visión borrosa o cambios en el test de la cuadrícula. NASA estudia estos cambios como SANS.",
    },
    "English": {
        "tormenta": "NASA DONKI recorded a solar storm that day. Storms cause radiation spikes that the shelter reduces.",
        "co2": "CO₂ is above NASA's limit (3 mmHg) and 2 or more astronauts show symptoms at once (breathing, headache or reaction time): the cause is the cabin air.",
        "sensor_co2": "The sensor reads high CO₂, but fewer than 2 astronauts have symptoms. If the air were bad, everyone would feel it: the sensor is most likely failing.",
        "ambiente": "3 or more astronauts leave their baseline in the same variable on the same day: likely environmental cause.",
        "infeccion": "Heart rate and temperature above baseline at the same time (or temperature ≥ 38 °C), in one person only.",
        "fatiga": "Sleeps much less than baseline or reacts slower on the PVT, with no spacecraft cause.",
        "spo2": "Oxygen saturation below baseline or below 95 %, with other signs.",
        "sensor_spo2": "SpO₂ below 90 % with no change in heart rate or breathing: a real drop in oxygen would affect those too.",
        "renal": "Urine output below 1.5 L/day while bone loss continues: calcium from bone can form stones.",
        "ejercicio": "Less than 60 minutes of exercise that day: without exercise bone loss rises from ~1 % to ~1.5 % per month.",
        "individual": "A variable is 3 or more deviations away from personal baseline.",
        "presion": "American Heart Association categories: high from 130/80, stage 2 from 140/90; low below 90/60. In space blood pressure usually drops ~10 mmHg.",
        "glucosa": "Fasting glucose: normal 70–99 mg/dL, elevated 100–125, very high ≥ 126, low < 70. In space insulin resistance appears, especially with low activity.",
        "animo": "Mood 1 point or more below baseline for 3 days in a row (or ≤ 2 in the check-in). For NASA, isolation and confinement are the greatest behavioral risk.",
        "vision": "The astronaut reports blurred vision or changes in the grid test. NASA studies these changes as SANS.",
    },
}
FUENTES = {
    "tormenta": [("NASA DONKI", "https://ccmc.gsfc.nasa.gov/tools/DONKI"),
                 ("NASA-STD-3001 Radiation", "https://www.nasa.gov/wp-content/uploads/2023/03/radiation-protection-technical-brief-ochmo.pdf")],
    "co2": [("NASA CO₂ Technical Brief", "https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-004-carbon-dioxide.pdf")],
    "sensor_co2": [("NASA CO₂ Technical Brief", "https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-004-carbon-dioxide.pdf")],
    "ambiente": [("NASA Human System Risks", "https://www.nasa.gov/human-system-risks")],
    "infeccion": [("NASA Human System Risks (Immune)", "https://www.nasa.gov/human-system-risks"),
                  ("Stahn et al. 2017 (body temperature)", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5701078/")],
    "fatiga": [("Barger et al. 2014 (sleep)", "https://www.eurekalert.org/news-releases/595450"),
               ("NASA Cognition (PVT)", "https://www.med.upenn.edu/uep/cognition.html")],
    "spo2": [("NASA Habitable Atmosphere Brief", "https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-003-habitable-atmosphere.pdf")],
    "sensor_spo2": [("NASA Habitable Atmosphere Brief", "https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-003-habitable-atmosphere.pdf")],
    "renal": [("NASA renal stone risk (NTRS)", "https://ntrs.nasa.gov/api/citations/20170004709/downloads/20170004709.pdf")],
    "ejercicio": [("NASA bone changes risk", "https://www.nasa.gov/reference/risk-of-spaceflight-induced-bone-changes/")],
    "individual": [("NASA Human System Risks", "https://www.nasa.gov/human-system-risks")],
    "presion": [("Norsk et al. 2015 (NASA, blood pressure in space)", "https://www.healthday.com/health-news/cardiovascular-diseases/weightlessness-in-space-may-lower-blood-pressure-in-astronauts-695509.html"),
                ("American Heart Association", "https://heart.org/bplevels")],
    "glucosa": [("Hughson et al. (insulin resistance in space)", "https://gizmodo.com/living-in-space-is-like-being-old-and-having-type-2-dia-1592801454"),
                ("NASA HRP Risks (Food and Nutrition)", "https://www.nasa.gov/hrp/risks/")],
    "animo": [("NASA Behavioral Risk in Spaceflight", "https://ntrs.nasa.gov/api/citations/20240000994/downloads/Behavioral%20Risk%20In%20Spaceflight_Picano.pdf"),
              ("NASA HRP Risks (Behavioral)", "https://www.nasa.gov/hrp/risks/")],
    "vision": [("NASA HRP Risks (SANS)", "https://www.nasa.gov/hrp/risks/"),
               ("NASA Ongoing HRP Research", "https://www.nasa.gov/hrp/ongoing-hrp-research/")],
}
# Qué hacer a bordo si no hay contacto con la Tierra (modo apagón)
PROTOCOLO_APAGON = {
    "Español": {
        "infeccion": "Protocolo a bordo: aislar, hidratar, medir temperatura cada 4 h y seguir la guía médica del botiquín.",
        "renal": "Protocolo a bordo: subir la ingesta de agua y repetir la medición mañana.",
        "spo2": "Protocolo a bordo: repetir la medición y revisar el oxígeno de la cabina.",
        "presion": "Protocolo a bordo: descansar 15 minutos, repetir la medición y anotar ambas.",
        "animo": "Protocolo a bordo: descanso, una actividad con la tripulación y un mensaje grabado para el psicólogo, que se enviará al recuperar contacto.",
        "vision": "Protocolo a bordo: repetir el test visual y las fotos del ojo cada día hasta recuperar contacto.",
    },
    "English": {
        "infeccion": "On-board protocol: isolate, hydrate, check temperature every 4 h and follow the medical kit guide.",
        "renal": "On-board protocol: increase water intake and measure again tomorrow.",
        "spo2": "On-board protocol: repeat the measurement and check cabin oxygen.",
        "presion": "On-board protocol: rest 15 minutes, measure again and log both readings.",
        "animo": "On-board protocol: rest, an activity with the crew and a recorded message for the psychologist, sent when contact returns.",
        "vision": "On-board protocol: repeat the vision test and eye photos daily until contact returns.",
    },
}

NOMBRES_VAR = {
    "Español": {"fc_lpm": "Pulso en reposo (lpm)", "temp_c": "Temperatura (°C)", "spo2_pct": "SpO₂ (%)",
                "resp_rpm": "Respiración (rpm)", "sueno_h": "Sueño (h)", "reaccion_ms": "Reacción PVT (ms)",
                "cefalea_0a10": "Dolor de cabeza (0–10)", "orina_l": "Orina (L/día)", "ejercicio_min": "Ejercicio (min)",
                "perdida_osea_pct": "Pérdida ósea acumulada (%)", "fatiga_0a10": "Fatiga (0–10)",
                "estres_0a10": "Estrés (0–10)", "estres_termico_0a10": "Estrés térmico (0–10)",
                "preparacion": "Índice de preparación (0–100)", "co2_mmhg": "CO₂ cabina (mmHg)",
                "pas_mmhg": "Presión sistólica (mmHg)", "pad_mmhg": "Presión diastólica (mmHg)",
                "glucosa_mgdl": "Glucosa en ayunas (mg/dL)", "animo_1a5": "Ánimo (1–5)"},
    "English": {"fc_lpm": "Resting heart rate (bpm)", "temp_c": "Body temperature (°C)", "spo2_pct": "SpO₂ (%)",
                "resp_rpm": "Respiratory rate (rpm)", "sueno_h": "Sleep (h)", "reaccion_ms": "PVT reaction (ms)",
                "cefalea_0a10": "Headache (0–10)", "orina_l": "Urine (L/day)", "ejercicio_min": "Exercise (min)",
                "perdida_osea_pct": "Cumulative bone loss (%)", "fatiga_0a10": "Fatigue (0–10)",
                "estres_0a10": "Stress (0–10)", "estres_termico_0a10": "Heat stress (0–10)",
                "preparacion": "Readiness index (0–100)", "co2_mmhg": "Cabin CO₂ (mmHg)",
                "pas_mmhg": "Systolic pressure (mmHg)", "pad_mmhg": "Diastolic pressure (mmHg)",
                "glucosa_mgdl": "Fasting glucose (mg/dL)", "animo_1a5": "Mood (1–5)"},
}

# Colores pensados para fondo oscuro (verde = bien, amarillo/naranja = atención, rojo = crítico)
COLOR = {"verde": "#35d49a", "amarillo": "#ffb547", "rojo": "#ff5a5f"}
ORDEN = {"verde": 0, "amarillo": 1, "rojo": 2}
COLOR_ASTRONAUTA = {"A1": "#5aa9ff", "A2": "#ff9a52", "A3": "#3ddc97", "A4": "#b28cff"}
COLOR_EVENTO = {"mal_sueno": "#a78bfa", "sin_ejercicio": "#94a3b8", "deshidratacion": "#38bdf8",
                "falla_filtro_co2": "#fbbf24", "infeccion": "#34d399",
                "falla_sensor_co2": "#d08b4a", "falla_sensor_spo2": "#d08b4a"}
COLOR_ORIGEN = {"nave": "#3ee0ff", "persona": "#c4b5fd", "sensor": "#8a96a8"}
COLOR_SENSOR = "#8a96a8"
ARCHIVO_VIVO = Path(__file__).parent / "data" / "en_vivo.csv"


# ===========================================================================
# DATOS
# ===========================================================================
@st.cache_data
def datos():
    return gen.cargar_o_generar()


mision, alertas = datos()
val_resumen, val_tabla, val_falsas = gen.validar(mision, alertas)
try:
    robustez = pd.read_csv(Path(__file__).parent / "data" / "robustez.csv")
except FileNotFoundError:
    robustez = None
base = gen.lineas_base(mision)
tormentas = sorted(mision.loc[mision["tormenta_solar"], "fecha"].unique())
ultimo_dia = int(mision["dia_mision"].max())

# ===========================================================================
# BARRA LATERAL
# ===========================================================================
with st.sidebar:
    st.markdown("<div class='consola-marca'>🛰️ Consola · Console</div>", unsafe_allow_html=True)
    inicial ="English" if st.query_params.get("lang", "") == "en" else IDIOMA_POR_DEFECTO
    idioma = st.radio("Idioma / Language", ["Español", "English"],
                      index=["Español", "English"].index(inicial), horizontal=True)
    tx, msg, nv = T[idioma], MENSAJES[idioma], NOMBRES_VAR[idioma]
    opciones_modo = ["astronauta", "mision", "juego"]
    modo = st.radio("Modo" if idioma == "Español" else "Mode", opciones_modo,
                    index=opciones_modo.index(st.query_params.get("modo", "astronauta"))
                    if st.query_params.get("modo", "") in opciones_modo else 0,
                    format_func=lambda m: {"astronauta": "🧑‍🚀 " + ("Modo astronauta" if idioma == "Español" else "Astronaut mode"),
                                           "mision": "🛰️ " + ("Modo misión" if idioma == "Español" else "Mission mode"),
                                           "juego": "🎮 " + ("Modo juego · Misión Cóndor" if idioma == "Español" else "Game mode · Mission Condor")}[m])
    try:
        dia_inicial = min(max(int(st.query_params.get("dia", 9)), 1), ultimo_dia)
    except ValueError:
        dia_inicial = 9
    dia = st.slider(tx["dia"], 1, ultimo_dia, dia_inicial)
    fecha = mision.loc[mision["dia_mision"] == dia, "fecha"].iloc[0]
    st.caption(f"📅 {fecha:%Y-%m-%d}")
    apagon = st.toggle(tx["apagon"], value=st.query_params.get("apagon", "") == "1", help=tx["apagon_ayuda"])
    st.markdown(f"**{tx['eventos_t']}**")
    clave = "es" if idioma == "Español" else "en"
    st.markdown(f"<span style='color:{COLOR['rojo']}'>■</span> "
                + ("Tormentas solares reales (NASA DONKI): " if clave == "es" else "Real solar storms (NASA DONKI): ")
                + ", ".join(f"{d.day}" for d in tormentas) + (" de mayo" if clave == "es" else " May"),
                unsafe_allow_html=True)
    for e in gen.GUION:
        d0, d1 = pd.Timestamp(e["inicio"]).day, pd.Timestamp(e["fin"]).day
        dias_txt = f"{d0}" if d0 == d1 else f"{d0}–{d1}"
        st.markdown(f"<span style='color:{COLOR_EVENTO[e['evento']]}'>■</span> {dias_txt}: {e[clave]}",
                    unsafe_allow_html=True)
    st.divider()
    st.caption(tx["nota"])

hoy = mision[mision["dia_mision"] == dia].set_index("astronauta")
amb = hoy.iloc[0]
alertas_hoy = alertas[alertas["dia_mision"] == dia]


def nivel_de(astronauta, tabla=alertas_hoy):
    # una falla de sensor no cambia el estado de salud de la persona
    niveles = [a["nivel"] for _, a in tabla.iterrows()
               if astronauta in str(a["afectados"]) and a["origen"] != "sensor"]
    return max(niveles, key=ORDEN.get) if niveles else "verde"


def franjas(fig, alto=330):
    for d in tormentas:
        fig.add_vrect(x0=d, x1=d + timedelta(days=1), fillcolor=COLOR["rojo"], opacity=0.13, line_width=0)
    for e in gen.GUION:
        fig.add_vrect(x0=e["inicio"], x1=pd.Timestamp(e["fin"]) + pd.Timedelta(days=1),
                      fillcolor=COLOR_EVENTO[e["evento"]], opacity=0.12, line_width=0)
    fig.add_vline(x=fecha, line_dash="dash", line_color="rgba(62,224,255,.7)")
    fig.update_layout(height=alto, margin=dict(l=10, r=10, t=30, b=10),
                      legend=dict(orientation="h", y=1.12), hovermode="x unified")
    return fig


def texto_evidencia(ev):
    """Convierte la evidencia guardada por el motor en frases legibles."""
    lineas = []
    for e in json.loads(ev) if isinstance(ev, str) and ev else []:
        if e["t"] == "z":
            lineas.append(f"{e['astronauta']} · {nv.get(e['var'], e['var'])}: **{e['valor']:g}** "
                          f"({tx['su_normal']}: {e['normal']:g}; {e['z']:+.1f} {tx['desv']})")
        elif e["t"] == "lim":
            nombre = nv.get(e["var"], e["var"])
            extra = f" ({tx['limite']}: {e['limite']:g})" if e["limite"] else ""
            lineas.append(f"{nombre}: **{e['valor']:g}**{extra}")
        elif e["t"] == "donki":
            lineas.append(tx["donki"])
        elif e["t"] == "n":
            lineas.append(tx["sintomas"].format(v=e["valor"], t=e["total"]))
        elif e["t"] == "pa":
            lineas.append(("Presión arterial" if idioma == "Español" else "Blood pressure") + f": **{e['valor']}** mmHg")
        elif e["t"] == "txt":
            lineas.append(e["valor"])
        elif e["t"] == "dias":
            lineas.append((f"{e['valor']} días seguidos" if idioma == "Español" else f"{e['valor']} days in a row"))
    return lineas


ORIGEN = {"nave": tx["nave"], "persona": tx["persona"], "sensor": tx["sensor"]}
nv.setdefault("radiacion_sin_refugio_msv", "Radiación del día (mSv)" if idioma == "Español" else "Radiation today (mSv)")


# ===========================================================================
# ENCABEZADO
# ===========================================================================
# Modo juego: "Misión Cóndor" tiene su propia barra (días, barras y enlace con la Tierra)
if modo == "juego":
    import juego
    juego.mostrar(dict(mision=mision, alertas=alertas, base=base, idioma=idioma, msg=msg, nv=nv,
                       reglas=REGLAS[idioma], fuentes=FUENTES, protocolo=PROTOCOLO_APAGON[idioma],
                       texto_evidencia=texto_evidencia))
    st.stop()

# Barra de misión: solo muestra datos que ya existen (día, fecha, alertas de la nave, radiación, enlace)
h = tema.H[idioma]
de_la_nave = alertas_hoy[alertas_hoy["codigo"].isin(["tormenta", "co2", "sensor_co2", "ambiente"])]
if de_la_nave.empty:
    nave_txt, nave_col = h["nominal"], COLOR["verde"]
else:
    a0 = de_la_nave.sort_values("nivel", key=lambda s: s.map(ORDEN), ascending=False).iloc[0]
    nave_txt = msg[a0["codigo"]][0]
    nave_col = COLOR_SENSOR if a0["origen"] == "sensor" else COLOR[a0["nivel"]]
enlace_txt, enlace_col = ((h["sin_contacto"], COLOR["rojo"]) if apagon
                          else (h["retraso"].format(m=gen.RETRASO_TIERRA_MIN), COLOR["verde"]))
st.markdown(tema.hud(idioma, tx["titulo"], tx["subtitulo"], [
    (h["mision"], h["mision_v"], None),
    (h["tmas"], f"{h['dia']} {dia:02d} / {ultimo_dia}", None),
    (h["fecha"], f"{fecha:%Y-%m-%d}", None),
    (h["nave"], nave_txt, nave_col),
    (h["enlace"], enlace_txt, enlace_col),
    (h["rad"], f"{amb['radiacion_acum_msv']:.0f} mSv · {amb['radiacion_pct_limite']:.1f}%", None),
]), unsafe_allow_html=True)

if modo == "astronauta":
    import astronauta
    astronauta.mostrar(dict(
        mision=mision, alertas=alertas, base=base, dia=dia, fecha=fecha, idioma=idioma, tx=tx, msg=msg, nv=nv,
        reglas=REGLAS[idioma], fuentes=FUENTES, origen=ORIGEN, color=COLOR, orden=ORDEN, apagon=apagon,
        protocolo=PROTOCOLO_APAGON[idioma], texto_evidencia=texto_evidencia, franjas=franjas,
        color_astronauta=COLOR_ASTRONAUTA, color_origen=COLOR_ORIGEN))
    st.stop()
tab_panel, tab_bitacora, tab_como = st.tabs([tx["tab_panel"], tx["tab_bitacora"], tx["tab_como"]])

# ===========================================================================
# PESTAÑA 1: PANEL DE LA MISIÓN
# ===========================================================================
with tab_panel:
    st.markdown(tema.seccion(tx["tripulacion"], f"{tx['dia']} {dia} · {fecha:%Y-%m-%d}"), unsafe_allow_html=True)
    cols = st.columns(4)
    for i, (col, (nombre, f)) in enumerate(zip(cols, hoy.iterrows())):
        nivel = nivel_de(nombre)
        prep = int(f["preparacion"])
        apto = prep >= 70 and nivel != "rojo"
        color_prep = COLOR["verde"] if prep >= 70 else (COLOR["amarillo"] if prep >= 45 else COLOR["rojo"])
        filas_html = ""
        for var, fmt in [("fc_lpm", "{:.0f}"), ("temp_c", "{:.1f}"), ("spo2_pct", "{:.1f}"),
                         ("resp_rpm", "{:.1f}"), ("sueno_h", "{:.1f}"), ("reaccion_ms", "{:.0f}"),
                         ("cefalea_0a10", "{:.1f}")]:
            delta = f[var] - base.loc[nombre, (var, "mean")]
            fuera = abs(delta) >= 2 * gen.PISO[var]
            filas_html += (f"<tr><td>{nv[var]}</td><td>{fmt.format(f[var])}</td>"
                           f"<td style='color:{COLOR['rojo'] if fuera else '#5f7590'}'>{delta:+.1f}</td></tr>")
        for var, fmt, malo in [("pas_mmhg", "{:.0f}", f["pas_mmhg"] >= gen.PAS_ALTA or f["pas_mmhg"] < gen.PAS_BAJA),
                               ("glucosa_mgdl", "{:.0f}", f["glucosa_mgdl"] >= gen.GLU_ALTA or f["glucosa_mgdl"] < gen.GLU_BAJA),
                               ("orina_l", "{:.1f}", f["orina_l"] < gen.ORINA_MIN),
                               ("ejercicio_min", "{:.0f}", f["ejercicio_min"] < gen.EJERCICIO_MIN),
                               ("perdida_osea_pct", "{:.2f}", False)]:
            filas_html += (f"<tr class='{'mal' if malo else ''}'><td>{nv[var]}</td>"
                           f"<td>{fmt.format(f[var])}</td><td></td></tr>")
        col.markdown(
            f"<div class='trip entrar' style='--c:{COLOR[nivel]};animation-delay:{i * 0.07:.2f}s'>"
            f"<div class='trip-cab'><div class='avatar' style='--a:{COLOR_ASTRONAUTA[nombre]}'>🧑‍🚀</div>"
            f"<div style='flex:1;min-width:0'><div class='trip-nombre'>{nombre}</div>"
            f"<div class='trip-estado'><span class='led' style='--c:{COLOR[nivel]}'></span>{tx['estado'][nivel]}</div></div>"
            f"{tema.anillo(prep, 100, color_prep, '/100', 74)}</div>"
            f"<div title='{tx['apto'] if apto else tx['no_apto']}'>"
            f"{tema.sello(('✓ ' + tx['apto_c']) if apto else ('✕ ' + tx['no_apto_c']), COLOR['verde'] if apto else COLOR['rojo'])}"
            f"</div>"
            f"<table class='lecturas'>{filas_html}</table>"
            f"<div style='font-size:.68rem;color:#6f86a0;text-align:right;margin-top:4px'>± {tx['normal']}</div></div>",
            unsafe_allow_html=True)

    if ARCHIVO_VIVO.exists() and time.time() - ARCHIVO_VIVO.stat().st_mtime < 120:
        @st.fragment(run_every=2)
        def tarjeta_en_vivo():
            try:
                vivo = pd.read_csv(ARCHIVO_VIVO).tail(120)
            except Exception:
                vivo = pd.DataFrame()
            with st.container(border=True):
                st.markdown(f"**🔴 {tx['envivo']} · A5** &nbsp; <span style='opacity:0.7;font-size:0.85rem'>"
                            f"{tx['envivo_ayuda']}</span>", unsafe_allow_html=True)
                if vivo.empty or time.time() - ARCHIVO_VIVO.stat().st_mtime > 15:
                    st.info(tx["envivo_sin"])
                    return
                ult = vivo.iloc[-1]
                base_fc = vivo["fc"].head(20).mean()          # "su normal" = primeras 20 lecturas
                c1, c2, c3 = st.columns([1, 1, 3])
                c1.metric(nv["fc_lpm"], f"{ult['fc']:.0f}", f"{ult['fc'] - base_fc:+.0f}",
                          delta_color="off")
                c2.metric(nv["spo2_pct"], f"{ult['spo2']:.0f}")
                fig = go.Figure()
                fig.add_trace(go.Scatter(y=vivo["fc"], name=nv["fc_lpm"], line=dict(color=COLOR["rojo"])))
                fig.add_trace(go.Scatter(y=vivo["spo2"], name=nv["spo2_pct"], yaxis="y2", line=dict(color=tema.CIAN)))
                fig.update_layout(height=170, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
                                  yaxis2=dict(overlaying="y", side="right"))
                c3.plotly_chart(fig, width="stretch", theme=None)
                # Las mismas reglas que con la tripulación: ¿es la persona o el sensor?
                if ult["spo2"] < gen.SPO2_IMPOSIBLE and abs(ult["fc"] - base_fc) < 10:
                    st.warning(f"🔧 {msg['sensor_spo2'][0]}: {msg['sensor_spo2'][1]}")
                elif ult["spo2"] < gen.SPO2_MIN:
                    st.error(f"🧑‍🚀 {msg['spo2'][0]}: {msg['spo2'][1]}")
                elif ult["fc"] - base_fc > 20:
                    st.warning(f"🧑‍🚀 {nv['fc_lpm']} +{ult['fc'] - base_fc:.0f} {tx['normal']}")

        tarjeta_en_vivo()

    izq, der = st.columns([3, 2])
    with izq:
        st.markdown(tema.seccion(tx["alertas"], f"{len(alertas_hoy)}"), unsafe_allow_html=True)
        if alertas_hoy.empty:
            st.markdown(tema.tarjeta_alerta("✅", COLOR["verde"], tx["sin_alertas"], [], []), unsafe_allow_html=True)
        if apagon:
            st.warning(tx["apagon_aviso"])
        for _, a in alertas_hoy.sort_values("nivel", key=lambda s: s.map(ORDEN), ascending=False).iterrows():
            titulo, accion = msg[a["codigo"]]
            origen = ORIGEN[a["origen"]]
            if a["triaje"] == "tierra" and apagon:
                triaje, color_triaje = tx["en_cola"], COLOR["amarillo"]
                accion = PROTOCOLO_APAGON[idioma].get(a["codigo"], accion)
            elif a["triaje"] == "bordo":
                triaje, color_triaje = tx["bordo"], COLOR["verde"]
            else:
                triaje, color_triaje = tx["tierra_t"], "#6fb3ff"
            icono = "🔧" if a["origen"] == "sensor" else ("🔴" if a["nivel"] == "rojo" else "🟡")
            color_a = COLOR_SENSOR if a["origen"] == "sensor" else COLOR[a["nivel"]]
            detalle = f" · {tx['datos']}: {a['detalle']}" if isinstance(a["detalle"], str) and a["detalle"] else ""
            st.markdown(tema.tarjeta_alerta(
                icono, color_a, titulo,
                [tema.chip(origen, COLOR_ORIGEN[a["origen"]]), tema.chip(triaje, color_triaje)],
                [f"{tx['afecta']}: <b>{a['afectados']}</b>{detalle}", f"➡️ {tx['accion']}: {accion}"],
                critica=a["nivel"] == "rojo" and a["origen"] != "sensor"), unsafe_allow_html=True)
            with st.expander(f"🔎 {tx['porque']}"):
                st.markdown(f"**{tx['regla']}:** {REGLAS[idioma][a['codigo']]}")
                st.markdown(f"**{tx['evidencia']}:**\n" + "\n".join(f"- {l}" for l in texto_evidencia(a["evidencia"])))
                st.markdown(f"**{tx['fuentes']}:** " + " · ".join(f"[{n}]({u})" for n, u in FUENTES[a["codigo"]]))

        with st.expander(f"📡 {tx['tierra']}"):
            if apagon:
                cola = alertas[(alertas["dia_mision"] <= dia) & (alertas["triaje"] == "tierra")]
                st.caption(tx["cola"].format(n=len(cola)))
            else:
                st.caption(tx["retraso"].format(m=gen.RETRASO_TIERRA_MIN))
            lineas = [f"CREW HEALTH REPORT · {tx['dia']} {dia} ({fecha:%Y-%m-%d})"]
            for _, a in alertas_hoy.iterrows():
                lineas.append(f"[{a['nivel'].upper()}] {msg[a['codigo']][0]} — {a['afectados']}"
                              + (f" ({a['detalle']})" if isinstance(a["detalle"], str) and a["detalle"] else ""))
            for nombre, f in hoy.iterrows():
                lineas.append(f"{nombre}: {tx['preparacion']} {int(f['preparacion'])}/100 · "
                              f"{f['fc_lpm']} bpm · {f['temp_c']} °C · SpO2 {f['spo2_pct']}%")
            lineas.append(f"{tx['rad_acum']}: {amb['radiacion_acum_msv']:.1f} mSv ({amb['radiacion_pct_limite']:.1f}%) · "
                          f"CO2 {amb['co2_mmhg']:.1f} mmHg")
            st.code("\n".join(lineas), language=None)

    with der:
        st.markdown(tema.seccion(tx["ambiente"]), unsafe_allow_html=True)
        co2_alto = amb["co2_mmhg"] > gen.CO2_LIMITE
        extra_rad = amb["radiacion_msv"] - gen.RAD_FONDO
        st.markdown(
            "<div class='instrumentos'>"
            + tema.instrumento(tx["rad_hoy"], f"{amb['radiacion_msv']:.1f}", "mSv",
                               f"{extra_rad:+.1f} mSv vs. {gen.RAD_FONDO:g}",
                               color=COLOR["rojo"] if extra_rad > 0.5 else None)
            + tema.instrumento(tx["co2"], f"{amb['co2_mmhg']:.1f}", "mmHg",
                               ("🔴 " if co2_alto else "🟢 ") + tx["co2_lim"],
                               pct=amb["co2_mmhg"] / 6 * 100, color=COLOR["rojo"] if co2_alto else COLOR["verde"],
                               marca=gen.CO2_LIMITE / 6 * 100)
            + tema.instrumento(tx["temp_cab"], f"{amb['temp_cabina_c']:.1f}", "°C")
            + tema.instrumento(tx["rad_acum"], f"{amb['radiacion_acum_msv']:.0f}", "mSv",
                               f"{amb['radiacion_pct_limite']:.1f}% {tx['del_limite']}",
                               pct=amb["radiacion_pct_limite"], color=COLOR["amarillo"])
            + "</div>", unsafe_allow_html=True)

    st.markdown(tema.seccion(tx["tendencias"]), unsafe_allow_html=True)
    opciones = ["preparacion", "resp_rpm", "cefalea_0a10", "fc_lpm", "temp_c", "spo2_pct", "sueno_h",
                "reaccion_ms", "orina_l", "ejercicio_min", "perdida_osea_pct", "fatiga_0a10", "estres_0a10",
                "estres_termico_0a10", "co2_mmhg"]
    var = st.selectbox(tx["variable"], opciones, format_func=lambda v: nv[v])
    fig = go.Figure()
    for nombre, d in mision.groupby("astronauta"):
        fig.add_trace(go.Scatter(x=d["fecha"], y=d[var], name=nombre, mode="lines+markers",
                                 line=dict(color=COLOR_ASTRONAUTA[nombre], width=2), marker=dict(size=4)))
    st.plotly_chart(franjas(fig), width="stretch", theme=None)

    st.markdown(tema.seccion(tx["radiacion"]), unsafe_allow_html=True)
    r = mision.drop_duplicates("dia_mision")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=r["fecha"], y=r["radiacion_sin_refugio_msv"], name=tx["sin_ref"],
                         marker_color="rgba(255,90,95,.55)"))
    fig.add_trace(go.Bar(x=r["fecha"], y=r["radiacion_msv"], name=tx["con_ref"], marker_color=tema.CIAN))
    fig.update_layout(barmode="overlay", yaxis_title="mSv")
    st.plotly_chart(franjas(fig, 300), width="stretch", theme=None)
    ultimo = r.iloc[-1]
    evitada = ultimo["radiacion_acum_sin_refugio_msv"] - ultimo["radiacion_acum_msv"]
    st.metric(tx["ahorro"], f"{evitada:.0f} mSv",
              f"-{evitada / ultimo['radiacion_acum_sin_refugio_msv'] * 100:.0f}%", delta_color="inverse")

# ===========================================================================
# PESTAÑA 2: BITÁCORA DE LA MISIÓN
# ===========================================================================
with tab_bitacora:
    st.markdown(tema.seccion(tx["prep_titulo"]), unsafe_allow_html=True)
    fig = go.Figure()
    for nombre, d in mision.groupby("astronauta"):
        fig.add_trace(go.Scatter(x=d["fecha"], y=d["preparacion"], name=nombre, mode="lines",
                                 line=dict(color=COLOR_ASTRONAUTA[nombre], width=2)))
    fig.add_hline(y=70, line_dash="dot", line_color="rgba(255,255,255,.4)")
    st.plotly_chart(franjas(fig, 300), width="stretch", theme=None)

    st.markdown(tema.seccion(tx["bit_titulo"]), unsafe_allow_html=True)
    bit = alertas.copy()
    bit[tx["bit_dia"]] = bit["dia_mision"]
    bit[tx["bit_nivel"]] = bit["nivel"].map({"rojo": "🔴", "amarillo": "🟡"})
    bit[tx["bit_alerta"]] = bit["codigo"].map(lambda c: msg[c][0])
    bit[tx["bit_origen"]] = bit["origen"].map(ORIGEN)
    bit[tx["bit_afecta"]] = bit["afectados"]
    bit[tx["bit_triaje"]] = bit["triaje"].map({"bordo": tx["bordo"], "tierra": tx["tierra_t"]})
    bit[tx["bit_detalle"]] = bit["detalle"].fillna("").astype(str)
    st.dataframe(bit[[tx[k] for k in ["bit_dia", "bit_nivel", "bit_alerta", "bit_origen",
                                      "bit_afecta", "bit_triaje", "bit_detalle"]]],
                 hide_index=True, width="stretch", height=520)

    st.markdown(tema.seccion(tx["val_titulo"], tx["val_intro"]), unsafe_allow_html=True)
    v1, v2, v3, v4 = st.columns(4)
    r = val_resumen
    v1.metric(tx["val_eventos"], f"{r['eventos_detectados']}/{r['eventos']}")
    v2.metric(tx["val_primer"], f"{r['primer_dia']}/{r['eventos']}")
    v3.metric(tx["val_dias"], f"{r['dias_detectados']}/{r['dias_evento']}")
    v4.metric(tx["val_falsas"], f"{r['falsas_alarmas']}/{r['alertas']}")
    nombres_ev = {"tormenta": msg["tormenta"][0]}
    for e in gen.GUION:
        nombres_ev[e["evento"]] = e["es" if idioma == "Español" else "en"]
    vt = val_tabla.copy()
    vt[tx["val_evento"]] = vt["evento"].map(nombres_ev)
    vt[tx["val_afecta"]] = vt["afectados"]
    vt[tx["val_dias_t"]] = vt["dias"]
    vt[tx["val_det"]] = vt["dias_detectados"]
    vt[tx["val_1"]] = vt["primer_dia"].map({True: "✅", False: "❌"})
    st.dataframe(vt[[tx[k] for k in ["val_evento", "val_afecta", "val_dias_t", "val_det", "val_1"]]],
                 hide_index=True, width="stretch")

    if robustez is not None:
        st.markdown(f"**{tx['val_robust']}**")
        w1, w2, w3, w4 = st.columns(4)
        w1.metric(tx["val_recall"], f"{(robustez['dias_detectados'] / robustez['dias_evento']).mean() * 100:.1f} %")
        w2.metric(tx["val_prec"], f"{(1 - robustez['falsas_alarmas'] / robustez['alertas']).mean() * 100:.1f} %")
        w3.metric(tx["val_falsas_prom"], f"{robustez['falsas_alarmas'].mean():.1f}")
        w4.metric(tx["val_todos"], f"{(robustez['eventos_detectados'] == robustez['eventos']).sum()}/{len(robustez)}")

# ===========================================================================
# PESTAÑA 3: CÓMO FUNCIONA
# ===========================================================================
with tab_como, st.container(key="como"):
    if idioma == "Español":
        st.markdown("""
### El problema
En una misión a Marte, un mensaje a la Tierra tarda varios minutos y el médico no está a bordo. El reto de NASA pide un software que reúna indicadores de salud y permita a los astronautas **evaluar su estado y actuar**.

### Cómo funciona
1. **Datos:** sensores (pulso, SpO₂, temperatura, respiración, sueño), un check-in diario (dolor de cabeza, estrés), una prueba de reacción de 3 minutos (como la PVT de NASA), registros de agua y ejercicio, y los sensores de la nave (radiación, CO₂, temperatura).
2. **"Tu normal":** los primeros 7 días la app aprende los valores normales de cada astronauta. Después compara cada dato con *su* normal, no con un promedio general.
3. **¿Eres tú o es la nave?:** si 3 o más astronautas se salen de su normal en lo mismo a la vez, la causa es el **ambiente**; si le pasa a uno solo, es **esa persona**.
4. **Variables cruzadas:** la alerta no sale por un solo dato. Por ejemplo, pulso + temperatura → posible infección; poca orina + pérdida ósea → riesgo de cálculo renal.
5. **Acción y triaje:** cada alerta dice qué hacer y si se resuelve **a bordo** o conviene **consultar con la Tierra**, con un resumen listo para enviar.
6. **Índice de preparación (0–100):** resume el estado de cada astronauta y dice si está apto para tareas críticas, como una caminata espacial.
7. **¿O es el sensor?:** si un sensor marca algo grave pero el cuerpo no muestra ninguna señal (por ejemplo, CO₂ alto sin síntomas en nadie, o una SpO₂ imposible con pulso y respiración normales), la app sospecha del **sensor** y pide verificarlo antes de actuar.
8. **¿Por qué?:** cada alerta muestra la regla, los datos exactos que la dispararon y la fuente de NASA que la respalda.
9. **Modo apagón:** cuando Marte queda detrás del Sol no hay contacto con la Tierra durante dos a tres semanas. Con el interruptor, todo pasa a protocolos a bordo y los informes quedan en cola.
10. **Validación:** comparamos las alertas con lo que de verdad pasó en el guion, y repetimos la misión 30 veces con distinta variación aleatoria para medir aciertos y falsas alarmas (pestaña Bitácora).
11. **Sensor real (opcional):** un MAX30102 con un ESP32 envía pulso y SpO₂ reales, que aparecen como "A5 en vivo" y pasan por las mismas reglas.
13. **Modo juego · Misión Cóndor:** un juego narrativo (inspirado en *Papers, Please* y *Reigns*) con 4 días reales de la misión (9, 21, 26 y 29) y la llegada a Marte: cada tripulante va a la estación médica, se mide (tensiómetro, oxímetro, termómetro, glucómetro, sueño y ánimo), sube sus datos a VITA, sella si está apto y decide con tarjetas. VITA usa los mismos datos y alertas que el resto de la app.
12. **Modo astronauta:** cada astronauta ingresa sus datos (teclado, clics y cámara): **tu gemelo de salud** (cuerpo clickeable), **check-in** con los 6 indicadores que pide NASA (presión, pulso, glucosa, temperatura, sueño y ánimo) y guía "cómo medirlo", el minijuego **"Atrapa el meteorito"** (jugar = medir la reacción), **misiones del día** con racha y el **Escudo de la tripulación** (meta cooperativa), el **mensaje a la Tierra** que se ve viajar y la **visión** con cámara (SANS).

### Datos de NASA
- **NASA DONKI:** fechas reales de tormentas solares (mayo de 2024).
- **NASA-STD-3001:** límite de radiación de 600 mSv en la carrera; CO₂ máximo de 3 mmHg.
- **Programa de Investigación Humana de NASA:** riesgos de pérdida ósea (1–1,5 % al mes), cálculos renales, sueño (~6 h de promedio en la ISS), CO₂ y salud conductual.
- **Curiosity RAD:** 1,8 mSv por día en el viaje a Marte.

*Los datos fisiológicos son simulados con esos valores de referencia, porque los datos médicos de los astronautas no son públicos. En una misión real vendrían de los sensores.*
""")
    else:
        st.markdown("""
### The problem
On a Mars mission, a message to Earth takes several minutes and the flight surgeon is not on board. NASA's challenge asks for software that gathers health indicators and lets astronauts **evaluate their status and act**.

### How it works
1. **Data:** wearable sensors (heart rate, SpO₂, temperature, respiration, sleep), a daily check-in (headache, stress), a 3-minute reaction test (like NASA's PVT), water and exercise logs, and spacecraft sensors (radiation, CO₂, temperature).
2. **Personal baseline:** during the first 7 days the app learns each astronaut's normal values, then compares every reading with *their* normal, not a population average.
3. **Is it you or the spacecraft?** If 3 or more astronauts leave their baseline in the same variable at once, the cause is **environmental**; if only one does, it is **that person**.
4. **Cross-checked variables:** alerts never come from a single reading. E.g. heart rate + temperature → possible infection; low urine output + bone loss → kidney stone risk.
5. **Action and triage:** every alert says what to do and whether it is **handled on board** or should be **sent to Earth**, with a ready-made summary.
6. **Readiness index (0–100):** summarizes each astronaut's status and whether they are cleared for critical tasks such as a spacewalk.
7. **Or is it the sensor?** If a sensor reports something serious but the body shows no sign of it (e.g. high CO₂ with no symptoms in anyone, or an impossible SpO₂ with normal heart rate and breathing), the app suspects the **sensor** and asks to verify it before acting.
8. **Why?** Every alert shows its rule, the exact data that triggered it and the NASA source behind it.
9. **Blackout mode:** when Mars is behind the Sun there is no contact with Earth for two to three weeks. With the switch on, everything moves to on-board protocols and reports are queued.
10. **Validation:** we compare alerts with what really happened in the mission script, and rerun the mission 30 times with different random variation to measure hits and false alarms (Mission log tab).
11. **Real sensor (optional):** a MAX30102 with an ESP32 streams real heart rate and SpO₂, shown as "A5 live" and checked with the same rules.
13. **Game mode · Mission Condor:** a narrative game (inspired by *Papers, Please* and *Reigns*) with 4 real mission days (9, 21, 26 and 29) and the arrival at Mars: each crew member goes to the medical station, measures themselves (BP cuff, pulse oximeter, thermometer, glucose meter, sleep and mood), uploads the data to VITA, stamps whether they are cleared and decides with cards. VITA uses the same data and alerts as the rest of the app.
12. **Astronaut mode:** each astronaut enters their own data (keyboard, clicks and camera): **your health twin** (clickable body), a **check-in** with the 6 indicators NASA suggests (blood pressure, heart rate, blood sugar, temperature, sleep and mood) plus a "how to measure" guide, the **"Catch the meteor"** mini-game (playing = measuring reaction time), **daily missions** with a streak and the **Crew shield** (a cooperative goal), the **message to Earth** you can watch travel, and **vision** with a camera (SANS).

### NASA data
- **NASA DONKI:** real solar storm dates (May 2024).
- **NASA-STD-3001:** 600 mSv career radiation limit; 3 mmHg CO₂ limit.
- **NASA Human Research Program:** bone loss (1–1.5% per month), kidney stones, sleep (~6 h average on ISS), CO₂ and behavioral health risks.
- **Curiosity RAD:** 1.8 mSv per day during the cruise to Mars.

*Physiological data are simulated from these reference values because astronaut medical data are not public. In a real mission they would come from sensors.*
""")
