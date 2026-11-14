"""
MODO ASTRONAUTA - Crew Health Monitor
NASA Space Apps Challenge 2026

Lo que ve UN astronauta: su gemelo de salud (cuerpo clickeable), el check-in diario
(teclado y clics), el minijuego "Atrapa el meteorito" (prueba de reacción), las misiones
del día con racha y el Escudo de la tripulación, el mensaje a la Tierra y la visión (cámara).

Usa el MISMO cerebro que el Modo misión (generador.py).
"""

import json
import urllib.request
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import generador as gen
import tema

CARPETA = Path(__file__).parent
ARCHIVO_REGISTROS = CARPETA / "data" / "registros.csv"
CARPETA_VISION = CARPETA / "data" / "vision"
_meteorito = components.declare_component("meteorito", path=str(CARPETA / "componentes" / "meteorito"))

GRIS = "#8a96a8"
ESTACIONES = ["escaner", "checkin", "reaccion", "tierra", "vision", "logros"]

# ===========================================================================
# TEXTOS
# ===========================================================================
A = {
    "Español": dict(
        estaciones={"escaner": "🩻 Escáner", "checkin": "📝 Check-in", "reaccion": "☄️ Reacción",
                    "tierra": "📡 Tierra", "vision": "👁️ Visión", "logros": "🏅 Logros"},
        estacion="Estación", turno="Turno médico de hoy", credencial="Credencial de vuelo · tripulante",
        pasos_ci=[("❤️", "Corazón y presión", "Mide en reposo, sentado, antes de moverte."),
                  ("🌡️", "Cuerpo", "Temperatura, oxígeno, respiración y glucosa en ayunas."),
                  ("💧", "Rutina del día", "Sueño, hidratación y ejercicio."),
                  ("🧠", "Mente", "Cómo te sientes hoy. Es privado.")],
        paso="Tarjeta {i} de {n}", siguiente="Siguiente →", atras="← Atrás", transmitir="📡 Transmitir check-in",
        corregir="✏️ Corregir check-in", transmitido="Transmisión recibida",
        transmitido_sub="El sistema comparó tu check-in con tus valores normales.",
        entendido="✔ Entendido", recibido="✔ Recibido", sello_recibido="Recibido",
        escaner="Escáner biométrico", tu_normal="Tu normal", sin_jugar="Todavía no jugaste hoy. Toca «Empezar» en la pantalla del juego.",
        canal="Canal médico con la Tierra", silencio="Canal en silencio", hecho="hecho",
        quien="¿Quién eres?", hola="Hola, {a}. Este es tu chequeo del día {d}.",
        preparacion="Preparación", racha="Racha", puntos="Puntos de hoy", dias="días",
        gemelo="Tu gemelo de salud", gemelo_sub="Cada parte se pinta según cómo estás hoy comparado con tu normal.",
        toca="Toca una parte del cuerpo", que_hace="Qué hace", como_esta="Cómo está hoy", que_hacer="Qué hacer",
        todo_bien="Todo dentro de tu normal. ¡Sigue así!", como_medir="Cómo medirlo",
        checkin="Check-in de hoy", checkin_sub="Escribe lo que mediste. Los valores vienen precargados con los sensores; corrígelos si hace falta.",
        enviar="Enviar y evaluar", pa_sis="Presión sistólica (la de arriba)", pa_dia="Presión diastólica (la de abajo)",
        animo="¿Cómo te sientes hoy?", animo_ayuda="Es privado: solo lo ve el médico si tú lo envías.",
        sintomas="¿Tienes alguno de estos síntomas?", reaccion_juego="Reacción (del juego)",
        sin_juego="Juega 'Atrapa el meteorito' para medirla", resultado="Resultado de tu check-in",
        sin_alertas="✅ Todo dentro de tu normal. Buen trabajo cuidándote.",
        guardado="Check-in guardado", juego="☄️ Atrapa el meteorito",
        juego_sub="Una prueba de reacción como la que NASA usa para medir la concentración, convertida en juego. 5 meteoritos.",
        tu_reaccion="Tu reacción hoy", vs_normal="vs. tu normal", juego_lento="Más lento que tu normal: puede ser cansancio o falta de sueño.",
        juego_ok="Dentro de tu normal: tu concentración está bien.",
        misiones="🏅 Misiones de hoy", m_checkin="Check-in de salud", m_agua="Hidratación (≥ 2 L de orina)",
        m_ejercicio="Ejercicio (≥ 90 min)", m_juego="Atrapa el meteorito", escudo="Escudo de la tripulación",
        escudo_sub="Los cuatro suman: % de misiones cumplidas por toda la tripulación en los últimos 7 días.",
        insignias="Insignias", tierra="📡 Comunicación con la Tierra",
        en_camino="Informe en camino al médico · llega en ~{m} min", en_cola="Sin contacto (conjunción solar): el informe queda en cola",
        nada_tierra="Hoy no hay nada para consultar con la Tierra.", animacion="Animación acelerada: 1 segundo = 1 minuto real.",
        vision="👁️ Visión (SANS)", vision_sub="En misiones largas pueden cambiar los ojos y la visión (SANS). Esto no diagnostica: guarda tu registro y avisa si algo cambia.",
        camara="Foto del ojo con la cámara de la computadora", esp32="O desde la ESP32-CAM (dirección de captura)",
        capturar="Capturar desde ESP32-CAM", foto_base="Tu primera foto", foto_hoy="Hoy",
        amsler="Test de la cuadrícula: tapa un ojo y mira el punto del centro.",
        amsler_q="¿Ves líneas torcidas, borrosas o partes que faltan?", si="Sí", no="No",
        vision_ok="Sin cambios reportados.", error_cam="No se pudo conectar con la ESP32-CAM: {e}",
        partes={"cabeza": "🧠 Cabeza", "corazon": "❤️ Corazón", "pulmones": "🫁 Pulmones",
                "rinones": "💧 Riñones", "huesos": "🦴 Huesos", "cuerpo": "🌡️ Todo el cuerpo"},
        estado={"verde": "Bien", "amarillo": "Atención", "rojo": "Actuar ahora", "sensor": "Revisar sensor"},
        nombres_sintomas=["Dolor de cabeza", "Visión borrosa", "Mareo", "Náuseas", "Congestión"],
        insignia_nombres={"solar": "☀️ Escudo solar", "gota": "💧 Gota constante", "hueso": "🦴 Hueso de acero",
                          "meteoro": "☄️ Cazameteoritos", "equipo": "🤝 Tripulación unida"},
        insignia_desc={"solar": "Te protegiste en una tormenta solar real", "gota": "7 días seguidos bien hidratado",
                       "hueso": "7 días seguidos con ejercicio", "meteoro": "Jugaste la prueba de reacción hoy",
                       "equipo": "Escudo de la tripulación ≥ 80 %"},
        juego_textos=dict(titulo="Atrapa el meteorito", texto="Toca cada meteorito apenas aparezca. No toques antes: los meteoritos aparecen en momentos al azar.",
                          empezar="Empezar", ronda="Ronda", espera="espera…", resultado="Tu tiempo de reacción",
                          otra="Jugar otra vez", temprano="¡Muy pronto! Espera a que aparezca."),
    ),
    "English": dict(
        estaciones={"escaner": "🩻 Body scan", "checkin": "📝 Check-in", "reaccion": "☄️ Reaction",
                    "tierra": "📡 Earth", "vision": "👁️ Vision", "logros": "🏅 Rewards"},
        estacion="Station", turno="Today's medical shift", credencial="Flight credential · crew member",
        pasos_ci=[("❤️", "Heart and blood pressure", "Measure at rest, seated, before moving around."),
                  ("🌡️", "Body", "Temperature, oxygen, breathing and fasting blood sugar."),
                  ("💧", "Daily routine", "Sleep, hydration and exercise."),
                  ("🧠", "Mind", "How you feel today. It's private.")],
        paso="Card {i} of {n}", siguiente="Next →", atras="← Back", transmitir="📡 Transmit check-in",
        corregir="✏️ Correct check-in", transmitido="Transmission received",
        transmitido_sub="The system compared your check-in with your personal baseline.",
        entendido="✔ Acknowledge", recibido="✔ Acknowledged", sello_recibido="Received",
        escaner="Biometric scanner", tu_normal="Your baseline", sin_jugar="You haven't played today. Tap 'Start' on the game screen.",
        canal="Medical channel with Earth", silencio="Channel quiet", hecho="done",
        quien="Who are you?", hola="Hi, {a}. This is your check for day {d}.",
        preparacion="Readiness", racha="Streak", puntos="Today's points", dias="days",
        gemelo="Your health twin", gemelo_sub="Each body part is colored by how you are today compared with your own baseline.",
        toca="Tap a body part", que_hace="What it does", como_esta="How it is today", que_hacer="What to do",
        todo_bien="Everything within your baseline. Keep it up!", como_medir="How to measure it",
        checkin="Today's check-in", checkin_sub="Enter what you measured. Values are pre-filled from the sensors; correct them if needed.",
        enviar="Submit and assess", pa_sis="Systolic pressure (top number)", pa_dia="Diastolic pressure (bottom number)",
        animo="How do you feel today?", animo_ayuda="Private: the flight surgeon only sees it if you send it.",
        sintomas="Do you have any of these symptoms?", reaccion_juego="Reaction (from the game)",
        sin_juego="Play 'Catch the meteor' to measure it", resultado="Your check-in result",
        sin_alertas="✅ Everything within your baseline. Great job taking care of yourself.",
        guardado="Check-in saved", juego="☄️ Catch the meteor",
        juego_sub="A reaction test like the one NASA uses to measure alertness, turned into a game. 5 meteors.",
        tu_reaccion="Your reaction today", vs_normal="vs. your baseline", juego_lento="Slower than your baseline: it may be fatigue or lack of sleep.",
        juego_ok="Within your baseline: your alertness is fine.",
        misiones="🏅 Today's missions", m_checkin="Health check-in", m_agua="Hydration (≥ 2 L urine)",
        m_ejercicio="Exercise (≥ 90 min)", m_juego="Catch the meteor", escudo="Crew shield",
        escudo_sub="All four add up: % of missions completed by the whole crew over the last 7 days.",
        insignias="Badges", tierra="📡 Communication with Earth",
        en_camino="Report on its way to the flight surgeon · arrives in ~{m} min", en_cola="No contact (solar conjunction): report queued",
        nada_tierra="Nothing to consult with Earth today.", animacion="Sped-up animation: 1 second = 1 real minute.",
        vision="👁️ Vision (SANS)", vision_sub="On long missions the eyes and vision can change (SANS). This does not diagnose: it keeps your record and warns you if something changes.",
        camara="Eye photo with the computer camera", esp32="Or from the ESP32-CAM (capture address)",
        capturar="Capture from ESP32-CAM", foto_base="Your first photo", foto_hoy="Today",
        amsler="Grid test: cover one eye and look at the center dot.",
        amsler_q="Do you see wavy, blurry or missing lines?", si="Yes", no="No",
        vision_ok="No changes reported.", error_cam="Could not connect to the ESP32-CAM: {e}",
        partes={"cabeza": "🧠 Head", "corazon": "❤️ Heart", "pulmones": "🫁 Lungs",
                "rinones": "💧 Kidneys", "huesos": "🦴 Bones", "cuerpo": "🌡️ Whole body"},
        estado={"verde": "OK", "amarillo": "Watch", "rojo": "Act now", "sensor": "Check sensor"},
        nombres_sintomas=["Headache", "Blurred vision", "Dizziness", "Nausea", "Congestion"],
        insignia_nombres={"solar": "☀️ Solar shield", "gota": "💧 Steady drop", "hueso": "🦴 Steel bones",
                          "meteoro": "☄️ Meteor catcher", "equipo": "🤝 United crew"},
        insignia_desc={"solar": "You sheltered during a real solar storm", "gota": "7 days in a row well hydrated",
                       "hueso": "7 days in a row with exercise", "meteoro": "You played the reaction test today",
                       "equipo": "Crew shield ≥ 80 %"},
        juego_textos=dict(titulo="Catch the meteor", texto="Tap each meteor as soon as it appears. Don't tap early: meteors appear at random times.",
                          empezar="Start", ronda="Round", espera="wait…", resultado="Your reaction time",
                          otra="Play again", temprano="Too early! Wait for it to appear."),
    ),
}

# Qué hace cada parte del cuerpo y qué variables y alertas le corresponden
PARTES = {
    "cabeza": dict(vars=["reaccion_ms", "cefalea_0a10", "animo_1a5", "sueno_h"],
                   alertas={"fatiga", "animo", "vision", "co2", "sensor_co2"}),
    "corazon": dict(vars=["fc_lpm", "pas_mmhg", "pad_mmhg"], alertas={"presion", "infeccion"}),
    "pulmones": dict(vars=["resp_rpm", "spo2_pct"], alertas={"spo2", "sensor_spo2", "co2", "sensor_co2"}),
    "rinones": dict(vars=["orina_l"], alertas={"renal"}),
    "huesos": dict(vars=["perdida_osea_pct", "ejercicio_min"], alertas={"ejercicio"}),
    "cuerpo": dict(vars=["temp_c", "glucosa_mgdl"], alertas={"infeccion", "glucosa", "tormenta"}),
}
QUE_HACE = {
    "Español": {
        "cabeza": "Tu cerebro maneja la concentración, el sueño y el ánimo. En el espacio lo afectan el aislamiento, el CO₂ alto y dormir poco.",
        "corazon": "Bombea la sangre. Sin gravedad, la sangre sube hacia el pecho y la presión suele bajar unos 10 mmHg.",
        "pulmones": "Llevan oxígeno a la sangre y sacan el CO₂. Si el aire de la nave tiene mucho CO₂, respiras más rápido.",
        "rinones": "Filtran la sangre. Con la pérdida ósea sale más calcio; si tomas poca agua, pueden formarse cálculos.",
        "huesos": "Sostienen tu cuerpo. Sin gravedad pierden ~1–1,5 % de densidad por mes; el ejercicio lo frena.",
        "cuerpo": "La temperatura, el azúcar en sangre y la radiación afectan a todo el cuerpo.",
    },
    "English": {
        "cabeza": "Your brain handles alertness, sleep and mood. In space it is affected by isolation, high CO₂ and too little sleep.",
        "corazon": "It pumps blood. Without gravity, blood shifts toward the chest and blood pressure usually drops about 10 mmHg.",
        "pulmones": "They bring oxygen into the blood and remove CO₂. If the cabin air has too much CO₂, you breathe faster.",
        "rinones": "They filter the blood. Bone loss releases more calcium; with too little water, stones can form.",
        "huesos": "They hold your body up. Without gravity they lose ~1–1.5 % density per month; exercise slows it down.",
        "cuerpo": "Temperature, blood sugar and radiation affect the whole body.",
    },
}
# Guía "cómo medirlo" (se muestra como ayuda en cada campo y en el gemelo)
GUIA = {
    "Español": {
        "pas_mmhg": "1) Quédate quieto 5 minutos. 2) Brazalete en el brazo, a la altura del corazón. 3) No hables mientras mide. 4) Anota los dos números: el de arriba (sistólica) y el de abajo (diastólica).",
        "pad_mmhg": "Es el número de abajo del tensiómetro. Normal: menos de 80.",
        "fc_lpm": "Al despertar, antes de moverte: lo da el reloj o el oxímetro. O cuenta los latidos en la muñeca durante 30 s y multiplica por 2.",
        "glucosa_mgdl": "En ayunas: limpia el dedo, pincha el costado de la yema con la lanceta, pon la gota en la tira del glucómetro y anota el número.",
        "temp_c": "Termómetro bajo la lengua, boca cerrada, 1 minuto. En vuelos largos tu normal puede estar cerca de 37 °C.",
        "spo2_pct": "Oxímetro en el dedo, mano quieta y caliente. Espera 30 s a que el número se estabilice.",
        "resp_rpm": "En reposo, cuenta cuántas veces sube tu pecho en 30 s y multiplica por 2.",
        "sueno_h": "Lo registra el reloj de muñeca (como el estudio ARCHeR de NASA) o anota a qué hora te dormiste y despertaste.",
        "orina_l": "Litros de orina del día. Meta de NASA: 2,5–3 L. Si no la mides, usa el agua que tomaste como guía.",
        "ejercicio_min": "Minutos en la cinta, la bicicleta o el equipo de resistencia. En la ISS se hacen unas 2 h al día.",
        "cefalea_0a10": "0 = nada, 10 = el peor dolor que puedas imaginar.",
        "animo_1a5": "Elige la carita que mejor describe cómo te sientes hoy.",
        "reaccion_ms": "Juega 'Atrapa el meteorito': mide tu tiempo de reacción como la prueba PVT de NASA.",
        "perdida_osea_pct": "Se estima con los días en misión y tu ejercicio; a bordo no hay escáner de huesos.",
    },
    "English": {
        "pas_mmhg": "1) Stay still for 5 minutes. 2) Cuff on the arm, at heart level. 3) Don't talk while it measures. 4) Log both numbers: top (systolic) and bottom (diastolic).",
        "pad_mmhg": "The bottom number on the monitor. Normal: below 80.",
        "fc_lpm": "On waking, before moving: read it from the watch or the oximeter. Or count wrist beats for 30 s and multiply by 2.",
        "glucosa_mgdl": "While fasting: clean your finger, prick the side of the fingertip, put the drop on the meter strip and log the number.",
        "temp_c": "Thermometer under the tongue, mouth closed, 1 minute. On long flights your baseline may be close to 37 °C.",
        "spo2_pct": "Oximeter on the finger, hand still and warm. Wait 30 s for the number to settle.",
        "resp_rpm": "At rest, count how many times your chest rises in 30 s and multiply by 2.",
        "sueno_h": "Logged by the wrist watch (like NASA's ARCHeR study), or note when you fell asleep and woke up.",
        "orina_l": "Liters of urine per day. NASA target: 2.5–3 L. If not measured, use the water you drank as a guide.",
        "ejercicio_min": "Minutes on the treadmill, bike or resistance device. On the ISS crews do about 2 h a day.",
        "cefalea_0a10": "0 = none, 10 = the worst pain you can imagine.",
        "animo_1a5": "Pick the face that best describes how you feel today.",
        "reaccion_ms": "Play 'Catch the meteor': it measures your reaction time like NASA's PVT.",
        "perdida_osea_pct": "Estimated from mission days and your exercise; there is no bone scanner on board.",
    },
}
CARITAS = ["😫", "😟", "😐", "🙂", "😄"]


# ===========================================================================
# AYUDANTES
# ===========================================================================
def _estado_variable(var, valor, base_astro):
    """Color de una variable: comparada con su normal (si aplica) o con su umbral fijo."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "verde"
    if var in gen.VARIABLES:
        desv = max(float(base_astro[(var, "std")]), gen.PISO[var])
        z = (float(valor) - float(base_astro[(var, "mean")])) / desv
        malo = {"sueno_h": -z, "spo2_pct": -z}.get(var, z)
        return "amarillo" if malo >= gen.UMBRAL else "verde"
    if var == "pas_mmhg":
        return "rojo" if valor >= gen.PAS_MUY_ALTA else ("amarillo" if valor >= gen.PAS_ALTA or valor < gen.PAS_BAJA else "verde")
    if var == "pad_mmhg":
        return "rojo" if valor >= gen.PAD_MUY_ALTA else ("amarillo" if valor >= gen.PAD_ALTA or valor < gen.PAD_BAJA else "verde")
    if var == "glucosa_mgdl":
        return "rojo" if valor < gen.GLU_BAJA or valor >= gen.GLU_MUY_ALTA else ("amarillo" if valor >= gen.GLU_ALTA else "verde")
    if var == "orina_l":
        return "amarillo" if valor < gen.ORINA_MIN else "verde"
    if var == "ejercicio_min":
        return "amarillo" if valor < gen.EJERCICIO_MIN else "verde"
    if var == "animo_1a5":
        return "amarillo" if valor <= 2 else "verde"
    return "verde"


def _nivel_parte(parte, alertas_lista, valores, base_astro):
    """Nivel de cada parte del cuerpo según sus alertas (y sus variables)."""
    orden = {"verde": 0, "sensor": 1, "amarillo": 2, "rojo": 3}
    nivel = "verde"
    for a in alertas_lista:
        if a["codigo"] in PARTES[parte]["alertas"]:
            n = "sensor" if a["origen"] == "sensor" else a["nivel"]
            nivel = max(nivel, n, key=orden.get)
    for v in PARTES[parte]["vars"]:
        nivel = max(nivel, _estado_variable(v, valores.get(v), base_astro), key=orden.get)
    return nivel


def _svg_gemelo(niveles, seleccion, color):
    """Dibuja la silueta del astronauta (holograma); cada parte con el color de su estado."""
    c = dict(color, sensor=GRIS)

    def estilo(parte, opacidad=0.35):
        borde = 3 if parte == seleccion else 1.5
        clase = " class='gem-sel'" if parte == seleccion else ""
        return (f"fill='{c[niveles[parte]]}' fill-opacity='{opacidad}' stroke='{c[niveles[parte]]}' "
                f"stroke-width='{borde}' filter='url(#brillo)'{clase}")

    huesos = estilo("huesos", 0.18)
    return f"""
<svg viewBox='0 0 240 340' width='100%' style='max-width:300px;display:block;margin:auto'>
  <defs><radialGradient id='visor' cx='40%' cy='35%'><stop offset='0%' stop-color='#ffffff' stop-opacity='0.9'/>
  <stop offset='100%' stop-color='#9fb3d9' stop-opacity='0.2'/></radialGradient>
  <filter id='brillo' x='-30%' y='-30%' width='160%' height='160%'><feGaussianBlur stdDeviation='2.2' result='b'/>
  <feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge></filter></defs>
  <ellipse cx='120' cy='330' rx='78' ry='7' fill='#3ee0ff' fill-opacity='0.16' stroke='#3ee0ff' stroke-opacity='0.35'/>
  <circle cx='120' cy='52' r='38' fill='none' stroke='#7fb8d8' stroke-opacity='0.75' stroke-width='2.5'/>
  <circle cx='120' cy='52' r='30' {estilo('cabeza', 0.45)}/>
  <ellipse cx='110' cy='44' rx='12' ry='8' fill='url(#visor)'/>
  <rect x='58' y='100' width='22' height='110' rx='11' {huesos}/>
  <rect x='160' y='100' width='22' height='110' rx='11' {huesos}/>
  <rect x='82' y='94' width='76' height='130' rx='22' {estilo('cuerpo', 0.12)}/>
  <ellipse cx='103' cy='132' rx='13' ry='20' {estilo('pulmones', 0.45)}/>
  <ellipse cx='137' cy='132' rx='13' ry='20' {estilo('pulmones', 0.45)}/>
  <path d='M120 150 c-10 -14 -26 -2 -14 10 l14 12 l14 -12 c12 -12 -4 -24 -14 -10z' {estilo('corazon', 0.7)}/>
  <ellipse cx='106' cy='192' rx='8' ry='11' {estilo('rinones', 0.55)}/>
  <ellipse cx='134' cy='192' rx='8' ry='11' {estilo('rinones', 0.55)}/>
  <rect x='88' y='228' width='28' height='96' rx='12' {huesos}/>
  <rect x='124' y='228' width='28' height='96' rx='12' {huesos}/>
</svg>"""


def _clave_acuse(a, c):
    return f"{c['dia']}|{a['afectados']}|{a['codigo']}"


def _tarjeta_alerta(a, c, idx):
    """Tarjeta de alerta (una decisión por tarjeta): qué pasa, de dónde viene, qué hacer y botón para confirmar."""
    T = A[c["idioma"]]
    t = c["msg"][a["codigo"]]
    titulo, accion = t
    if a["triaje"] == "tierra" and c["apagon"]:
        accion = c["protocolo"].get(a["codigo"], accion)
        triaje, color_triaje = c["tx"]["en_cola"], c["color"]["amarillo"]
    elif a["triaje"] == "bordo":
        triaje, color_triaje = c["tx"]["bordo"], c["color"]["verde"]
    else:
        triaje, color_triaje = c["tx"]["tierra_t"], "#6fb3ff"
    color = GRIS if a["origen"] == "sensor" else c["color"][a["nivel"]]
    icono = "🔧" if a["origen"] == "sensor" else ("🔴" if a["nivel"] == "rojo" else "🟡")
    acuses = st.session_state.setdefault("acuses", set())
    recibida = _clave_acuse(a, c) in acuses
    st.markdown(tema.tarjeta_alerta(
        icono, color, titulo,
        [tema.chip(c["origen"][a["origen"]], c["color_origen"][a["origen"]]), tema.chip(triaje, color_triaje)],
        [f"➡️ {accion}"], critica=a["nivel"] == "rojo" and a["origen"] != "sensor",
        recibida_txt=T["sello_recibido"] if recibida else None), unsafe_allow_html=True)
    b1, b2 = st.columns([3, 5])
    with b1:
        if recibida:
            st.button(T["recibido"], key=f"ack_{a['codigo']}_{idx}", disabled=True, width="stretch")
        elif st.button(T["entendido"], key=f"ack_{a['codigo']}_{idx}", width="stretch"):
            acuses.add(_clave_acuse(a, c))
            st.rerun()
    with b2, st.expander(f"🔎 {c['tx']['porque']}", expanded=False):
        st.markdown(f"**{c['tx']['regla']}:** {c['reglas'][a['codigo']]}")
        lineas = c["texto_evidencia"](a["evidencia"])
        if lineas:
            st.markdown("\n".join(f"- {l}" for l in lineas))
        st.markdown(f"**{c['tx']['fuentes']}:** " + " · ".join(f"[{n}]({u})" for n, u in c["fuentes"][a["codigo"]]))


def _mensaje_tierra(minutos, en_cola, texto, pie):
    """Animación del informe viajando de la nave a la Tierra (1 s = 1 min real)."""
    dur = max(3, min(minutos, 22))
    punto = ("animation: latido 1.2s ease-in-out infinite; left: 9%;" if en_cola
             else f"animation: viaje {dur}s linear forwards;")
    llegada = "" if en_cola else f"animation: llegada 1.2s {dur}s ease-out 3;"
    html = f"""
<link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@600&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<div class="canal">
  <div class="cab"><span class="led"></span>EARTH CONTROL · {texto}</div>
  <div class="nave">🛰️</div><div class="tierra">🌍<span class="onda" style="{llegada}"></span></div>
  <div class="ruta"></div>
  <div class="paquete" style="{punto}"></div>
  <div class="pie">{pie}</div>
</div>
<style>
  body {{ margin: 0; }}
  .canal {{ font-family: 'JetBrains Mono', monospace; position: relative; height: 122px; border-radius: 14px; overflow: hidden; color: #d9e6f5;
           background: radial-gradient(ellipse at 85% 50%, rgba(47,123,255,.25), transparent 60%),
                       linear-gradient(rgba(98,180,220,.06) 1px, transparent 1px) 0 0/22px 22px,
                       linear-gradient(90deg, rgba(98,180,220,.06) 1px, transparent 1px) 0 0/22px 22px, #06101f;
           border: 1px solid rgba(98,180,220,.25); }}
  .cab {{ position: absolute; top: 10px; left: 14px; right: 14px; font-family: 'Chakra Petch', sans-serif; font-size: 13px;
          letter-spacing: .06em; color: #9fe9ff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .led {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: {'#ffb547' if en_cola else '#35d49a'};
          box-shadow: 0 0 8px {'#ffb547' if en_cola else '#35d49a'}; margin-right: 8px; animation: latido 1.6s infinite; }}
  .nave, .tierra {{ position: absolute; top: 48px; font-size: 30px; }}
  .nave {{ left: 3%; }} .tierra {{ right: 3%; }}
  .onda {{ position: absolute; inset: -6px; border-radius: 50%; border: 2px solid #3ee0ff; opacity: 0; }}
  .ruta {{ position: absolute; left: 12%; right: 12%; top: 66px; border-top: 2px dashed rgba(111,180,230,.45); }}
  .paquete {{ position: absolute; top: 59px; width: 14px; height: 14px; border-radius: 50%; background: #ffb547;
              box-shadow: 0 0 12px #ffb547, -18px 0 14px -4px rgba(255,181,71,.5), -34px 0 14px -6px rgba(255,181,71,.25); }}
  .pie {{ position: absolute; bottom: 8px; width: 100%; text-align: center; font-size: 11px; color: #8aa0b8; }}
  @keyframes viaje {{ from {{ left: 12%; }} to {{ left: 86%; }} }}
  @keyframes latido {{ 0%,100% {{ transform: scale(1); opacity: 1; }} 50% {{ transform: scale(1.4); opacity: .6; }} }}
  @keyframes llegada {{ from {{ transform: scale(.6); opacity: .9; }} to {{ transform: scale(1.8); opacity: 0; }} }}
</style>"""
    # st.iframe reemplaza a components.html en las versiones nuevas de Streamlit
    if hasattr(st, "iframe"):
        st.iframe(html, height=128)
    else:
        components.html(html, height=128)


def _misiones(mision, astro, dia, registros, juegos):
    """Misiones cumplidas por astronauta y día. Los días anteriores salen de los datos de la misión;
    hoy cuenta lo que el astronauta hizo en la app."""
    def de_fila(f, a, d):
        hoy = d == dia
        return dict(
            checkin=(a, d) in registros if hoy else True,
            agua=f["orina_l"] >= 2.0,
            ejercicio=f["ejercicio_min"] >= 90,
            juego=(a, d) in juegos if hoy else True,
        )
    tabla = {}
    for _, f in mision[mision["dia_mision"] <= dia].iterrows():
        tabla[(f["astronauta"], int(f["dia_mision"]))] = de_fila(f, f["astronauta"], int(f["dia_mision"]))
    if (astro, dia) in registros:     # el check-in de hoy reemplaza los datos simulados
        v = registros[(astro, dia)]["valores"]
        tabla[(astro, dia)].update(agua=v["orina_l"] >= 2.0, ejercicio=v["ejercicio_min"] >= 90)
    return tabla


PUNTOS = {"checkin": 10, "agua": 10, "ejercicio": 20, "juego": 10}


# ===========================================================================
# PANTALLA
# ===========================================================================
def mostrar(c):
    idioma, tx = c["idioma"], c["tx"]
    T = A[idioma]
    mision, dia, base = c["mision"], c["dia"], c["base"]
    color = dict(c["color"], sensor=GRIS)
    registros = st.session_state.setdefault("registros", {})
    juegos = st.session_state.setdefault("juegos", {})
    vision = st.session_state.setdefault("vision", {})

    # ===================== CREDENCIAL (¿quién es?) =====================
    with st.container(key="credencial"):
        cred, kpis = st.columns([4, 7], vertical_alignment="center", gap="medium")
        with cred:
            lugar_credencial = st.empty()
            astros = list(gen.TRIPULACION)
            inicial = st.query_params.get("astro", "A2")
            astro = st.segmented_control(T["quien"], astros, default=inicial if inicial in astros else "A2",
                                         key="astro_sel") or "A2"
    base_astro = base.loc[astro]
    fila = mision[(mision["dia_mision"] == dia) & (mision["astronauta"] == astro)].iloc[0]

    # Valores de hoy: el check-in si existe; si no, lo que dicen los sensores (datos de la misión)
    if (astro, dia) in registros:
        valores = dict(registros[(astro, dia)]["valores"])
        alertas_lista = registros[(astro, dia)]["alertas"]
    else:
        valores = {k: fila[k] for k in fila.index}
        alertas_lista = [a for _, a in c["alertas"][c["alertas"]["dia_mision"] == dia].iterrows()
                         if astro in str(a["afectados"])]
        alertas_lista = [dict(a) for a in alertas_lista]
    if (astro, dia) in juegos:
        valores["reaccion_ms"] = juegos[(astro, dia)]["ms"]

    # Índice de preparación con los valores de hoy
    fila_hoy = dict(fila); fila_hoy.update(valores)
    prep = int(gen.indice_preparacion(pd.concat([mision, pd.DataFrame([fila_hoy])], ignore_index=True)).iloc[-1])

    # Misiones, racha y escudo
    tabla_m = _misiones(mision, astro, dia, registros, juegos)
    hechas_hoy = tabla_m[(astro, dia)]
    puntos_hoy = sum(PUNTOS[k] for k, ok in hechas_hoy.items() if ok)
    racha = 0
    for d in range(dia, 0, -1):
        if all(tabla_m[(astro, d)].values()):
            racha += 1
        elif d == dia:
            continue          # hoy todavía puede completarse
        else:
            break
    ultimos = [v for (a, d), v in tabla_m.items() if d > dia - 7]
    escudo = round(100 * sum(sum(v.values()) for v in ultimos) / max(1, 4 * len(ultimos)))

    # Apto para tareas críticas: la misma regla del Modo misión (≥ 70 y sin alerta roja de salud)
    rojo_salud = any(a["nivel"] == "rojo" and a["origen"] != "sensor" for a in alertas_lista)
    apto = prep >= 70 and not rojo_salud
    color_prep = color["verde"] if prep >= 70 else (color["amarillo"] if prep >= 45 else color["rojo"])

    lugar_credencial.markdown(
        f"<div class='credencial entrar'><div class='cred-foto' style='--a:{c['color_astronauta'][astro]}'>🧑‍🚀</div>"
        f"<div><div class='cred-id'>{T['credencial']}</div><div class='cred-nombre'>{astro}</div>"
        f"<div class='cred-hola'>{T['hola'].format(a=astro, d=dia)}</div></div></div>", unsafe_allow_html=True)
    kpis.markdown(
        f"<div class='kpis entrar-2'>"
        f"<div class='kpi kpi-prep'>{tema.anillo(prep, 100, color_prep, '/100', 84)}"
        f"<div><div class='inst-etq'>{T['preparacion']}</div><div style='margin:8px 0 6px'>"
        f"{tema.sello(('✓ ' + tx['apto_c']) if apto else ('✕ ' + tx['no_apto_c']), color['verde'] if apto else color['rojo'])}"
        f"</div><div style='font-size:.72rem;color:#8aa0b8;line-height:1.25'>{tx['apto'] if apto else tx['no_apto']}</div></div></div>"
        f"<div class='kpi'><div class='inst-etq'>{T['racha']}</div><div class='kpi-val'>🔥 {racha}<small> {T['dias']}</small></div></div>"
        f"<div class='kpi'><div class='inst-etq'>{T['puntos']}</div><div class='kpi-val'>{puntos_hoy}<small>/50</small></div>"
        f"{tema.barra(puntos_hoy / 50 * 100)}</div>"
        f"<div class='kpi'><div class='inst-etq'>{T['escudo']}</div><div class='kpi-val'>🛡️ {escudo}<small>%</small></div>"
        f"{tema.barra(escudo, color['verde'])}</div></div>", unsafe_allow_html=True)

    # ===================== PROGRESO DEL TURNO =====================
    nombres = {"checkin": T["m_checkin"], "agua": T["m_agua"], "ejercicio": T["m_ejercicio"], "juego": T["m_juego"]}
    hechas = sum(hechas_hoy.values())
    st.markdown(tema.seccion(T["turno"], f"{hechas}/4 · {puntos_hoy}/50 pts"), unsafe_allow_html=True)
    st.markdown("<div class='turno entrar-3'>" + "".join(
        f"<div class='paso {'hecho' if ok else ''}'><div class='paso-n'>{i + 1:02d}"
        f"{' · ' + T['hecho'] if ok else ''}</div><div class='paso-t'>{'✅' if ok else '⬜'} {nombres[k]}</div>"
        f"<div class='paso-p'>+{PUNTOS[k]}</div></div>"
        for i, (k, ok) in enumerate(hechas_hoy.items())) + "</div>", unsafe_allow_html=True)

    # ===================== ESTACIONES =====================
    acuses = st.session_state.setdefault("acuses", set())
    pendientes = sum(1 for a in alertas_lista if _clave_acuse(a, c) not in acuses)
    a_tierra = [a for a in alertas_lista if a["triaje"] == "tierra"]

    def etiqueta(e):
        txt = T["estaciones"][e]
        if e == "escaner" and pendientes:
            txt += f" · {pendientes}"
        if (e == "checkin" and (astro, dia) in registros) or (e == "reaccion" and (astro, dia) in juegos):
            txt += " ✓"
        if e == "tierra" and a_tierra:
            txt += f" · {len(a_tierra)}"
        return txt

    est_inicial = st.query_params.get("estacion", "escaner")
    with st.container(key="selector_est"):
        estacion = st.segmented_control(T["estacion"], ESTACIONES, format_func=etiqueta, key="estacion",
                                        default=est_inicial if est_inicial in ESTACIONES else "escaner",
                                        label_visibility="collapsed") or "escaner"

    # ----------------------------- ESCÁNER (gemelo de salud) -----------------------------
    if estacion == "escaner":
        with st.container(key="est_escaner"):
            niveles = {p: _nivel_parte(p, alertas_lista, valores, base_astro) for p in PARTES}
            orden = {"verde": 0, "sensor": 1, "amarillo": 2, "rojo": 3}
            peor = max(PARTES, key=lambda p: orden[niveles[p]])
            izq, der = st.columns([5, 6], gap="large")
            with izq:
                lugar_svg = st.empty()
                sel = st.pills(T["toca"], list(PARTES), default=peor, key=f"parte_{astro}_{dia}",
                               format_func=lambda p: f"{T['partes'][p]}") or peor
                st.caption(T["gemelo_sub"])
                leyenda = "".join(tema.chip(T["estado"][n], color[n]) for n in ["verde", "amarillo", "rojo", "sensor"])
                lugar_svg.markdown(
                    f"<div class='escaner esquinas'><div class='panel-cab'><span>{T['escaner']} · {astro}</span>"
                    f"<span>{T['gemelo']}</span></div>{_svg_gemelo(niveles, sel, c['color'])}"
                    f"<div class='leyenda'>{leyenda}</div></div>", unsafe_allow_html=True)
            with der:
                col = color[niveles[sel]]
                filas = ""
                for v in PARTES[sel]["vars"]:
                    val = valores.get(v)
                    if val is None or (isinstance(val, float) and pd.isna(val)):
                        continue
                    est = _estado_variable(v, val, base_astro)
                    normal = (f"{tx['su_normal']} {float(base_astro[(v, 'mean')]):.1f}" if v in gen.VARIABLES else "")
                    txt = CARITAS[int(val) - 1] if v == "animo_1a5" else f"{float(val):g}"
                    filas += (f"<div class='lectura'><span class='pt' style='--c:{color[est]}'></span>"
                              f"<span class='nm'>{c['nv'].get(v, v)}<small>{normal}</small></span>"
                              f"<span class='vl'>{txt}</span></div>")
                st.markdown(
                    f"<div class='panel entrar' style='border-color:color-mix(in srgb, {col} 45%, transparent)'>"
                    f"<div class='dossier-cab'><span class='dossier-t'>{T['partes'][sel]}</span>"
                    f"{tema.sello(T['estado'][niveles[sel]], col)}</div>"
                    f"<div style='font-size:.88rem;color:#b3c4d8;margin:8px 0 12px'><b>{T['que_hace']}:</b> "
                    f"{QUE_HACE[idioma][sel]}</div><div class='panel-cab'><span>{T['como_esta']}</span></div>{filas}</div>",
                    unsafe_allow_html=True)
                propias = [a for a in alertas_lista if a["codigo"] in PARTES[sel]["alertas"]]
                st.markdown(tema.seccion(T["que_hacer"]), unsafe_allow_html=True)
                if propias:
                    for i, a in enumerate(propias):
                        _tarjeta_alerta(a, c, i)
                else:
                    st.markdown(tema.tarjeta_alerta("✅", color["verde"], T["todo_bien"], [], []), unsafe_allow_html=True)
                with st.expander(f"📖 {T['como_medir']}"):
                    for v in PARTES[sel]["vars"]:
                        st.markdown(f"**{c['nv'].get(v, v)}:** {GUIA[idioma][v]}")

    # ----------------------------- CHECK-IN (una tarjeta por paso) -----------------------------
    elif estacion == "checkin":
        with st.container(key="est_checkin"):
            clave_b, clave_p, clave_e = f"borrador_{astro}_{dia}", f"paso_{astro}_{dia}", f"editar_{astro}_{dia}"
            if (astro, dia) in registros and not st.session_state.get(clave_e):
                if st.session_state.pop(f"transmitido_{astro}_{dia}", False):
                    st.toast(T["guardado"], icon="📡")
                    st.markdown(f"<div class='transmision entrar'><div class='ondas'>📡</div>"
                                f"<div class='tt'>{T['transmitido']}</div><div class='apagado' style='font-size:.85rem'>"
                                f"{T['transmitido_sub']}</div></div>", unsafe_allow_html=True)
                st.markdown(tema.seccion(T["resultado"]), unsafe_allow_html=True)
                propias = [a for a in registros[(astro, dia)]["alertas"]]
                if not [a for a in propias if a["codigo"] not in {"tormenta", "co2", "sensor_co2", "ambiente"}]:
                    st.markdown(tema.tarjeta_alerta("✅", color["verde"], T["sin_alertas"], [], []), unsafe_allow_html=True)
                for i, a in enumerate(propias):
                    _tarjeta_alerta(a, c, 100 + i)
                if st.button(T["corregir"], key=f"corregir_{astro}_{dia}"):
                    st.session_state[clave_e] = True
                    st.session_state.pop(clave_b, None)
                    st.session_state[clave_p] = 0
                    st.rerun()
            else:
                if clave_b not in st.session_state:
                    st.session_state[clave_b] = dict(
                        pas_mmhg=int(valores["pas_mmhg"]), pad_mmhg=int(valores["pad_mmhg"]), fc_lpm=int(valores["fc_lpm"]),
                        glucosa_mgdl=int(valores["glucosa_mgdl"]), temp_c=float(valores["temp_c"]),
                        spo2_pct=float(valores["spo2_pct"]), sueno_h=float(valores["sueno_h"]),
                        orina_l=float(valores["orina_l"]), ejercicio_min=int(valores["ejercicio_min"]),
                        resp_rpm=float(valores["resp_rpm"]), cefalea_0a10=int(round(float(valores["cefalea_0a10"]))),
                        animo_1a5=int(valores["animo_1a5"]), sint=[])
                b = st.session_state[clave_b]
                paso = st.session_state.get(clave_p, 0)
                n_pasos = len(T["pasos_ci"])
                ico, titulo, sub = T["pasos_ci"][paso]
                g = GUIA[idioma]
                k = lambda v: f"ci_{astro}_{dia}_{v}"
                enviado = False
                with st.container(key="carta"):
                    st.markdown(
                        f"<div class='entrar'><div class='puntos-pasos'>"
                        + "".join(f"<i class='{'si' if i <= paso else ''}'></i>" for i in range(n_pasos))
                        + f"</div><div class='carta-cab'><div class='carta-ico'>{ico}</div><div>"
                        f"<div class='carta-n'>{T['checkin']} · {T['paso'].format(i=paso + 1, n=n_pasos)}</div>"
                        f"<div class='carta-t'>{titulo}</div><div class='carta-s'>{sub}</div></div></div></div>",
                        unsafe_allow_html=True)
                    with st.form(f"checkin_{astro}_{dia}_{paso}", border=False):
                        nuevo = {}
                        if paso == 0:
                            a1, a2 = st.columns(2)
                            nuevo["pas_mmhg"] = a1.number_input(T["pa_sis"], 60, 220, b["pas_mmhg"], help=g["pas_mmhg"], key=k("pas"))
                            nuevo["pad_mmhg"] = a2.number_input(T["pa_dia"], 30, 140, b["pad_mmhg"], help=g["pad_mmhg"], key=k("pad"))
                            nuevo["fc_lpm"] = a1.number_input(c["nv"]["fc_lpm"], 30, 200, b["fc_lpm"], help=g["fc_lpm"], key=k("fc"))
                        elif paso == 1:
                            a1, a2 = st.columns(2)
                            nuevo["temp_c"] = a1.number_input(c["nv"]["temp_c"], 34.0, 42.0, b["temp_c"], 0.1, help=g["temp_c"], key=k("temp"))
                            nuevo["spo2_pct"] = a2.number_input(c["nv"]["spo2_pct"], 70.0, 100.0, b["spo2_pct"], 0.5, help=g["spo2_pct"], key=k("spo2"))
                            nuevo["resp_rpm"] = a1.number_input(c["nv"]["resp_rpm"], 5.0, 40.0, b["resp_rpm"], 0.5, help=g["resp_rpm"], key=k("resp"))
                            nuevo["glucosa_mgdl"] = a2.number_input(c["nv"]["glucosa_mgdl"], 30, 400, b["glucosa_mgdl"], help=g["glucosa_mgdl"], key=k("glu"))
                        elif paso == 2:
                            a1, a2 = st.columns(2)
                            nuevo["sueno_h"] = a1.number_input(c["nv"]["sueno_h"], 0.0, 14.0, b["sueno_h"], 0.5, help=g["sueno_h"], key=k("sueno"))
                            nuevo["orina_l"] = a2.number_input(c["nv"]["orina_l"], 0.0, 6.0, b["orina_l"], 0.1, help=g["orina_l"], key=k("orina"))
                            nuevo["ejercicio_min"] = a1.number_input(c["nv"]["ejercicio_min"], 0, 300, b["ejercicio_min"], 5, help=g["ejercicio_min"], key=k("ejer"))
                        else:
                            nuevo["cefalea_0a10"] = st.slider(c["nv"]["cefalea_0a10"], 0, 10, b["cefalea_0a10"], help=g["cefalea_0a10"], key=k("cef"))
                            nuevo["animo_1a5"] = st.select_slider(T["animo"], options=[1, 2, 3, 4, 5], value=b["animo_1a5"],
                                                                  format_func=lambda x: CARITAS[x - 1], help=T["animo_ayuda"], key=k("animo"))
                            nuevo["sint"] = st.multiselect(T["sintomas"], list(range(len(T["nombres_sintomas"]))), default=b["sint"],
                                                           format_func=lambda i: T["nombres_sintomas"][i], key=k("sint"))
                            if (astro, dia) in juegos:
                                st.caption(f"☄️ {T['reaccion_juego']}: **{juegos[(astro, dia)]['ms']} ms**")
                            else:
                                st.caption(f"☄️ {T['reaccion_juego']}: {T['sin_juego']}")
                        n1, n2 = st.columns(2)
                        atras = n1.form_submit_button(T["atras"], width="stretch", disabled=paso == 0)
                        if paso < n_pasos - 1:
                            siguiente = n2.form_submit_button(T["siguiente"], type="primary", width="stretch")
                        else:
                            siguiente = False
                            enviado = n2.form_submit_button(T["transmitir"], type="primary", width="stretch")
                    b.update(nuevo)
                    if atras or siguiente:
                        st.session_state[clave_p] = paso - 1 if atras else paso + 1
                        st.rerun()
                    # Lo que ya se anotó en las otras tarjetas
                    st.markdown("<div class='resumen-chips'>" + "".join(tema.chip(t) for t in [
                        f"PA {b['pas_mmhg']}/{b['pad_mmhg']}", f"FC {b['fc_lpm']}", f"T {b['temp_c']:.1f} °C",
                        f"SpO₂ {b['spo2_pct']:g}", f"GLU {b['glucosa_mgdl']}", f"💤 {b['sueno_h']:g} h",
                        f"💧 {b['orina_l']:g} L", f"🏃 {b['ejercicio_min']} min", CARITAS[b['animo_1a5'] - 1]])
                        + "</div>", unsafe_allow_html=True)

                if enviado:
                    pas, pad, fc, glu = b["pas_mmhg"], b["pad_mmhg"], b["fc_lpm"], b["glucosa_mgdl"]
                    temp, spo2, sueno, orina = b["temp_c"], b["spo2_pct"], b["sueno_h"], b["orina_l"]
                    ejer, resp, cef, animo = b["ejercicio_min"], b["resp_rpm"], b["cefalea_0a10"], b["animo_1a5"]
                    sint = [T["nombres_sintomas"][i] for i in b["sint"]]
                    nuevos = dict(pas_mmhg=pas, pad_mmhg=pad, fc_lpm=fc, glucosa_mgdl=glu, temp_c=temp, spo2_pct=spo2,
                                  sueno_h=sueno, orina_l=orina, ejercicio_min=ejer, resp_rpm=resp, cefalea_0a10=cef,
                                  animo_1a5=animo, perdida_osea_pct=float(fila["perdida_osea_pct"]))
                    if T["nombres_sintomas"][0] in sint:
                        nuevos["cefalea_0a10"] = max(cef, 4)
                    if T["nombres_sintomas"][1] in sint:
                        nuevos["vision_cambios"] = T["nombres_sintomas"][1]
                    nuevos["reaccion_ms"] = juegos[(astro, dia)]["ms"] if (astro, dia) in juegos else float(fila["reaccion_ms"])
                    res = gen.evaluar_registro(mision, astro, nuevos)
                    # Lo que afecta a toda la tripulación ese día (tormenta, CO₂) se mantiene
                    comunes = [dict(a) for _, a in c["alertas"][c["alertas"]["dia_mision"] == dia].iterrows()
                               if a["codigo"] in {"tormenta", "co2", "sensor_co2", "ambiente"}]
                    registros[(astro, dia)] = dict(valores=nuevos, alertas=comunes + res, momento=datetime.now().isoformat())
                    try:
                        fila_csv = dict(momento=datetime.now().isoformat(timespec="seconds"), astronauta=astro, dia_mision=dia,
                                        **{k: v for k, v in nuevos.items()}, alertas=",".join(a["codigo"] for a in res))
                        pd.DataFrame([fila_csv]).to_csv(ARCHIVO_REGISTROS, mode="a", index=False,
                                                        header=not ARCHIVO_REGISTROS.exists())
                    except OSError:
                        pass
                    st.session_state.pop(f"parte_{astro}_{dia}", None)   # el gemelo muestra la parte más grave
                    for clave in (clave_b, clave_p, clave_e):
                        st.session_state.pop(clave, None)
                    st.session_state[f"transmitido_{astro}_{dia}"] = True
                    st.rerun()

    # ----------------------------- REACCIÓN (minijuego) -----------------------------
    elif estacion == "reaccion":
        with st.container(key="est_reaccion"):
            j1, j2 = st.columns([7, 4], gap="large")
            with j1:
                st.markdown(tema.seccion(T["juego"], T["juego_sub"]), unsafe_allow_html=True)
                resultado = _meteorito(textos=T["juego_textos"], key=f"meteorito_{astro}_{dia}", default=None)
                if resultado and resultado.get("momento") != st.session_state.get(f"ult_{astro}_{dia}"):
                    st.session_state[f"ult_{astro}_{dia}"] = resultado.get("momento")
                    juegos[(astro, dia)] = resultado
                    st.rerun()
            with j2:
                normal = float(base_astro[("reaccion_ms", "mean")])
                st.markdown(tema.seccion(T["tu_reaccion"]), unsafe_allow_html=True)
                if (astro, dia) in juegos:
                    ms = juegos[(astro, dia)]["ms"]
                    delta = ms - normal
                    lento = delta / max(float(base_astro[("reaccion_ms", "std")]), gen.PISO["reaccion_ms"]) >= gen.UMBRAL
                    col = color["amarillo"] if lento else color["verde"]
                    st.markdown(tema.instrumento(T["tu_reaccion"], f"{ms}", "ms",
                                                 f"{delta:+.0f} ms {T['vs_normal']} ({normal:.0f} ms)",
                                                 pct=ms / 600 * 100, color=col, marca=normal / 600 * 100),
                                unsafe_allow_html=True)
                    st.markdown(tema.tarjeta_alerta("⚠️" if lento else "✅", col,
                                                    T["juego_lento"] if lento else T["juego_ok"], [], []),
                                unsafe_allow_html=True)
                else:
                    st.markdown(tema.instrumento(T["tu_normal"], f"{normal:.0f}", "ms", T["sin_jugar"]),
                                unsafe_allow_html=True)

    # ----------------------------- TIERRA (comunicaciones) -----------------------------
    elif estacion == "tierra":
        with st.container(key="est_tierra"):
            st.markdown(tema.seccion(T["canal"], tx["retraso"].format(m=gen.RETRASO_TIERRA_MIN)), unsafe_allow_html=True)
            if a_tierra:
                texto = T["en_cola"] if c["apagon"] else T["en_camino"].format(m=gen.RETRASO_TIERRA_MIN)
                _mensaje_tierra(gen.RETRASO_TIERRA_MIN, c["apagon"], texto, T["animacion"])
                st.code("\n".join([f"CREW HEALTH REPORT · {astro} · {tx['dia']} {dia}"] +
                                  [f"[{a['nivel'].upper()}] {c['msg'][a['codigo']][0]}" for a in a_tierra] +
                                  [f"BP {int(valores['pas_mmhg'])}/{int(valores['pad_mmhg'])} · HR {int(valores['fc_lpm'])} · "
                                   f"T {float(valores['temp_c']):.1f} °C · GLU {int(valores['glucosa_mgdl'])} · "
                                   f"{c['nv']['preparacion']} {prep}/100"]), language=None)
            else:
                st.markdown(tema.tarjeta_alerta("📡", color["verde"], T["silencio"], [], [T["nada_tierra"]]),
                            unsafe_allow_html=True)

    # ----------------------------- VISIÓN (SANS) -----------------------------
    elif estacion == "vision":
        with st.container(key="est_vision"):
            st.markdown(tema.seccion(T["vision"], T["vision_sub"]), unsafe_allow_html=True)
            t1, t2 = st.columns(2, gap="large")
            with t1:
                CARPETA_VISION.mkdir(parents=True, exist_ok=True)
                foto = st.camera_input(T["camara"], key=f"cam_{astro}_{dia}")
                url = st.text_input(T["esp32"], placeholder="http://192.168.1.50/capture", key=f"url_{astro}")
                if st.button(T["capturar"], key=f"btn_{astro}_{dia}") and url:
                    try:
                        with urllib.request.urlopen(url, timeout=6) as r:
                            (CARPETA_VISION / f"{astro}_dia{dia:02d}.jpg").write_bytes(r.read())
                    except Exception as e:
                        st.error(T["error_cam"].format(e=e))
                if foto is not None:
                    (CARPETA_VISION / f"{astro}_dia{dia:02d}.jpg").write_bytes(foto.getvalue())
                fotos = sorted(CARPETA_VISION.glob(f"{astro}_dia*.jpg"))
                if fotos:
                    f1, f2 = st.columns(2)
                    f1.image(str(fotos[0]), caption=T["foto_base"])
                    f2.image(str(fotos[-1]), caption=T["foto_hoy"])
            with t2:
                st.markdown(f"<div class='panel'><div class='panel-cab'><span>Amsler</span></div>"
                            f"<div style='font-size:.88rem;margin-bottom:10px'>{T['amsler']}</div>{_amsler()}</div>",
                            unsafe_allow_html=True)
                resp = st.radio(T["amsler_q"], [T["no"], T["si"]], horizontal=True, key=f"amsler_{astro}_{dia}")
                if resp == T["si"]:
                    _tarjeta_alerta(dict(nivel="amarillo", origen="persona", codigo="vision", afectados=astro,
                                         triaje="tierra", evidencia=json.dumps([])), c, 999)
                else:
                    st.caption(T["vision_ok"])

    # ----------------------------- LOGROS (misiones, escudo, insignias) -----------------------------
    else:
        with st.container(key="est_logros"):
            l1, l2 = st.columns([5, 6], gap="large")
            with l1:
                st.markdown(tema.seccion(T["misiones"]), unsafe_allow_html=True)
                st.markdown("".join(
                    f"<div class='lectura'><span class='pt' style='--c:{color['verde'] if ok else '#3a4d63'}'></span>"
                    f"<span class='nm'>{'✅' if ok else '⬜'} {nombres[k]}</span><span class='vl'>+{PUNTOS[k]}</span></div>"
                    for k, ok in hechas_hoy.items()), unsafe_allow_html=True)
                st.markdown(tema.seccion(T["escudo"]), unsafe_allow_html=True)
                st.markdown(tema.instrumento(T["escudo"], f"🛡️ {escudo}", "%", T["escudo_sub"], pct=escudo,
                                             color=color["verde"], marca=80), unsafe_allow_html=True)
            with l2:
                # Insignias
                def dias_seguidos(clave):
                    n = 0
                    for d in range(dia, 0, -1):
                        if tabla_m[(astro, d)][clave]:
                            n += 1
                        else:
                            break
                    return n
                tiene = {
                    "solar": bool(mision[(mision["dia_mision"] <= dia) & mision["tormenta_solar"]].shape[0]),
                    "gota": dias_seguidos("agua") >= 7,
                    "hueso": dias_seguidos("ejercicio") >= 7,
                    "meteoro": (astro, dia) in juegos,
                    "equipo": escudo >= 80,
                }
                st.markdown(tema.seccion(T["insignias"], f"{sum(tiene.values())}/{len(tiene)}"), unsafe_allow_html=True)
                st.markdown("<div class='insignias'>" + "".join(
                    f"<div class='insignia {'si' if ok else 'no'} entrar'><div class='in'>{T['insignia_nombres'][k]}</div>"
                    f"<div class='id'>{T['insignia_desc'][k]}</div></div>" for k, ok in tiene.items()) + "</div>",
                    unsafe_allow_html=True)


def _amsler():
    """Cuadrícula de Amsler simple (test visual de autochequeo)."""
    lineas = "".join(f"<line x1='{i*12}' y1='0' x2='{i*12}' y2='120' stroke='#444' stroke-width='0.8'/>"
                     f"<line x1='0' y1='{i*12}' x2='120' y2='{i*12}' stroke='#444' stroke-width='0.8'/>" for i in range(11))
    return (f"<svg viewBox='0 0 120 120' width='180' style='background:#fff;border:3px solid #1c3550;border-radius:8px;display:block;margin:auto;box-shadow:0 0 22px rgba(62,224,255,.15)'>"
            f"{lineas}<circle cx='60' cy='60' r='2.5' fill='#000'/></svg>")
