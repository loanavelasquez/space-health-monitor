"""
GENERADOR DE MISIÓN + MOTOR DE ALERTAS
NASA Space Apps Challenge 2026 - Crew Health Monitor

Crea los datos de una misión simulada (31 días x 4 astronautas), detecta
anomalías respecto del "normal" de cada astronauta, cruza las variables y
genera alertas con acciones, un índice de preparación y un triaje
(resolver a bordo / consultar con la Tierra).

Para regenerar los datos:   python generador.py

Cada valor indica de dónde sale (fuente) o si es un SUPUESTO del equipo.
"""

import json
import random
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

CARPETA_DATOS = Path(__file__).parent / "data"

# ===========================================================================
# 1. PARÁMETROS DE LA MISIÓN
# ===========================================================================

FECHA_INICIO = "2024-05-01"
FECHA_FIN = "2024-05-31"
SEMILLA = 7
RETRASO_TIERRA_MIN = 12   # NASA (ASCEND 2022): de 0 a ~22 min de ida según la posición; usamos un valor intermedio

# --- "El normal" de cada astronauta (línea base personal) -------------------
# fc:       pulso en reposo (lpm). Rango clínico normal 60-100.
# spo2:     oxigenación (%). Normal 95-100.
# temp:     temperatura central (°C). En vuelos largos sube ~1 °C en reposo
#           ("fiebre espacial", Stahn et al. 2017), por eso las bases son ~37 °C.
# resp:     respiraciones por minuto. Normal 12-20.
# sueno:    horas de sueño. En la ISS el promedio es ~6,1 h aunque NASA
#           programa 8,5 h (Barger et al. 2014).
# reaccion: tiempo de reacción (ms) en la prueba de vigilancia PVT de 3 min
#           de la batería Cognition de NASA. SUPUESTO: 270-320 ms.
# orina:    litros de orina al día. NASA busca 2,5-3 L/día; el riesgo de
#           cálculos renales sube por debajo de 1,5 L/día.
# ejercicio: minutos de ejercicio al día. NASA: en la ISS ~2 h/día (contramedida
#           principal contra la pérdida ósea y muscular).
# pas/pad:  presión arterial sistólica/diastólica (mmHg). En vuelos de 3-6 meses baja
#           ~10 mmHg (Norsk et al. 2015, NASA), por eso las bases son algo bajas.
# glucosa:  glucosa en ayunas (mg/dL). Normal 70-99. En el espacio aparece resistencia
#           a la insulina (Hughson et al.), sobre todo con poca actividad.
# animo:    check-in de ánimo de 1 (muy mal) a 5 (muy bien). NASA: el aislamiento y el
#           encierro son el mayor riesgo para la salud conductual.
TRIPULACION = {
    "A1": dict(fc=62, spo2=98.0, temp=37.0, resp=14, sueno=6.3, reaccion=280, orina=2.6, ejercicio=120,
               pas=108, pad=68, glucosa=86, animo=4.2),
    "A2": dict(fc=70, spo2=97.5, temp=37.2, resp=15, sueno=6.1, reaccion=300, orina=2.4, ejercicio=110,
               pas=112, pad=70, glucosa=90, animo=4.1),
    "A3": dict(fc=66, spo2=98.0, temp=36.9, resp=13, sueno=6.5, reaccion=290, orina=2.8, ejercicio=125,
               pas=110, pad=69, glucosa=84, animo=4.3),
    "A4": dict(fc=72, spo2=97.0, temp=37.1, resp=16, sueno=6.0, reaccion=310, orina=2.5, ejercicio=115,
               pas=116, pad=72, glucosa=88, animo=4.0),
}
# Variación natural de un día a otro (SUPUESTO)
VARIACION = dict(fc=2.0, spo2=0.4, temp=0.12, resp=0.7, sueno=0.35, reaccion=12, orina=0.15, ejercicio=8,
                 pas=4.0, pad=3.0, glucosa=3.0, animo=0.35)

# --- Ambiente de la nave ---------------------------------------------------
RAD_FONDO = 1.8            # mSv/día en el viaje a Marte (Curiosity RAD, Zeitlin et al. 2013)
RAD_TORMENTA = 10.0        # ESTIMACIÓN dentro del rango publicado: Curiosity midió ~5 tormentas en su viaje
                           # (~5 % de la dosis total, unos 3 mSv por tormenta) y 8,1 mGy en la tormenta de mayo 2024
                           # en la superficie de Marte (con atmósfera); en el espacio una tormenta grande da más
RAD_TORMENTA_DIA2 = 4.0    # ESTIMACIÓN: las tormentas duran 1-2 días y van bajando
PROTECCION_REFUGIO = 0.75  # Artemis I (DLR/NASA): la dosis en la zona más protegida de Orion fue 4 veces menor
LIMITE_CARRERA = 600.0     # mSv, límite de carrera (NASA-STD-3001)
LIMITE_TORMENTA = 250.0    # mSv por tormenta solar (NASA-STD-3001)
CO2_NORMAL = 2.0           # mmHg; NASA recomienda < 2,5 de promedio para mantener el dolor de cabeza < 1 %
CO2_LIMITE = 3.0           # mmHg; límite de NASA (promedio de 1 h)
CO2_FALLA = 5.0            # mmHg; > 4,5 se asocia a fatiga, malestar y peor sueño (NASA OCHMO)
TEMP_CABINA = 24.0         # °C: la ISS se mantiene alrededor de 24 °C
PERDIDA_OSEA_MES = 1.0     # % de densidad ósea por mes con ejercicio (NASA: 1-1,5 %/mes)
PERDIDA_OSEA_MES_SIN_EJ = 1.5   # % por mes cuando no se cumple el ejercicio (SUPUESTO: extremo alto)

# Tormentas solares (eventos SEP) de NASA DONKI para mayo 2024 (respaldo si la API no responde)
TORMENTAS_RESPALDO = ["2024-05-09", "2024-05-10", "2024-05-11", "2024-05-13"]

# --- Guion de la misión (eventos simulados) ---------------------------------
GUION = [
    dict(evento="mal_sueno", inicio="2024-05-10", fin="2024-05-15", afectados=["A2"],
         es="A2 duerme mal después de la tormenta solar", en="A2 sleeps poorly after the solar storm"),
    dict(evento="sin_ejercicio", inicio="2024-05-15", fin="2024-05-19", afectados=["A4"],
         es="A4 casi no hace ejercicio (equipo en mantenimiento)", en="A4 barely exercises (equipment under maintenance)"),
    dict(evento="deshidratacion", inicio="2024-05-16", fin="2024-05-19", afectados=["A1"],
         es="A1 toma poca agua", en="A1 drinks too little water"),
    dict(evento="falla_filtro_co2", inicio="2024-05-20", fin="2024-05-22", afectados=["A1", "A2", "A3", "A4"],
         es="Falla el filtro de CO₂ de la cabina", en="Cabin CO₂ scrubber failure"),
    dict(evento="infeccion", inicio="2024-05-25", fin="2024-05-28", afectados=["A3"],
         es="A3 tiene una posible infección", en="A3 has a possible infection"),
    # Fallas de SENSOR: el sensor marca algo raro, pero el cuerpo y la cabina están bien
    dict(evento="falla_sensor_co2", inicio="2024-05-29", fin="2024-05-30", afectados=["A1", "A2", "A3", "A4"],
         es="El sensor de CO₂ falla y marca alto (el aire está bien)",
         en="The CO₂ sensor fails and reads high (the air is fine)"),
    dict(evento="falla_sensor_spo2", inicio="2024-05-31", fin="2024-05-31", afectados=["A2"],
         es="El oxímetro de A2 se suelta y marca una SpO₂ imposible",
         en="A2's pulse oximeter slips and reads an impossible SpO₂"),
]

# Qué alerta debería dar cada evento (se usa para validar el motor de alertas)
ALERTA_ESPERADA = {"tormenta": "tormenta", "mal_sueno": "fatiga", "sin_ejercicio": "ejercicio",
                   "deshidratacion": "renal", "falla_filtro_co2": "co2", "infeccion": "infeccion",
                   "falla_sensor_co2": "sensor_co2", "falla_sensor_spo2": "sensor_spo2"}
# Alertas extra que también son correctas para un evento (no cuentan como falsas alarmas)
ALERTAS_ACEPTADAS = {"mal_sueno": {"animo", "glucosa"}, "sin_ejercicio": {"glucosa"},
                     "falla_filtro_co2": {"animo"}, "infeccion": {"animo"}, "tormenta": {"presion"}}


# ===========================================================================
# 2. TORMENTAS SOLARES REALES (NASA DONKI)
# ===========================================================================

def obtener_tormentas(inicio=FECHA_INICIO, fin=FECHA_FIN):
    """Fechas de tormentas solares (eventos SEP) desde NASA DONKI."""
    q = f"startDate={inicio}&endDate={fin}"
    urls = [f"https://ccmc.gsfc.nasa.gov/DONKI/WS/get/SEP?{q}",
            f"https://api.nasa.gov/DONKI/SEP?{q}&api_key=DEMO_KEY"]
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                eventos = json.loads(r.read().decode("utf-8"))
            fechas = sorted({e["eventTime"][:10] for e in (eventos or [])})
            print(f"Tormentas desde NASA DONKI: {fechas}")
            return [date.fromisoformat(f) for f in fechas]
        except Exception as error:
            print(f"No respondió {url.split('?')[0]} ({error})")
    print(f"Se usan las fechas de respaldo de DONKI: {TORMENTAS_RESPALDO}")
    return [date.fromisoformat(f) for f in TORMENTAS_RESPALDO]


def evento_activo(nombre, dia, astronauta=None):
    for e in GUION:
        if e["evento"] == nombre and date.fromisoformat(e["inicio"]) <= dia <= date.fromisoformat(e["fin"]):
            if astronauta is None or astronauta in e["afectados"]:
                return True
    return False


# ===========================================================================
# 3. GENERAR LA MISIÓN
# ===========================================================================

def generar_mision(tormentas):
    random.seed(SEMILLA)
    dias = pd.date_range(FECHA_INICIO, FECHA_FIN).date

    # --- Ambiente (igual para toda la tripulación) ---
    ambiente, acum, acum_sin = [], 0.0, 0.0
    for i, dia in enumerate(dias, start=1):
        extra = RAD_TORMENTA if dia in tormentas else (
            RAD_TORMENTA_DIA2 if (dia - timedelta(days=1)) in tormentas else 0.0)
        fondo = RAD_FONDO + random.uniform(-0.15, 0.15)
        dosis = fondo + extra * (1 - PROTECCION_REFUGIO)      # la tripulación sigue la alerta
        acum += dosis
        acum_sin += fondo + extra
        falla = evento_activo("falla_filtro_co2", dia)
        co2_real = (CO2_FALLA if falla else CO2_NORMAL) + random.uniform(-0.2, 0.2)
        # Lo que MARCA el sensor: igual al real, salvo cuando el sensor falla
        co2_medido = 5.8 + random.uniform(-0.2, 0.2) if evento_activo("falla_sensor_co2", dia) else co2_real
        ambiente.append(dict(
            fecha=dia, dia_mision=i, tormenta_solar=dia in tormentas,
            radiacion_msv=round(dosis, 2), radiacion_sin_refugio_msv=round(fondo + extra, 2),
            radiacion_acum_msv=round(acum, 1), radiacion_acum_sin_refugio_msv=round(acum_sin, 1),
            radiacion_pct_limite=round(acum / LIMITE_CARRERA * 100, 1),
            co2_mmhg=round(co2_medido, 2),          # lo que ve la app (sensor)
            co2_real_mmhg=round(co2_real, 2),       # lo que respira la tripulación (solo para validar)
            temp_cabina_c=round(TEMP_CABINA + (2.5 if falla else 0) + random.uniform(-0.3, 0.3), 1),
        ))
    ambiente = pd.DataFrame(ambiente)

    # --- Salud de cada astronauta ---
    random.seed(SEMILLA + 1)
    filas = []
    perdida_osea = {n: 0.0 for n in TRIPULACION}
    for _, amb in ambiente.iterrows():
        dia = amb["fecha"]
        for nombre, base in TRIPULACION.items():
            v = {k: base[k] + random.gauss(0, VARIACION[k]) for k in base}
            cefalea = max(0.0, random.uniform(-0.5, 1.0))           # check-in diario 0-10
            estres = 3.0 + random.uniform(-0.5, 0.5)                 # check-in diario 0-10

            # CO2 alto: respira más rápido, dolor de cabeza, duerme peor, reacciona más lento
            # (el cuerpo reacciona al CO2 REAL, no a lo que marca el sensor)
            exceso_co2 = max(0, amb["co2_real_mmhg"] - CO2_LIMITE)
            v["resp"] += 1.5 * exceso_co2
            v["sueno"] -= 0.3 * exceso_co2
            v["reaccion"] += 25 * exceso_co2
            cefalea += 2.5 * max(0, amb["co2_real_mmhg"] - 2.8)
            v["animo"] -= 0.3 * exceso_co2

            # Tormenta solar: estrés y reacción algo más lenta (alerta, refugio, descanso interrumpido)
            if amb["tormenta_solar"]:
                estres += 3
                v["reaccion"] += 20
                v["pas"] += 4        # el estrés sube un poco la presión

            # Mal sueño
            if evento_activo("mal_sueno", dia, nombre):
                v["sueno"] -= 2.0
                estres += 2
                v["animo"] -= 1.6    # dormir mal baja el ánimo
                v["glucosa"] += 4    # y empeora el control del azúcar

            # Infección: pulso y temperatura suben, algo menos de oxígeno, dolor de cabeza
            infeccion = evento_activo("infeccion", dia, nombre)
            if infeccion:
                v["fc"] += 12        # regla clínica de Liebermeister: ~8-10 lpm más por cada °C de fiebre
                v["temp"] += 1.1
                v["spo2"] -= 0.8
                cefalea += 2
                v["animo"] -= 1.0

            # Deshidratación: menos orina
            if evento_activo("deshidratacion", dia, nombre):
                v["orina"] -= 1.4

            # Sin ejercicio: más pérdida ósea
            sin_ej = evento_activo("sin_ejercicio", dia, nombre)
            if sin_ej:
                v["ejercicio"] = 20 + random.uniform(-5, 10)
                v["glucosa"] += 12   # moverse menos aumenta la resistencia a la insulina
            tasa = PERDIDA_OSEA_MES_SIN_EJ if v["ejercicio"] < 60 else PERDIDA_OSEA_MES
            perdida_osea[nombre] += tasa / 30

            # La falta de sueño se nota en fatiga y concentración
            deficit = max(0, base["sueno"] - v["sueno"])
            v["reaccion"] += 30 * deficit
            fatiga = 2 + 1.5 * deficit + (3 if infeccion else 0) + random.uniform(-0.5, 0.5)
            estres_termico = max(0, amb["temp_cabina_c"] - 26) * 2 + max(0, v["temp"] - 37.8) * 4

            # Falla del oxímetro: la lectura cae a un valor imposible, el cuerpo está bien
            if evento_activo("falla_sensor_spo2", dia, nombre):
                v["spo2"] = 86 + random.uniform(-1, 1)

            filas.append(dict(
                fecha=dia, dia_mision=amb["dia_mision"], astronauta=nombre,
                fc_lpm=round(v["fc"]), spo2_pct=round(min(v["spo2"], 100), 1),
                temp_c=round(v["temp"], 1), resp_rpm=round(v["resp"], 1),
                sueno_h=round(v["sueno"], 1), reaccion_ms=round(v["reaccion"]),
                orina_l=round(v["orina"], 2), ejercicio_min=round(v["ejercicio"]),
                cefalea_0a10=round(min(cefalea, 10), 1), fatiga_0a10=round(min(max(fatiga, 0), 10), 1),
                estres_0a10=round(min(max(estres, 0), 10), 1),
                perdida_osea_pct=round(perdida_osea[nombre], 2),
                estres_termico_0a10=round(min(estres_termico, 10), 1),
                pas_mmhg=round(v["pas"]), pad_mmhg=round(v["pad"]), glucosa_mgdl=round(v["glucosa"]),
                animo_1a5=int(min(5, max(1, round(v["animo"])))),
            ))
    return pd.DataFrame(filas).merge(ambiente, on=["fecha", "dia_mision"])


# ===========================================================================
# 4. MOTOR DE ALERTAS
# ===========================================================================

# Variables que se comparan con "el normal" de cada astronauta
VARIABLES = ["fc_lpm", "temp_c", "resp_rpm", "sueno_h", "reaccion_ms", "spo2_pct", "cefalea_0a10"]
PISO = dict(fc_lpm=VARIACION["fc"], temp_c=VARIACION["temp"], resp_rpm=VARIACION["resp"],
            sueno_h=VARIACION["sueno"], reaccion_ms=VARIACION["reaccion"], spo2_pct=VARIACION["spo2"],
            cefalea_0a10=0.6)
UMBRAL = 3.0       # DECISIÓN DE DISEÑO: desviaciones respecto de su normal (comprobado con la prueba de 30 misiones)
DIAS_BASE = 7      # días usados para aprender "el normal"

# Umbrales fijos (no dependen de la persona)
ORINA_MIN = 1.5        # L/día: por debajo sube el riesgo de cálculos renales (NASA)
EJERCICIO_MIN = 60     # min/día: DECISIÓN DE DISEÑO = la mitad del promedio de NASA (~2 h/día)
FIEBRE = 38.0          # °C
SPO2_MIN = 95.0        # %
# Presión arterial: categorías de la American Heart Association + presión baja
PAS_ALTA, PAD_ALTA = 130, 80        # desde aquí: alta (etapa 1)
PAS_MUY_ALTA, PAD_MUY_ALTA = 140, 90  # etapa 2
PAS_BAJA, PAD_BAJA = 90, 60
# Glucosa en ayunas (mg/dL): valores clínicos estándar
GLU_BAJA, GLU_ALTA, GLU_MUY_ALTA = 70, 100, 126
ANIMO_DIAS = 3         # días seguidos con ánimo bajo antes de sugerir hablar con el psicólogo

# Qué alerta se resuelve a bordo y cuál conviene consultar con la Tierra
TRIAJE = {"tormenta": "bordo", "co2": "bordo", "ambiente": "bordo", "fatiga": "bordo",
          "ejercicio": "bordo", "renal": "tierra", "infeccion": "tierra", "spo2": "tierra",
          "individual": "bordo", "sensor_co2": "bordo", "sensor_spo2": "bordo",
          "presion": "tierra", "glucosa": "bordo", "animo": "tierra", "vision": "tierra"}

SPO2_IMPOSIBLE = 90.0  # una SpO2 menor sin ningún otro síntoma es más probable que sea un error del sensor
Z_SINTOMA = 2.0        # desde cuántas desviaciones contamos a alguien como "con síntomas" de CO2


def lineas_base(mision):
    return mision[mision["dia_mision"] <= DIAS_BASE].groupby("astronauta")[VARIABLES].agg(["mean", "std"])


def puntajes_z(mision):
    """Para cada fila y variable: cuántas 'desviaciones' se aleja de su normal."""
    base = lineas_base(mision)
    z = pd.DataFrame(index=mision.index)
    for var in VARIABLES:
        media = mision["astronauta"].map(base[(var, "mean")])
        desv = mision["astronauta"].map(base[(var, "std")]).clip(lower=PISO[var])
        z[var] = (mision[var] - media) / desv
    return z


def generar_alertas(mision):
    """Revisa cada día y decide: ¿es la nave, eres tú o es el sensor?
    Cada alerta guarda su EVIDENCIA (qué datos la dispararon), para poder explicar el "por qué"."""
    z = puntajes_z(mision)
    base = lineas_base(mision)
    alertas = []
    # Ánimo bajo = 1 punto o más por debajo de su normal; se cuenta en días seguidos
    animo_normal = mision[mision["dia_mision"] <= DIAS_BASE].groupby("astronauta")["animo_1a5"].mean()
    animo_bajo = (mision["animo_1a5"] <= mision["astronauta"].map(animo_normal) - 1)
    bajo = dict(zip(zip(mision["astronauta"], mision["dia_mision"]), animo_bajo))

    for dia, grupo in mision.groupby("dia_mision"):
        fila = grupo.iloc[0]
        zg = z.loc[grupo.index]
        zg.index = grupo["astronauta"]
        fuera = (zg.abs() >= UMBRAL)
        datos = grupo.set_index("astronauta")

        def nueva(nivel, origen, codigo, afectados, detalle, evidencia):
            alertas.append(dict(dia_mision=dia, nivel=nivel, origen=origen, codigo=codigo,
                                afectados=afectados, detalle=detalle, triaje=TRIAJE[codigo],
                                evidencia=json.dumps(evidencia, ensure_ascii=False)))

        def ev_z(a, var):   # evidencia: dato vs. el normal de esa persona
            return dict(t="z", var=var, astronauta=a, valor=float(datos.loc[a, var]),
                        normal=round(float(base.loc[a, (var, "mean")]), 1), z=round(float(zg.loc[a, var]), 1))

        # --- Radiación: tormenta solar real (NASA DONKI) ---
        if fila["tormenta_solar"]:
            nueva("rojo", "nave", "tormenta", "A1, A2, A3, A4", f"{fila['radiacion_sin_refugio_msv']} mSv",
                  [dict(t="donki"), dict(t="lim", var="radiacion_sin_refugio_msv",
                                         valor=float(fila["radiacion_sin_refugio_msv"]), limite=RAD_FONDO)])

        # --- CO2: ¿es la nave o es el sensor? ---
        sintomas = {"resp_rpm", "cefalea_0a10", "reaccion_ms"}
        con_sintomas = [a for a in zg.index if (zg.loc[a, list(sintomas)] >= Z_SINTOMA).any()]
        explicadas = set()
        if fila["co2_mmhg"] > CO2_LIMITE:
            ev = [dict(t="lim", var="co2_mmhg", valor=float(fila["co2_mmhg"]), limite=CO2_LIMITE),
                  dict(t="n", k="sintomas", valor=len(con_sintomas), total=len(zg))]
            if len(con_sintomas) >= 2:
                ev += [ev_z(a, v) for a in con_sintomas for v in sintomas if zg.loc[a, v] >= Z_SINTOMA][:6]
                nueva("rojo", "nave", "co2", "A1, A2, A3, A4", f"{fila['co2_mmhg']} mmHg", ev)
                explicadas |= sintomas | {"sueno_h"}
            else:
                nueva("amarillo", "sensor", "sensor_co2", "A1, A2, A3, A4", f"{fila['co2_mmhg']} mmHg", ev)

        # --- Cambios en 3 o más astronautas sin causa conocida -> probable causa ambiental ---
        comunes = [v for v in VARIABLES if fuera[v].sum() >= 3 and v not in explicadas]
        if fila["tormenta_solar"]:
            explicadas |= {"reaccion_ms"}
            comunes = [v for v in comunes if v != "reaccion_ms"]
        if comunes:
            nueva("amarillo", "nave", "ambiente", "A1, A2, A3, A4", ", ".join(comunes),
                  [ev_z(a, v) for v in comunes for a in zg.index if fuera.loc[a, v]][:6])
            explicadas |= set(comunes)

        # --- Problemas de una sola persona: "eres tú" (o su sensor) ---
        for a, f in datos.iterrows():
            vars_ = {v for v in VARIABLES if fuera.loc[a, v]} - explicadas
            spo2_sola = (f["spo2_pct"] < SPO2_IMPOSIBLE and abs(zg.loc[a, "fc_lpm"]) < 2
                         and abs(zg.loc[a, "resp_rpm"]) < 2)
            if spo2_sola:
                nueva("amarillo", "sensor", "sensor_spo2", a, f"{f['spo2_pct']} %",
                      [ev_z(a, "spo2_pct"), ev_z(a, "fc_lpm"), ev_z(a, "resp_rpm")])
                vars_.discard("spo2_pct")
            if {"fc_lpm", "temp_c"} <= vars_ or f["temp_c"] >= FIEBRE:
                nueva("rojo", "persona", "infeccion", a, f"{f['temp_c']} °C, {f['fc_lpm']} lpm",
                      [ev_z(a, "temp_c"), ev_z(a, "fc_lpm"),
                       dict(t="lim", var="temp_c", valor=float(f["temp_c"]), limite=FIEBRE)])
            elif "sueno_h" in vars_ or "reaccion_ms" in vars_:
                nueva("amarillo", "persona", "fatiga", a, f"{f['sueno_h']} h, {f['reaccion_ms']} ms",
                      [ev_z(a, "sueno_h"), ev_z(a, "reaccion_ms")])
            elif "spo2_pct" in vars_ or (f["spo2_pct"] < SPO2_MIN and not spo2_sola):
                nueva("amarillo", "persona", "spo2", a, f"{f['spo2_pct']} %", [ev_z(a, "spo2_pct")])
            elif vars_:
                nueva("amarillo", "persona", "individual", a, ", ".join(sorted(vars_)),
                      [ev_z(a, v) for v in sorted(vars_)])
            if f["orina_l"] < ORINA_MIN:
                nueva("amarillo", "persona", "renal", a, f"{f['orina_l']} L",
                      [dict(t="lim", var="orina_l", valor=float(f["orina_l"]), limite=ORINA_MIN),
                       dict(t="lim", var="perdida_osea_pct", valor=float(f["perdida_osea_pct"]), limite=0)])
            if f["ejercicio_min"] < EJERCICIO_MIN:
                nueva("amarillo", "persona", "ejercicio", a, f"{f['ejercicio_min']} min",
                      [dict(t="lim", var="ejercicio_min", valor=float(f["ejercicio_min"]), limite=EJERCICIO_MIN)])
            for codigo, nivel, ev in reglas_fijas(f):
                nueva(nivel, "persona", codigo, a, str(ev[0]["valor"]) if ev and "valor" in ev[0] else "", ev)
            if all(bajo.get((a, dia - k), False) for k in range(ANIMO_DIAS)):
                nueva("amarillo", "persona", "animo", a, f"{int(f['animo_1a5'])}/5",
                      [dict(t="lim", var="animo_1a5", valor=float(f["animo_1a5"]),
                            limite=round(float(animo_normal[a]), 1)), dict(t="dias", valor=ANIMO_DIAS)])

    return pd.DataFrame(alertas, columns=["dia_mision", "nivel", "origen", "codigo", "afectados",
                                          "detalle", "triaje", "evidencia"])


# ===========================================================================
# 5. VALIDACIÓN: ¿la app detecta lo que pasó de verdad en el guion?
# ===========================================================================

def validar(mision, alertas):
    """Compara las alertas con el guion (la 'verdad'):
    - eventos detectados, días detectados y si se detectó el mismo primer día
    - falsas alarmas: alertas que no corresponden a ningún evento del guion."""
    dias = mision.drop_duplicates("dia_mision").set_index("fecha")["dia_mision"]
    tormentas = sorted(mision.loc[mision["tormenta_solar"], "fecha"].unique())
    eventos = [dict(evento="tormenta", dias=[dias[d] for d in tormentas],
                    afectados=["A1", "A2", "A3", "A4"])]
    for e in GUION:
        rango = pd.date_range(e["inicio"], e["fin"]).date
        eventos.append(dict(evento=e["evento"], dias=[dias[d] for d in rango], afectados=e["afectados"]))

    def coincide(fila_alerta, ev, extras=False):
        codigos = {ALERTA_ESPERADA[ev["evento"]]}
        if extras:
            codigos |= ALERTAS_ACEPTADAS.get(ev["evento"], set())
        if fila_alerta["codigo"] not in codigos or fila_alerta["dia_mision"] not in ev["dias"]:
            return False
        if extras and fila_alerta["codigo"] != ALERTA_ESPERADA[ev["evento"]]:
            # una consecuencia del evento en una persona afectada también es correcta
            return any(a in fila_alerta["afectados"] for a in ev["afectados"])
        return all(a in fila_alerta["afectados"] for a in ev["afectados"])

    resultados = []
    for ev in eventos:
        detectados = [d for d in ev["dias"]
                      if any(coincide(f, ev) for _, f in alertas[alertas["dia_mision"] == d].iterrows())]
        resultados.append(dict(evento=ev["evento"], afectados=", ".join(ev["afectados"]),
                               dias=len(ev["dias"]), dias_detectados=len(detectados),
                               primer_dia=ev["dias"][0] in detectados))
    res = pd.DataFrame(resultados)

    ok = alertas.apply(lambda f: any(coincide(f, ev, extras=True) for ev in eventos), axis=1)
    falsas = alertas[~ok]
    resumen = dict(
        eventos=len(res), eventos_detectados=int((res["dias_detectados"] > 0).sum()),
        primer_dia=int(res["primer_dia"].sum()),
        dias_evento=int(res["dias"].sum()), dias_detectados=int(res["dias_detectados"].sum()),
        alertas=len(alertas), alertas_correctas=int(ok.sum()), falsas_alarmas=len(falsas),
        mediciones=len(mision),
    )
    return resumen, res, falsas


def prueba_robustez(semillas=range(1, 31), tormentas=None):
    """Repite la misión con distintas variaciones aleatorias (semillas) y mide
    cuánto acierta el motor en promedio. Así sabemos que no fue suerte."""
    global SEMILLA
    original = SEMILLA
    tormentas = tormentas or [date.fromisoformat(f) for f in TORMENTAS_RESPALDO]
    filas = []
    try:
        for s in semillas:
            SEMILLA = s
            m = generar_mision(tormentas)
            r, _, _ = validar(m, generar_alertas(m))
            filas.append(dict(semilla=s, **r))
    finally:
        SEMILLA = original
    return pd.DataFrame(filas)


def reglas_fijas(f):
    """Reglas que no dependen de la persona: presión arterial y glucosa.
    Devuelve una lista de (codigo, nivel, evidencia)."""
    salida = []
    pas, pad = f["pas_mmhg"], f["pad_mmhg"]
    if pas >= PAS_MUY_ALTA or pad >= PAD_MUY_ALTA:
        nivel = "rojo"
    elif pas >= PAS_ALTA or pad >= PAD_ALTA or pas < PAS_BAJA or pad < PAD_BAJA:
        nivel = "amarillo"
    else:
        nivel = None
    if nivel:
        salida.append(("presion", nivel, [dict(t="pa", valor=f"{int(pas)}/{int(pad)}", pas=float(pas),
                                               pad=float(pad))]))
    glu = f["glucosa_mgdl"]
    if glu < GLU_BAJA or glu >= GLU_MUY_ALTA:
        salida.append(("glucosa", "rojo", [dict(t="lim", var="glucosa_mgdl", valor=float(glu),
                                               limite=GLU_BAJA if glu < GLU_BAJA else GLU_MUY_ALTA)]))
    elif glu >= GLU_ALTA:
        salida.append(("glucosa", "amarillo", [dict(t="lim", var="glucosa_mgdl", valor=float(glu), limite=GLU_ALTA)]))
    return salida


def evaluar_registro(mision, astronauta, valores):
    """Evalúa UN check-in que el astronauta acaba de ingresar, con las mismas reglas.
    'valores' es un diccionario con las mismas columnas de mision.csv.
    Devuelve una lista de alertas (diccionarios) para mostrar al instante."""
    base = lineas_base(mision)
    z = {}
    for var in VARIABLES:
        if var in valores and valores[var] is not None:
            desv = max(float(base.loc[astronauta, (var, "std")]), PISO[var])
            z[var] = (float(valores[var]) - float(base.loc[astronauta, (var, "mean")])) / desv
    fuera = {v for v, s in z.items() if abs(s) >= UMBRAL}
    res = []

    def ev_z(var):
        return dict(t="z", var=var, astronauta=astronauta, valor=float(valores[var]),
                    normal=round(float(base.loc[astronauta, (var, "mean")]), 1), z=round(z[var], 1))

    def nueva(nivel, codigo, evidencia, origen="persona"):
        res.append(dict(nivel=nivel, origen=origen, codigo=codigo, afectados=astronauta,
                        triaje=TRIAJE[codigo], evidencia=json.dumps(evidencia, ensure_ascii=False)))

    spo2 = valores.get("spo2_pct")
    spo2_sola = (spo2 is not None and spo2 < SPO2_IMPOSIBLE and abs(z.get("fc_lpm", 0)) < 2
                 and abs(z.get("resp_rpm", 0)) < 2)
    if spo2_sola:
        nueva("amarillo", "sensor_spo2", [ev_z(v) for v in ("spo2_pct", "fc_lpm", "resp_rpm") if v in z],
              origen="sensor")
        fuera.discard("spo2_pct")
    if {"fc_lpm", "temp_c"} <= fuera or (valores.get("temp_c") or 0) >= FIEBRE:
        nueva("rojo", "infeccion", [ev_z(v) for v in ("temp_c", "fc_lpm") if v in z])
    elif "sueno_h" in fuera or "reaccion_ms" in fuera:
        nueva("amarillo", "fatiga", [ev_z(v) for v in ("sueno_h", "reaccion_ms") if v in z])
    elif "spo2_pct" in fuera or (spo2 is not None and spo2 < SPO2_MIN and not spo2_sola):
        nueva("amarillo", "spo2", [ev_z("spo2_pct")])
    elif fuera:
        nueva("amarillo", "individual", [ev_z(v) for v in sorted(fuera)])
    if valores.get("orina_l") is not None and valores["orina_l"] < ORINA_MIN:
        nueva("amarillo", "renal", [dict(t="lim", var="orina_l", valor=float(valores["orina_l"]), limite=ORINA_MIN)])
    if valores.get("ejercicio_min") is not None and valores["ejercicio_min"] < EJERCICIO_MIN:
        nueva("amarillo", "ejercicio", [dict(t="lim", var="ejercicio_min", valor=float(valores["ejercicio_min"]),
                                             limite=EJERCICIO_MIN)])
    if valores.get("pas_mmhg") is not None and valores.get("pad_mmhg") is not None \
            and valores.get("glucosa_mgdl") is not None:
        for codigo, nivel, ev in reglas_fijas(valores):
            nueva(nivel, codigo, ev)
    if valores.get("vision_cambios"):
        nueva("amarillo", "vision", [dict(t="txt", valor=str(valores["vision_cambios"]))])
    if valores.get("animo_1a5") is not None and valores["animo_1a5"] <= 2:
        nueva("amarillo", "animo", [dict(t="lim", var="animo_1a5", valor=float(valores["animo_1a5"]), limite=3)])
    return res


def indice_preparacion(mision):
    """Índice de preparación 0-100 de cada astronauta y día.
    Resta puntos por cada variable que se aleja de su normal (en el sentido malo)
    y por los umbrales fijos. >= 70 y sin alerta roja: apto para tareas críticas (EVA)."""
    z = puntajes_z(mision)
    malo = pd.DataFrame({
        "fc_lpm": z["fc_lpm"].clip(lower=0), "temp_c": z["temp_c"].clip(lower=0),
        "resp_rpm": z["resp_rpm"].clip(lower=0), "sueno_h": (-z["sueno_h"]).clip(lower=0),
        "reaccion_ms": z["reaccion_ms"].clip(lower=0),
        "spo2_pct": (-z["spo2_pct"]).clip(lower=0).where(mision["spo2_pct"] >= SPO2_IMPOSIBLE, 0),
        "cefalea_0a10": z["cefalea_0a10"].clip(lower=0),
    }).clip(upper=5)
    puntos = 100 - 4 * malo.sum(axis=1)
    puntos -= (mision["orina_l"] < ORINA_MIN) * 10
    puntos -= (mision["ejercicio_min"] < EJERCICIO_MIN) * 5
    puntos -= ((mision["pas_mmhg"] >= PAS_ALTA) | (mision["pad_mmhg"] >= PAD_ALTA)
               | (mision["pas_mmhg"] < PAS_BAJA)) * 5
    puntos -= ((mision["glucosa_mgdl"] >= GLU_ALTA) | (mision["glucosa_mgdl"] < GLU_BAJA)) * 5
    puntos -= (mision["animo_1a5"] <= 2) * 10
    return puntos.clip(lower=0, upper=100).round()


def cargar_o_generar():
    """Lee data/mision.csv si existe; si no, genera la misión."""
    archivo = CARPETA_DATOS / "mision.csv"
    if archivo.exists():
        mision = pd.read_csv(archivo, parse_dates=["fecha"])
        mision["fecha"] = mision["fecha"].dt.date
    else:
        mision = generar_mision(obtener_tormentas())
    mision["preparacion"] = indice_preparacion(mision)
    return mision, generar_alertas(mision)


if __name__ == "__main__":
    CARPETA_DATOS.mkdir(exist_ok=True)
    mision = generar_mision(obtener_tormentas())
    alertas = generar_alertas(mision)
    mision.to_csv(CARPETA_DATOS / "mision.csv", index=False)
    alertas.to_csv(CARPETA_DATOS / "alertas.csv", index=False)
    print("Probando la robustez del motor con 30 misiones distintas...")
    prueba_robustez().to_csv(CARPETA_DATOS / "robustez.csv", index=False)
    print(f"Listo: {len(mision)} filas en data/mision.csv y {len(alertas)} alertas en data/alertas.csv")
