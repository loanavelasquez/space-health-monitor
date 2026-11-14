"""
TEMA VISUAL - Crew Health Monitor
NASA Space Apps Challenge 2026

Solo apariencia: colores, tipografías, animaciones y piezas de HTML (barra de misión,
tarjetas, sellos, anillos). No contiene lógica médica: todos los valores llegan ya
calculados desde app.py, astronauta.py y generador.py.
"""

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# Paleta (los mismos tonos se usan en CSS y en Python)
FONDO = "#050a14"
PANEL = "#0c1b2c"
CIAN = "#3ee0ff"
AZUL = "#2f7bff"
TEXTO = "#d9e6f5"
APAGADO = "#8aa0b8"

# ===========================================================================
# TEXTOS DE LA BARRA DE MISIÓN
# ===========================================================================
H = {
    "Español": dict(mision="Misión", mision_v="Marte · fase de viaje", tmas="Tiempo de misión", dia="Día",
                    fecha="Fecha", nave="Estado de la nave", nominal="Nominal", enlace="Enlace con la Tierra",
                    sin_contacto="Sin contacto", retraso="~{m} min de retraso", rad="Dosis acumulada",
                    sistema="Centro de operaciones médicas"),
    "English": dict(mision="Mission", mision_v="Mars · transit phase", tmas="Mission elapsed time", dia="Day",
                    fecha="Date", nave="Spacecraft status", nominal="Nominal", enlace="Earth link",
                    sin_contacto="No contact", retraso="~{m} min delay", rad="Cumulative dose",
                    sistema="Medical operations center"),
}

# ===========================================================================
# CSS GLOBAL
# ===========================================================================
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --fondo: #050a14; --panel: rgba(12, 27, 44, .82); --panel-solido: #0c1b2c; --petroleo: #0e2a3a;
  --linea: rgba(98, 180, 220, .16); --linea-fuerte: rgba(62, 224, 255, .38);
  --texto: #d9e6f5; --apagado: #8aa0b8; --cian: #3ee0ff; --azul: #2f7bff;
  --ok: #35d49a; --aviso: #ffb547; --critico: #ff5a5f; --sensor: #8a96a8;
  --titulo: 'Chakra Petch', 'Rajdhani', sans-serif; --cuerpo: 'IBM Plex Sans', system-ui, sans-serif;
  --mono: 'JetBrains Mono', ui-monospace, monospace;
}

/* ---------- Fondo: espacio profundo con estrellas y retícula ---------- */
.stApp {
  background:
    radial-gradient(1px 1px at 12% 18%, rgba(255,255,255,.55) 50%, transparent 51%),
    radial-gradient(1px 1px at 68% 8%, rgba(255,255,255,.4) 50%, transparent 51%),
    radial-gradient(1.4px 1.4px at 84% 42%, rgba(160,220,255,.5) 50%, transparent 51%),
    radial-gradient(1px 1px at 33% 72%, rgba(255,255,255,.35) 50%, transparent 51%),
    radial-gradient(1px 1px at 52% 38%, rgba(255,255,255,.3) 50%, transparent 51%),
    radial-gradient(1.2px 1.2px at 91% 86%, rgba(255,255,255,.4) 50%, transparent 51%),
    radial-gradient(ellipse 60% 45% at 85% -5%, rgba(47,123,255,.16), transparent 70%),
    radial-gradient(ellipse 50% 40% at -5% 105%, rgba(62,224,255,.08), transparent 70%),
    linear-gradient(rgba(98,180,220,.035) 1px, transparent 1px) 0 0 / 48px 48px,
    linear-gradient(90deg, rgba(98,180,220,.035) 1px, transparent 1px) 0 0 / 48px 48px,
    var(--fondo);
  background-attachment: fixed;
  color: var(--texto);
  font-family: var(--cuerpo);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { padding-top: 2.2rem; max-width: 1440px; }
[data-testid="stAppDeployButton"] { display: none; }

/* ---------- Tipografía ---------- */
h1, h2, h3, h4, [data-testid="stHeading"] * { font-family: var(--titulo) !important; letter-spacing: .02em; }
h3 { font-size: 1.25rem !important; }
[data-testid="stMarkdownContainer"] code { font-family: var(--mono); }
[data-testid="stCaptionContainer"] { color: var(--apagado) !important; }

/* ---------- Barra lateral: consola de control ---------- */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #081426 0%, #050c18 100%);
  border-right: 1px solid var(--linea); }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { font-family: var(--titulo); text-transform: uppercase;
  letter-spacing: .08em; font-size: .78rem; color: var(--apagado); }
[data-testid="stSidebarUserContent"] [data-testid="stMarkdownContainer"] p { font-size: .86rem; line-height: 1.45; }
.consola-marca { font-family: var(--titulo); font-size: .72rem; letter-spacing: .22em; color: var(--cian);
  text-transform: uppercase; padding: 6px 0 10px; border-bottom: 1px solid var(--linea); margin-bottom: 6px; }

/* ---------- Pestañas tipo consola ---------- */
[data-testid="stTabs"] [role="tablist"] { gap: 6px; border-bottom: 1px solid var(--linea); }
[data-testid="stTab"] { font-family: var(--titulo); text-transform: uppercase; letter-spacing: .08em;
  padding: 8px 16px !important; border-radius: 8px 8px 0 0; background: rgba(12,27,44,.5); }
[data-testid="stTab"][aria-selected="true"] { background: linear-gradient(180deg, rgba(62,224,255,.16), rgba(62,224,255,.02));
  color: var(--cian); box-shadow: inset 0 -2px 0 var(--cian); }
[data-testid="stTab"] p { font-size: .85rem !important; }
[data-testid="stTabPanel"] { animation: entrar .35s ease-out; }

/* ---------- Botones: teclas de consola ---------- */
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"] {
  background: rgba(14,42,58,.6); border: 1px solid var(--linea-fuerte); color: var(--texto);
  font-family: var(--titulo); letter-spacing: .05em; transition: all .18s ease; }
[data-testid="stBaseButton-secondary"]:hover, [data-testid="stBaseButton-secondaryFormSubmit"]:hover {
  border-color: var(--cian); color: var(--cian); box-shadow: 0 0 0 1px rgba(62,224,255,.25), 0 0 18px rgba(62,224,255,.18); }
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
  background: linear-gradient(135deg, #3ee0ff 0%, #2f7bff 100%); color: #021019; border: 0;
  font-family: var(--titulo); font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
  box-shadow: 0 6px 22px rgba(47,123,255,.35); transition: transform .15s ease, box-shadow .2s ease; }
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover {
  box-shadow: 0 8px 30px rgba(62,224,255,.5); transform: translateY(-1px); color: #021019; }
button:active { transform: scale(.97) !important; }
button:disabled { opacity: .55; }

/* Selectores de opciones (astronauta, estación, parte del cuerpo) */
[data-testid="stButtonGroup"] button { font-family: var(--titulo); letter-spacing: .04em; transition: all .18s ease; }
[data-testid="stButtonGroup"] button[data-selected="true"] { box-shadow: 0 0 16px rgba(62,224,255,.28); }
[data-testid="stButtonGroup"] [role="radiogroup"] { flex-wrap: wrap; overflow: visible !important; row-gap: 6px; }
[data-testid="stButtonGroup"] button[data-variant="segmented_control"] { flex: 1 1 auto; }

/* ---------- Paneles nativos ---------- */
[data-testid="stMetric"] { background: var(--panel); border: 1px solid var(--linea); border-radius: 12px;
  padding: 12px 16px; position: relative; overflow: hidden; }
[data-testid="stMetric"]::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: linear-gradient(180deg, var(--cian), transparent); }
[data-testid="stMetricLabel"] p { font-family: var(--titulo); text-transform: uppercase; letter-spacing: .08em;
  font-size: .74rem !important; color: var(--apagado); }
[data-testid="stMetricLabel"] * { white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }
[data-testid="stMetricValue"] { font-family: var(--mono); font-weight: 600; }
[data-testid="stExpander"] details { background: rgba(8,20,36,.6); border: 1px solid var(--linea); border-radius: 10px; }
[data-testid="stExpander"] summary p { font-family: var(--titulo); letter-spacing: .04em; }
[data-testid="stForm"] { background: transparent; border: 0; padding: 0; }
[data-testid="stCode"] pre { background: #030810 !important; border: 1px solid var(--linea);
  border-left: 3px solid var(--cian); font-family: var(--mono); }
[data-testid="stNumberInputField"], [data-testid="stTextInputField"] { font-family: var(--mono); }
[data-testid="stProgressBarTrack"] > div > div { background: linear-gradient(90deg, var(--azul), var(--cian)) !important; }
[data-testid="stAlert"] { border-radius: 10px; }
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"] { background: var(--panel); border: 1px solid var(--linea);
  border-radius: 12px; padding: 6px; }
hr { border-color: var(--linea) !important; }

/* ---------- Animaciones ---------- */
@keyframes entrar { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@keyframes escaneo { 0% { top: 4%; opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { top: 94%; opacity: 0; } }
@keyframes pulso { 0%, 100% { opacity: 1; } 50% { opacity: .45; } }
@keyframes latir { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.06); } }
@keyframes sellar { 0% { opacity: 0; transform: rotate(-14deg) scale(2.2); } 60% { opacity: 1; transform: rotate(-8deg) scale(.94); }
                    100% { opacity: 1; transform: rotate(-8deg) scale(1); } }
@keyframes anillo { from { stroke-dashoffset: var(--total); } to { stroke-dashoffset: var(--fin); } }
@keyframes barrido { from { transform: translateX(-100%); } to { transform: translateX(100%); } }
@keyframes llenar { from { width: 0; } }
.entrar { animation: entrar .45s ease-out both; }
.entrar-2 { animation: entrar .45s .08s ease-out both; }
.entrar-3 { animation: entrar .45s .16s ease-out both; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }

/* ---------- Barra de misión (HUD) ---------- */
.hud { display: grid; grid-template-columns: 1fr; gap: 12px; padding: 14px 16px; margin-bottom: 16px;
  background: linear-gradient(90deg, rgba(14,42,58,.85), rgba(10,22,40,.85)); border: 1px solid var(--linea);
  border-radius: 14px; position: relative; overflow: hidden; }
.hud::after { content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(62,224,255,.07), transparent);
  animation: barrido 6s linear infinite; pointer-events: none; }
.hud-marca { display: flex; align-items: center; gap: 12px; min-width: 0; }
.hud-logo { width: 42px; height: 42px; flex: none; }
.hud-titulo { font-family: var(--titulo); font-weight: 700; font-size: 1.3rem; letter-spacing: .12em; text-transform: uppercase; line-height: 1.1; }
.hud-sub { font-size: .76rem; color: var(--apagado); line-height: 1.35; }
.hud-celdas { display: grid; grid-template-columns: repeat(auto-fit, minmax(122px, 1fr)); gap: 8px; }
.hud-celda { background: rgba(3,10,20,.55); border: 1px solid var(--linea); border-radius: 10px; padding: 7px 12px; min-width: 0; }
.hud-etq { font-family: var(--titulo); font-size: .6rem; letter-spacing: .14em; text-transform: uppercase; color: var(--apagado);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hud-val { font-family: var(--mono); font-size: .84rem; font-weight: 600; line-height: 1.3; margin-top: 2px; }
.led { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: 1px;
  background: var(--c, var(--ok)); box-shadow: 0 0 8px var(--c, var(--ok)); animation: pulso 2s ease-in-out infinite; }

/* ---------- Títulos de sección ---------- */
.seccion { display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 10px; row-gap: 2px; margin: 18px 0 8px; }
.seccion-t { white-space: nowrap; font-family: var(--titulo); font-size: 1.05rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
.seccion-t::before { content: "// "; color: var(--cian); }
.seccion-s { font-size: .8rem; color: var(--apagado); }

/* ---------- Paneles y tarjetas propias ---------- */
.panel { background: var(--panel); border: 1px solid var(--linea); border-radius: 14px; padding: 14px 16px; position: relative; }
.panel-cab { font-family: var(--titulo); font-size: .7rem; letter-spacing: .16em; text-transform: uppercase; color: var(--apagado);
  display: flex; justify-content: space-between; margin-bottom: 8px; }
.esquinas { position: relative; }
.esquinas::before, .esquinas::after { content: ""; position: absolute; width: 14px; height: 14px; border: 2px solid var(--cian); opacity: .7; }
.esquinas::before { top: -1px; left: -1px; border-right: 0; border-bottom: 0; border-radius: 6px 0 0 0; }
.esquinas::after { bottom: -1px; right: -1px; border-left: 0; border-top: 0; border-radius: 0 0 6px 0; }
.chip { display: inline-flex; align-items: center; gap: 4px; padding: 2px 10px; border-radius: 999px; font-size: .74rem;
  font-weight: 600; border: 1px solid color-mix(in srgb, var(--c, var(--cian)) 55%, transparent);
  background: color-mix(in srgb, var(--c, var(--cian)) 14%, transparent); color: var(--c, var(--cian)); white-space: nowrap; }
.sello { display: inline-block; font-family: var(--titulo); font-weight: 700; text-transform: uppercase; letter-spacing: .12em;
  font-size: .8rem; padding: 5px 12px; border: 2.5px solid var(--c); color: var(--c); border-radius: 6px;
  transform: rotate(-8deg); animation: sellar .55s cubic-bezier(.2,.9,.3,1.3) both; background: color-mix(in srgb, var(--c) 8%, transparent);
  box-shadow: inset 0 0 0 2px color-mix(in srgb, var(--c) 20%, transparent); }
.num { font-family: var(--mono); font-weight: 600; }
.apagado { color: var(--apagado); }

/* Anillo de preparación */
.anillo { position: relative; display: inline-block; }
.anillo svg circle.prog { animation: anillo 1.2s ease-out both; }
.anillo-val { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.anillo-num { font-family: var(--mono); font-weight: 600; line-height: 1; }
.anillo-etq { font-family: var(--titulo); font-size: .56rem; letter-spacing: .14em; color: var(--apagado); text-transform: uppercase; }

/* Barras de instrumento */
.barra { height: 6px; border-radius: 4px; background: rgba(120,160,200,.14); overflow: hidden; position: relative; }
.barra > i { display: block; height: 100%; border-radius: 4px; background: var(--c, var(--cian)); box-shadow: 0 0 10px var(--c, var(--cian));
  animation: llenar 1s ease-out both; }
.barra > b { position: absolute; top: -3px; bottom: -3px; width: 2px; background: #fff; opacity: .7; }

/* Instrumentos (ambiente) */
.instrumentos { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }
.inst { background: var(--panel); border: 1px solid var(--linea); border-radius: 12px; padding: 12px 14px; }
.inst-etq { font-family: var(--titulo); font-size: .66rem; letter-spacing: .14em; text-transform: uppercase; color: var(--apagado); }
.inst-val { font-family: var(--mono); font-size: 1.55rem; font-weight: 600; margin: 2px 0 6px; }
.inst-val small { font-size: .8rem; color: var(--apagado); margin-left: 4px; }
.inst-sub { font-size: .74rem; color: var(--apagado); margin-top: 6px; }

/* Tarjetas de alerta (estilo Reigns: una decisión por tarjeta) */
.alerta { display: flex; gap: 14px; padding: 14px 16px; margin: 10px 0 4px; border-radius: 14px; position: relative; overflow: hidden;
  background: linear-gradient(135deg, color-mix(in srgb, var(--c) 13%, rgba(10,22,40,.92)), rgba(8,18,32,.92));
  border: 1px solid color-mix(in srgb, var(--c) 45%, transparent); box-shadow: 0 10px 26px rgba(0,0,0,.28); }
.alerta::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--c); box-shadow: 0 0 14px var(--c); }
.alerta.critica .alerta-ico { animation: latir 1.4s ease-in-out infinite; }
.alerta-ico { font-size: 1.7rem; line-height: 1; flex: none; width: 46px; height: 46px; display: flex; align-items: center; justify-content: center;
  border-radius: 12px; background: color-mix(in srgb, var(--c) 18%, transparent); border: 1px solid color-mix(in srgb, var(--c) 40%, transparent); }
.alerta-cuerpo { flex: 1; min-width: 0; }
.alerta-meta { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 4px; }
.alerta-tit { font-family: var(--titulo); font-weight: 700; font-size: 1.05rem; letter-spacing: .03em; }
.alerta-txt { font-size: .9rem; line-height: 1.45; margin-top: 2px; }
.alerta-txt b { color: #fff; }
.alerta .sello { position: absolute; right: 14px; bottom: 10px; font-size: .68rem; }
.alerta.recibida { opacity: .78; }

/* Tarjetas de tripulante (expediente) */
.trip { background: var(--panel); border: 1px solid var(--linea); border-radius: 16px; padding: 14px; position: relative; overflow: hidden; height: 100%; }
.trip::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 3px; background: var(--c); box-shadow: 0 0 14px var(--c); }
.trip-cab { display: flex; align-items: center; gap: 10px; }
.avatar { width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem;
  background: color-mix(in srgb, var(--a) 22%, transparent); border: 1px solid color-mix(in srgb, var(--a) 60%, transparent); flex: none; }
.trip-nombre { font-family: var(--titulo); font-weight: 700; font-size: 1.2rem; letter-spacing: .08em; }
.trip-estado { font-size: .78rem; color: var(--c); font-weight: 600; }
.trip .sello { font-size: .6rem; padding: 3px 8px; margin: 10px 0 2px 2px; transform-origin: left center; }
.lecturas { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: .82rem; }
.lecturas td { border: 0 !important; padding: 3px 0; border-bottom: 1px dashed rgba(98,180,220,.1) !important; }
.lecturas td:nth-child(2) { text-align: right; font-family: var(--mono); font-weight: 600; }
.lecturas td:nth-child(3) { text-align: right; font-family: var(--mono); font-size: .72rem; padding-left: 8px; width: 46px; }
.lecturas tr.mal td:nth-child(2) { color: var(--critico); }

/* ---------- Modo astronauta ---------- */
.credencial { display: flex; gap: 14px; align-items: center; }
.cred-foto { width: 64px; height: 64px; border-radius: 14px; font-size: 2rem; display: flex; align-items: center; justify-content: center; flex: none;
  background: radial-gradient(circle at 35% 30%, color-mix(in srgb, var(--a) 45%, transparent), rgba(5,10,20,.8));
  border: 1px solid color-mix(in srgb, var(--a) 70%, transparent); box-shadow: 0 0 22px color-mix(in srgb, var(--a) 30%, transparent); }
.cred-id { font-family: var(--titulo); font-size: .66rem; letter-spacing: .2em; color: var(--apagado); text-transform: uppercase; }
.cred-nombre { font-family: var(--titulo); font-weight: 700; font-size: 1.5rem; letter-spacing: .08em; line-height: 1.1; }
.cred-hola { font-size: .86rem; color: var(--apagado); }
.kpis { display: grid; grid-template-columns: minmax(0, 1.5fr) repeat(3, minmax(0, 1fr)); gap: 10px; align-items: stretch; }
.kpi { background: rgba(3,10,20,.5); border: 1px solid var(--linea); border-radius: 12px; padding: 10px 12px; display: flex; flex-direction: column; justify-content: center; }
.kpi-val { font-family: var(--mono); font-size: 1.35rem; font-weight: 600; margin: 4px 0 6px; white-space: nowrap; }
.kpi .inst-etq { letter-spacing: .1em; line-height: 1.25; }
.kpi-val small { font-size: .75rem; color: var(--apagado); }
.kpi-prep { display: flex; align-items: center; gap: 10px; }
@media (max-width: 640px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } .kpi-prep { grid-column: span 2; } }

/* Progreso del turno */
.turno { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin: 12px 0 4px; }
.paso { border: 1px solid var(--linea); border-radius: 10px; padding: 8px 10px; background: rgba(3,10,20,.45); position: relative; overflow: hidden; }
.paso.hecho { border-color: color-mix(in srgb, var(--ok) 50%, transparent); background: color-mix(in srgb, var(--ok) 10%, rgba(3,10,20,.5)); }
.paso-n { font-family: var(--titulo); font-size: .6rem; letter-spacing: .16em; color: var(--apagado); text-transform: uppercase; }
.paso-t { font-size: .8rem; font-weight: 600; line-height: 1.25; }
.paso-p { position: absolute; right: 8px; top: 6px; font-family: var(--mono); font-size: .7rem; color: var(--apagado); }
.paso.hecho .paso-p { color: var(--ok); }
@media (max-width: 640px) { .turno { grid-template-columns: repeat(2, minmax(0, 1fr)); } }

/* Estación activa: aparece con transición */
[class*="st-key-est_"] { animation: entrar .4s ease-out; }
.st-key-est_checkin { max-width: 820px; margin: 0 auto; }
.st-key-selector_est { margin-top: 10px; }

/* Escáner del gemelo */
.escaner { position: relative; border-radius: 16px; padding: 14px 10px 8px; overflow: hidden;
  background: radial-gradient(ellipse at 50% 40%, rgba(47,123,255,.14), rgba(3,8,16,.9) 70%); border: 1px solid var(--linea); }
.escaner::after { content: ""; position: absolute; left: 6%; right: 6%; height: 2px; top: 4%;
  background: linear-gradient(90deg, transparent, var(--cian), transparent); box-shadow: 0 0 14px var(--cian);
  animation: escaneo 3.2s ease-in-out infinite; }
.escaner .panel-cab { padding: 0 6px; }
.gem-sel { animation: pulso 1.6s ease-in-out infinite; }
.leyenda { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; margin-top: 6px; }
.lectura { display: grid; grid-template-columns: 10px 1fr auto; gap: 10px; align-items: center; padding: 8px 10px; margin: 6px 0;
  border-radius: 10px; background: rgba(3,10,20,.5); border: 1px solid var(--linea); }
.lectura .pt { width: 10px; height: 10px; border-radius: 50%; background: var(--c); box-shadow: 0 0 8px var(--c); }
.lectura .nm { font-size: .84rem; }
.lectura .nm small { display: block; color: var(--apagado); font-size: .72rem; }
.lectura .vl { font-family: var(--mono); font-weight: 600; font-size: 1.05rem; }
.dossier-cab { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
.dossier-t { font-family: var(--titulo); font-size: 1.35rem; font-weight: 700; letter-spacing: .05em; }

/* Check-in por tarjetas */
.carta-cab { display: flex; align-items: center; gap: 14px; margin-bottom: 6px; }
.carta-ico { font-size: 2.2rem; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; border-radius: 16px;
  background: linear-gradient(135deg, rgba(62,224,255,.18), rgba(47,123,255,.08)); border: 1px solid var(--linea-fuerte); flex: none; }
.carta-n { font-family: var(--titulo); font-size: .66rem; letter-spacing: .2em; color: var(--cian); text-transform: uppercase; }
.carta-t { font-family: var(--titulo); font-size: 1.4rem; font-weight: 700; letter-spacing: .04em; line-height: 1.15; }
.carta-s { font-size: .84rem; color: var(--apagado); }
.puntos-pasos { display: flex; gap: 6px; margin: 4px 0 12px; }
.puntos-pasos i { flex: 1; height: 4px; border-radius: 3px; background: rgba(120,160,200,.18); }
.puntos-pasos i.si { background: linear-gradient(90deg, var(--azul), var(--cian)); box-shadow: 0 0 8px rgba(62,224,255,.5); }
.resumen-chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 12px; }
.st-key-carta { background: linear-gradient(160deg, rgba(14,42,58,.75), rgba(8,18,32,.9)); border: 1px solid var(--linea-fuerte);
  border-radius: 18px; padding: 18px 20px 10px; box-shadow: 0 18px 40px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.04); }

/* Transmisión completada */
.transmision { text-align: center; padding: 18px; border-radius: 16px; margin-bottom: 10px; position: relative; overflow: hidden;
  background: radial-gradient(ellipse at 50% 0%, rgba(53,212,154,.22), rgba(8,18,32,.9) 70%); border: 1px solid rgba(53,212,154,.45); }
.transmision .ondas { font-size: 2rem; animation: latir 1s ease-in-out 3; }
.transmision .tt { font-family: var(--titulo); font-weight: 700; letter-spacing: .16em; text-transform: uppercase; color: var(--ok); }

/* Insignias */
.insignias { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; }
.insignia { border-radius: 12px; padding: 10px; border: 1px solid var(--linea); background: rgba(3,10,20,.5); }
.insignia.si { border-color: rgba(255,181,71,.55); background: linear-gradient(135deg, rgba(255,181,71,.14), rgba(3,10,20,.5)); box-shadow: 0 0 18px rgba(255,181,71,.12); }
.insignia.no { opacity: .45; filter: grayscale(1); }
.insignia .in { font-weight: 600; font-size: .86rem; }
.insignia .id { font-size: .72rem; color: var(--apagado); line-height: 1.3; margin-top: 2px; }

/* Texto largo legible (Cómo funciona) */
.st-key-como { max-width: 900px; }
.st-key-como h3 { color: var(--cian); margin-top: 1.2rem; }
</style>
"""

_LOGO = """<svg class='hud-logo' viewBox='0 0 48 48'><defs><linearGradient id='lg' x1='0' y1='0' x2='1' y2='1'>
<stop offset='0' stop-color='#3ee0ff'/><stop offset='1' stop-color='#2f7bff'/></linearGradient></defs>
<circle cx='24' cy='24' r='21' fill='none' stroke='url(#lg)' stroke-width='2' opacity='.5'/>
<ellipse cx='24' cy='24' rx='21' ry='8' fill='none' stroke='url(#lg)' stroke-width='1.5' transform='rotate(-25 24 24)'/>
<path d='M10 25 h7 l3 -7 l4 14 l3 -9 l2 2 h9' fill='none' stroke='#3ee0ff' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'/>
<circle cx='41' cy='16' r='2.4' fill='#ffb547'/></svg>"""


def aplicar():
    """Inyecta el CSS y deja la plantilla oscura para todos los gráficos."""
    st.markdown(_CSS, unsafe_allow_html=True)
    eje = dict(gridcolor="rgba(110,180,230,.09)", linecolor="rgba(110,180,230,.25)", zeroline=False,
               tickfont=dict(family="JetBrains Mono, monospace", size=11))
    pio.templates["mision"] = go.layout.Template(layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(4,12,24,.55)",
        font=dict(family="IBM Plex Sans, sans-serif", color="#a9bdd3", size=12),
        xaxis=eje, yaxis=eje,
        hoverlabel=dict(bgcolor="#0b1a2c", bordercolor=CIAN, font=dict(family="JetBrains Mono, monospace", color=TEXTO)),
        legend=dict(font=dict(color="#c4d4e6"), bgcolor="rgba(0,0,0,0)")))
    pio.templates.default = "plotly_dark+mision"


# ===========================================================================
# PIEZAS DE HTML
# ===========================================================================
def hud(idioma, titulo, subtitulo, celdas):
    """Barra superior de la misión. celdas = [(etiqueta, valor, color_led o None), ...]"""
    h = H[idioma]
    html = "".join(
        f"<div class='hud-celda'><div class='hud-etq'>{e}</div><div class='hud-val'>"
        + (f"<span class='led' style='--c:{c}'></span>" if c else "") + f"{v}</div></div>"
        for e, v, c in celdas)
    return (f"<div class='hud entrar'><div class='hud-marca'>{_LOGO}<div><div class='hud-titulo'>{titulo}</div>"
            f"<div class='hud-sub'>{h['sistema']} · {subtitulo}</div></div></div>"
            f"<div class='hud-celdas'>{html}</div></div>")


def seccion(titulo, sub=""):
    return (f"<div class='seccion entrar'><span class='seccion-t'>{titulo}</span>"
            + (f"<span class='seccion-s'>{sub}</span>" if sub else "") + "</div>")


def chip(texto, color=None):
    return f"<span class='chip' style='--c:{color or CIAN}'>{texto}</span>"


def sello(texto, color):
    return f"<span class='sello' style='--c:{color}'>{texto}</span>"


def barra(pct, color=None, marca=None):
    pct = max(0, min(100, pct))
    m = f"<b style='left:{max(0, min(100, marca))}%'></b>" if marca is not None else ""
    return f"<div class='barra'><i style='width:{pct:.0f}%;--c:{color or CIAN}'></i>{m}</div>"


def anillo(valor, maximo, color, etiqueta="", tam=92):
    """Anillo que se llena con animación (p. ej. índice de preparación)."""
    r = tam / 2 - 7
    total = 2 * 3.14159 * r
    fin = total * (1 - max(0, min(1, valor / maximo)))
    return (f"<div class='anillo' style='width:{tam}px;height:{tam}px'>"
            f"<svg width='{tam}' height='{tam}' viewBox='0 0 {tam} {tam}' style='transform:rotate(-90deg)'>"
            f"<circle cx='{tam/2}' cy='{tam/2}' r='{r}' fill='none' stroke='rgba(120,160,200,.15)' stroke-width='7'/>"
            f"<circle class='prog' cx='{tam/2}' cy='{tam/2}' r='{r}' fill='none' stroke='{color}' stroke-width='7' "
            f"stroke-linecap='round' stroke-dasharray='{total:.1f}' stroke-dashoffset='{fin:.1f}' "
            f"style='--total:{total:.1f};--fin:{fin:.1f};filter:drop-shadow(0 0 5px {color})'/></svg>"
            f"<div class='anillo-val'><span class='anillo-num' style='font-size:{tam/3.6:.0f}px'>{valor}</span>"
            f"<span class='anillo-etq'>{etiqueta}</span></div></div>")


def instrumento(etiqueta, valor, unidad="", sub="", pct=None, color=None, marca=None):
    b = barra(pct, color, marca) if pct is not None else ""
    return (f"<div class='inst entrar'><div class='inst-etq'>{etiqueta}</div>"
            f"<div class='inst-val' style='color:{color or TEXTO}'>{valor}<small>{unidad}</small></div>{b}"
            + (f"<div class='inst-sub'>{sub}</div>" if sub else "") + "</div>")


def tarjeta_alerta(icono, color, titulo, chips, lineas, critica=False, recibida_txt=None):
    """Tarjeta de alerta: icono, etiquetas (origen, triaje), título y qué hacer."""
    clase = "alerta entrar" + (" critica" if critica else "") + (" recibida" if recibida_txt else "")
    meta = "".join(chips)
    cuerpo = "".join(f"<div class='alerta-txt'>{l}</div>" for l in lineas)
    s = sello(recibida_txt, "#35d49a") if recibida_txt else ""
    return (f"<div class='{clase}' style='--c:{color}'><div class='alerta-ico'>{icono}</div>"
            f"<div class='alerta-cuerpo'><div class='alerta-meta'>{meta}</div><div class='alerta-tit'>{titulo}</div>"
            f"{cuerpo}</div>{s}</div>")
