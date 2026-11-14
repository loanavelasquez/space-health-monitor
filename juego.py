"""
MODO JUEGO - "Misión Cóndor"
Crew Health Monitor · NASA Space Apps Challenge 2026

Un juego narrativo (inspirado en Papers, Please y Reigns) donde cada tripulante se mide
a sí mismo en la estación médica y VITA -el monitor de salud, que es esta misma app-
le muestra su ficha. Todos los valores salen de data/mision.csv y todas las alertas
del motor de generador.py: el juego NO tiene lógica médica propia, solo la muestra.

Python prepara los datos y el componente (componentes/juego/index.html) dibuja el juego.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import astronauta
import generador as gen

CARPETA = Path(__file__).parent
_juego = components.declare_component("mision_condor", path=str(CARPETA / "componentes" / "juego"))

# Días del viaje que se juegan (el último es la llegada: lista de descenso)
DIAS_JUGABLES = [9, 21, 26, 29, 31]

# Variables que aparecen en la ficha de cada tripulante
VARS_FICHA = ["pas_mmhg", "pad_mmhg", "fc_lpm", "spo2_pct", "temp_c", "glucosa_mgdl", "sueno_h", "animo_1a5",
              "resp_rpm", "cefalea_0a10", "reaccion_ms", "orina_l", "ejercicio_min", "perdida_osea_pct"]


def _limpio(v):
    if isinstance(v, (bool,)):
        return v
    try:
        f = float(v)
        return None if pd.isna(f) else round(f, 2)
    except (TypeError, ValueError):
        return str(v)


def preparar_datos(c):
    """Arma el paquete (JSON) que recibe el juego. Solo lee datos y resultados del motor."""
    mision, alertas, base, idioma = c["mision"], c["alertas"], c["base"], c["idioma"]
    msg, reglas, fuentes, protocolo = c["msg"], c["reglas"], c["fuentes"], c["protocolo"]
    dias = {}
    for d in DIAS_JUGABLES:
        hoy = mision[mision["dia_mision"] == d].set_index("astronauta")
        amb = hoy.iloc[0]
        lista = []
        for _, a in alertas[alertas["dia_mision"] == d].iterrows():
            titulo, accion = msg[a["codigo"]]
            lista.append(dict(
                codigo=a["codigo"], nivel=a["nivel"], origen=a["origen"], triaje=a["triaje"],
                afectados=[x.strip() for x in str(a["afectados"]).split(",")],
                detalle=str(a["detalle"]) if isinstance(a["detalle"], str) else "",
                titulo=titulo, accion=accion, accion_apagon=protocolo.get(a["codigo"], accion),
                regla=reglas[a["codigo"]], fuentes=[dict(n=n, u=u) for n, u in fuentes[a["codigo"]]],
                evidencia=[l.replace("**", "") for l in c["texto_evidencia"](a["evidencia"])]))
        tripulantes = {}
        for astro, f in hoy.iterrows():
            base_astro = base.loc[astro]
            valores = {v: _limpio(f[v]) for v in VARS_FICHA}
            propias = [a for a in lista if astro in a["afectados"]]
            estados = {v: astronauta._estado_variable(v, f[v], base_astro) for v in VARS_FICHA}
            normales = {v: round(float(base_astro[(v, "mean")]), 1) for v in VARS_FICHA if v in gen.VARIABLES}
            # cambio vs. su normal en % (para frases como "respiración +28 % sobre tu normal")
            cambio = {v: round((float(f[v]) - normales[v]) / normales[v] * 100) for v in normales if normales[v]}
            niveles = {p: astronauta._nivel_parte(p, propias, dict(f), base_astro) for p in astronauta.PARTES}
            solo_suyas = [a for a in propias if a["codigo"] not in {"tormenta", "co2", "sensor_co2", "ambiente"}]
            niveles_propios = {p: astronauta._nivel_parte(p, solo_suyas, dict(f), base_astro) for p in astronauta.PARTES}
            prep = int(f["preparacion"])
            rojo = any(a["nivel"] == "rojo" and a["origen"] != "sensor" for a in propias)
            tripulantes[astro] = dict(valores=valores, estados=estados, normales=normales, cambio=cambio,
                                      niveles=niveles, niveles_propios=niveles_propios, prep=prep, apto=bool(prep >= 70 and not rojo),
                                      alertas=[a["codigo"] for a in propias])
        dias[str(d)] = dict(
            dia=d, fecha=f"{amb['fecha']:%Y-%m-%d}", tormenta=bool(amb["tormenta_solar"]),
            co2=_limpio(amb["co2_mmhg"]), co2_real=_limpio(amb["co2_real_mmhg"]), co2_limite=gen.CO2_LIMITE,
            rad=_limpio(amb["radiacion_msv"]), rad_sin=_limpio(amb["radiacion_sin_refugio_msv"]),
            rad_acum=_limpio(amb["radiacion_acum_msv"]), rad_pct=_limpio(amb["radiacion_pct_limite"]),
            temp_cabina=_limpio(amb["temp_cabina_c"]), alertas=lista, tripulantes=tripulantes)

    # Números reales de la app para la revelación final
    resumen, _, _ = gen.validar(mision, alertas)
    r = mision.drop_duplicates("dia_mision").iloc[-1]
    evitada = float(r["radiacion_acum_sin_refugio_msv"] - r["radiacion_acum_msv"])
    reales = dict(eventos=f"{resumen['eventos_detectados']}/{resumen['eventos']}",
                  dias=f"{resumen['dias_detectados']}/{resumen['dias_evento']}",
                  rad_evitada=round(evitada), rad_pct=round(evitada / float(r["radiacion_acum_sin_refugio_msv"]) * 100))
    try:
        rob = pd.read_csv(CARPETA / "data" / "robustez.csv")
        reales["recall"] = round(float((rob["dias_detectados"] / rob["dias_evento"]).mean() * 100), 1)
        reales["precision"] = round(float((1 - rob["falsas_alarmas"] / rob["alertas"]).mean() * 100), 1)
    except (OSError, KeyError):
        pass

    T = astronauta.A[idioma]
    return dict(
        lang="es" if idioma == "Español" else "en", dias=dias, reales=reales,
        nombres_var=c["nv"], guia=astronauta.GUIA[idioma], que_hace=astronauta.QUE_HACE[idioma],
        partes=T["partes"], estado=T["estado"], retraso=gen.RETRASO_TIERRA_MIN,
        limites=dict(apto=70, spo2_min=gen.SPO2_MIN, fiebre=gen.FIEBRE))


def mostrar(c):
    datos = preparar_datos(c)
    inicio = st.query_params.get("dia") if "dia" in st.query_params else None
    try:
        inicio = int(inicio) if inicio is not None and int(inicio) in DIAS_JUGABLES else None
    except ValueError:
        inicio = None
    resultado = _juego(datos=datos, inicio=inicio, key="mision_condor", default=None)
    # El juego devuelve un resumen al terminar (decisiones y sellos); queda guardado en la sesión
    if resultado:
        st.session_state["juego_resultado"] = resultado
