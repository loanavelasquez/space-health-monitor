/* MISIÓN CÓNDOR · motor del juego
   Recibe de Python (Streamlit) los datos de la misión y las alertas del motor de VITA.
   No calcula nada médico: solo muestra, anima y lleva las barras del juego. */

const ORDEN_DIAS = [9, 21, 26, 29, 31];
const COLORES = { verde: "#35d49a", amarillo: "#ffb547", rojo: "#ff5a5f", sensor: "#8a96a8" };
const TINTA = { verde: "#2e8b57", amarillo: "#b7791f", rojo: "#c0392b", sensor: "#6b7280" };
const COL_ORIGEN = { nave: "#1f7a99", persona: "#6d4fc2", sensor: "#6b7280" };
const CAUSA_DE_ORIGEN = { nave: "nave", persona: "tripulante", sensor: "sensor" };
const CARITAS = ["😫", "😟", "😐", "🙂", "😄"];
const ASTROS = ["A1", "A2", "A3", "A4"];

let DATA = null, LANG = "es", S = null, temporizador = null, medicionTimer = null;

/* ---------- utilidades ---------- */
const $ = (s, r = document) => r.querySelector(s);
const esc = (x) => String(x ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
function D() { return DATA.dias[String(S.dia)]; }
function L(x) {
  if (typeof x === "function") x = x(S, D());
  if (x && typeof x === "object" && ("es" in x || "en" in x)) return x[LANG] ?? x.es;
  return x ?? "";
}
function t(k, vars) {
  let s = TX[LANG][k] ?? TX.es[k] ?? k;
  if (vars) for (const [a, b] of Object.entries(vars)) s = s.split("{" + a + "}").join(b);
  return s;
}
function trip(a) { return D().tripulantes[a]; }
function fmt(v, dec = 1) { return v == null ? "—" : (Math.round(v * 10 ** dec) / 10 ** dec).toLocaleString(LANG === "es" ? "es" : "en"); }
function nv(v) { return DATA.nombres_var[v] || v; }
function peor(...e) { const o = { verde: 0, sensor: 1, amarillo: 2, rojo: 3 }; return e.reduce((a, b) => (o[b] > o[a] ? b : a), "verde"); }
function escenas(dia) {
  const lista = [];
  if (dia === 9 && S.conPrologo) lista.push({ tipo: "prologo" });
  if (DIAS[dia].bitacora && !(dia === 9)) lista.push({ tipo: "bitacora" });
  return lista.concat(DIAS[dia].escenas);
}
function escena() { return escenas(S.dia)[S.idx]; }
function apagonHoy() { return !!DIAS[S.dia].apagon; }

/* ---------- comunicación con Streamlit ---------- */
function enviar(tipo, datos) { window.parent.postMessage(Object.assign({ isStreamlitMessage: true, type: tipo }, datos), "*"); }
let ultimaAltura = 0;
function ajustarAltura() {
  const h = Math.ceil(document.getElementById("app").getBoundingClientRect().height) + 6;
  if (Math.abs(h - ultimaAltura) > 2) { ultimaAltura = h; enviar("streamlit:setFrameHeight", { height: h }); }
}
window.addEventListener("message", (e) => {
  if (!e.data || e.data.type !== "streamlit:render") return;
  const args = e.data.args || {};
  const nuevo = args.datos;
  if (!nuevo) return;
  const cambioIdioma = DATA && nuevo.lang !== LANG;
  DATA = nuevo; LANG = nuevo.lang || "es";
  if (!S) { iniciar(args.inicio); }
  else if (cambioIdioma) { construir(); render(); }
  ajustarAltura();
});

/* ---------- estado ---------- */
function nuevoEstado(dia, conPrologo) {
  return { dia, idx: 0, fase: null, bars: { ...DIAS[dia].inicio }, flags: {}, pos: casas(), actual: null,
    yaMidio: false, tutos: {}, sinTiempo: false, causas: { ok: 0, total: 0 }, sellos: { ok: 0, total: 0 },
    medidas: {}, plan: [], deltas: {}, conPrologo, aislado: {}, decRes: null, sello: null, puntos: {}, retraso: 6, desc: {} };
}
function casas() { const p = {}; ASTROS.forEach((a) => (p[a] = TRIPULACION[a].casa)); return p; }
function iniciar(inicio) {
  const dia = ORDEN_DIAS.includes(inicio) ? inicio : 9;
  S = nuevoEstado(dia, dia === 9 && !inicio);
  construir(); entrarEscena(); render();
}
function irADia(dia) {
  const conservar = S ? { tutos: S.tutos, sinTiempo: S.sinTiempo } : {};
  S = Object.assign(nuevoEstado(dia, false), conservar);
  entrarEscena(); render();
}
function siguienteDia() {
  const i = ORDEN_DIAS.indexOf(S.dia);
  const prox = ORDEN_DIAS[i + 1];
  S.dia = prox; S.idx = 0; S.deltas = {}; S.pos = casas(); S.aislado = {};
  const salto = { trip: -6, nave: -6, animo: -6, dosis: 3 };
  Object.entries(salto).forEach(([k, v]) => (S.bars[k] = Math.max(0, Math.min(100, S.bars[k] + v))));
  entrarEscena(); render();
  window.scrollTo(0, 0);
}
function siguienteEscena() {
  limpiarTemporizador();
  S.idx += 1; S.decRes = null; S.sello = null; S.puntos = {};
  if (S.idx >= escenas(S.dia).length) return siguienteDia();
  entrarEscena(); render();
}
function entrarEscena() {
  const e = escena();
  S.fase = null; S.decRes = null; S.sello = null; S.actual = null;
  if (!e) return;
  if (e.tipo === "manana" && e.retraso) S.retraso = e.retraso;
  if (e.tipo === "turno") {
    S.actual = e.astro; S.fase = "apertura"; S.medidas = {};
    if (e.desde) S.pos[e.astro] = e.desde;
  }
  if (e.tipo === "mover_grupo") ASTROS.forEach((a) => (S.pos[a] = e.destino));
  if (e.tipo === "medicion_grupo") S.medidas = {};
  if (e.tipo === "plan") S.plan = [];
  if (e.tipo === "descenso") S.desc = {};
  if (e.tipo === "imprevisto" && !e.opciones) S.decRes = { deltas: aplicar(L(e.ef) || e.ef) };
}

/* ---------- barras ---------- */
function aplicar(ef) {
  if (typeof ef === "function") ef = ef(S, D());
  const out = [];
  for (const [k, v] of Object.entries(ef || {})) {
    if (!v) continue;
    S.bars[k] = Math.max(0, Math.min(100, S.bars[k] + v));
    S.deltas[k] = (S.deltas[k] || 0) + v;
    out.push([k, v]);
  }
  return out;
}
function chipsDeltas(lista) {
  return `<div class="deltas">${lista.map(([k, v]) => {
    const b = BARRAS.find((x) => x.id === k);
    return `<span class="delta" style="--col:${b.col}">${v > 0 ? "▲" : "▼"} ${esc(L(b.n))}</span>`;
  }).join("")}</div>`;
}

/* ---------- construcción de la pantalla ---------- */
function construir() {
  document.getElementById("app").innerHTML = `<div id="top"></div><div id="mapa-zona"></div><div id="escena"></div><div id="capa"></div>`;
  construirMapa();
}
function construirMapa() {
  const mods = MODULOS.map((m, i) => `<div class="modulo ${m.id === "medica" ? "medica" : ""}" data-i="${i}" data-id="${m.id}">
      <div class="mn">${esc(L(m.n))}</div><div class="ms">${esc(L(m.s))}</div><div class="estado"></div></div>`).join("");
  const monos = ASTROS.map((a) => `<div class="mono" id="mono-${a}" style="--col:${TRIPULACION[a].col}">
      <span class="et">${TRIPULACION[a].ini}</span>${svgMonigote(TRIPULACION[a].col)}</div>`).join("");
  $("#mapa-zona").innerHTML = `<div class="mapa"><div class="casco">${mods}${monos}</div><div class="pista" id="pista"></div><div class="avisos" id="avisos"></div></div>`;
  $("#mapa-zona").querySelectorAll(".modulo").forEach((m) => m.addEventListener("click", () => moverA(m.dataset.id)));
}
function svgMonigote(col) {
  return `<svg viewBox="0 0 34 40"><rect x="5" y="17" width="5" height="12" rx="2" fill="#9fb3cc"/>
    <circle cx="17" cy="10" r="8" fill="#dfe9f5" stroke="${col}" stroke-width="2"/><ellipse cx="18.5" cy="9.5" rx="4.6" ry="3.6" fill="#13263f"/>
    <rect x="9" y="17" width="16" height="14" rx="5" fill="#e8eef6" stroke="${col}" stroke-width="2"/><circle cx="17" cy="23" r="2" fill="${col}"/>
    <rect x="10.5" y="30" width="5" height="8" rx="2.5" fill="#e8eef6" stroke="${col}" stroke-width="1.5"/>
    <rect x="18.5" y="30" width="5" height="8" rx="2.5" fill="#e8eef6" stroke="${col}" stroke-width="1.5"/></svg>`;
}
function ocultaMapa() { const e = escena(); return !e || ["prologo", "diario", "bitacora", "final", "revelacion", "descenso"].includes(e.tipo) || S.fin; }
function actualizarMapa() {
  const zona = $("#mapa-zona");
  zona.style.display = ocultaMapa() ? "none" : "";
  if (ocultaMapa()) return;
  const e = escena(), d = D();
  const porModulo = {};
  ASTROS.forEach((a) => {
    const i = MODULOS.findIndex((m) => m.id === S.pos[a]);
    const slot = (porModulo[i] = (porModulo[i] || 0) + 1) - 1;
    const el = $("#mono-" + a);
    el.style.left = `calc(${i * 20}% + ${i === 0 ? 18 : 6}px + ${slot * 3.6}%)`;
    el.classList.toggle("actual", S.actual === a);
    el.classList.toggle("aislado", !!S.aislado[a]);
  });
  const alarma29 = e && e.tipo === "alarma" && e.noche;
  const tormenta = d.tormenta && (S.flags.refugio || (e && e.tipo === "alarma"));
  zona.querySelectorAll(".modulo").forEach((m) => {
    const id = m.dataset.id; const est = m.querySelector(".estado");
    m.classList.toggle("alerta", (id === "soporte" && (alarma29 || (S.dia === 21 && !S.flags.filtro_ok))) || (id === "refugio" && e && e.tipo === "alarma" && !e.noche));
    m.classList.toggle("refugio-on", id === "refugio" && !!tormenta);
    m.classList.toggle("destino", S.fase === "mover" && id === (e.en || "medica"));
    est.textContent = "";
    if (id === "soporte") {
      const co2 = S.dia === 29 && !S.flags.causa29 ? d.co2 : S.dia === 21 && S.flags.filtro_ok ? 2.0 : d.dia === 29 ? d.co2_real : d.co2;
      est.textContent = `CO₂ ${fmt(co2)} mmHg`; est.style.color = co2 > d.co2_limite ? COLORES.rojo : COLORES.verde;
    }
    if (id === "comunicaciones") { est.textContent = apagonHoy() ? t("sin_contacto") : `${S.retraso} min`; est.style.color = apagonHoy() ? COLORES.rojo : COLORES.verde; }
    if (id === "refugio" && tormenta) { est.textContent = `☢ ${fmt(d.rad)} mSv`; est.style.color = "#c4b5fd"; }
  });
  const pista = $("#pista");
  if (S.fase === "mover" && S.actual) {
    pista.innerHTML = `${esc(t("mover", { n: TRIPULACION[S.actual].nombre.split(" ")[0], m: L(MODULOS.find((m) => m.id === (e.en || "medica")).n).toLowerCase() }))} <kbd>←</kbd> <kbd>→</kbd>`;
  } else pista.innerHTML = "";
}
function moverA(id) {
  if (S.fase !== "mover" || !S.actual) return;
  S.pos[S.actual] = id; actualizarMapa();
  const destino = escena().en || "medica";
  if (id === destino) {
    S.fase = "llegando";
    setTimeout(() => { if (S.fase === "llegando") { S.fase = "medir"; render(); } }, 1150);
  }
}
document.addEventListener("keydown", (ev) => {
  if (!S) return;
  if (S.fase === "mover" && (ev.key === "ArrowLeft" || ev.key === "ArrowRight")) {
    const i = MODULOS.findIndex((m) => m.id === S.pos[S.actual]);
    const j = Math.max(0, Math.min(4, i + (ev.key === "ArrowLeft" ? -1 : 1)));
    moverA(MODULOS[j].id); ev.preventDefault();
  }
});

/* ---------- barra superior ---------- */
function renderTop() {
  if (S.fin === "revelacion") { $("#top").innerHTML = ""; return; }
  const d = D(), n = ORDEN_DIAS.indexOf(S.dia) + 1;
  const barras = BARRAS.map((b) => {
    const v = S.bars[b.id]; const pel = (b.bajo && v < b.bajo) || (b.alto && v > b.alto);
    const zonas = (b.bajo ? `<div class="zona" style="left:0;width:${b.bajo}%"></div>` : "") + (b.alto ? `<div class="zona" style="left:${b.alto}%;width:${100 - b.alto}%"></div>` : "");
    const pt = S.puntos[b.id] ? `<div class="punto" style="left:${v}%;width:${S.puntos[b.id]}px;height:${S.puntos[b.id]}px"></div>` : "";
    const dl = S.deltas[b.id] ? `<b style="color:${S.deltas[b.id] > 0 ? "#7ee2b8" : "#ff8a8d"}">${S.deltas[b.id] > 0 ? "▲" : "▼"}</b>` : "";
    return `<div class="barra-j ${pel ? "peligro" : ""}" style="--col:${b.col}" title="${esc(L(b.n))}"><div class="bn"><span>${esc(L(b.n))}</span>${dl}</div>
      <div class="bt">${zonas}<div class="bf" style="width:${v}%"></div>${pt}</div></div>`;
  }).join("");
  const enlace = apagonHoy() ? `<span class="led no"></span>${t("tierra")}: ${t("sin_contacto")}` : `<span class="led"></span>${t("tierra")}: ${t("retraso", { m: S.retraso })}`;
  const saltos = ORDEN_DIAS.map((x) => `<button data-dia="${x}" class="${x === S.dia ? "on" : ""}">${x}</button>`).join("");
  $("#top").innerHTML = `<div class="top"><div class="top-dia"><div class="d1">${t("dia")} ${n} ${t("de")} 5 · ${t("viaje")} ${S.dia}</div>
      <div class="d2">${t("nave")} · ${d.fecha} · ${esc(L(DIAS[S.dia].titulo))}</div></div>
    <div class="barras">${barras}</div>
    <div class="top-tierra">${enlace}<div class="menu"><button id="b-tiempo" class="${S.sinTiempo ? "on" : ""}">⏱ ${t("sin_tiempo")}</button>
      <span style="font-size:10px;align-self:center">${t("saltar")}</span>${saltos}<button id="b-reset">↺ ${t("reiniciar")}</button></div></div></div>`;
  $("#b-tiempo").onclick = () => { S.sinTiempo = !S.sinTiempo; if (S.sinTiempo) limpiarTemporizador(); render(); };
  $("#b-reset").onclick = () => { limpiarTemporizador(); S = nuevoEstado(9, true); construir(); entrarEscena(); render(); };
  $("#top").querySelectorAll("[data-dia]").forEach((b) => (b.onclick = () => { limpiarTemporizador(); irADia(+b.dataset.dia); }));
}

/* ---------- render principal ---------- */
function render() {
  if (!S) return;
  limpiarTemporizador();
  renderTop(); actualizarMapa();
  $("#capa").innerHTML = "";
  const e = escena(); const zona = $("#escena");
  if (S.fin === "final") zona.innerHTML = vistaFinal();
  else if (S.fin === "revelacion") zona.innerHTML = vistaRevelacion();
  else if (!e) zona.innerHTML = "";
  else zona.innerHTML = ({
    prologo: vistaPrologo, bitacora: vistaBitacora, diario: vistaDiario, manana: vistaManana, turno: vistaTurno,
    alarma: vistaAlarmaBase, mover_grupo: vistaMoverGrupo, decision: () => vistaDecisionEscena(e), pizarra: vistaPizarra,
    medicion_grupo: vistaMedicionGrupo, plan: vistaPlan, imprevisto: vistaImprevistoBase, noche: vistaNoche, descenso: vistaDescenso,
  }[e.tipo] || (() => ""))();
  enlazar();
  if (e && e.tipo === "alarma") mostrarAlarma(e);
  if (e && e.tipo === "imprevisto") mostrarImprevisto(e);
  tutoriales();
  setTimeout(ajustarAltura, 60);
}

/* ---------- vistas: historia ---------- */
function vistaPrologo() {
  const txt = LANG === "es"
    ? "1 de mayo de 2024. Nave Cóndor. Destino: Marte.\nA partir de aquí, un mensaje a casa tarda minutos. A veces no llega.\nNo hay médico a bordo: cada uno se mide a sí mismo."
    : "May 1, 2024. Condor spacecraft. Destination: Mars.\nFrom here on, a message home takes minutes. Sometimes it never arrives.\nThere is no doctor on board: everyone measures themselves.";
  const vita = LANG === "es"
    ? "Hola. Soy VITA, el monitor de salud de la nave. La primera semana aprendí cómo es cada uno de ustedes cuando está bien. Desde ahora les aviso cuando algo cambie y les digo por qué. No doy órdenes: ustedes deciden."
    : "Hi. I'm VITA, the ship's health monitor. In the first week I learned what each of you looks like when you're well. From now on I'll warn you when something changes and tell you why. I don't give orders: you decide.";
  return `<div class="prologo"><div class="tl escribir" id="maquina" data-txt="${esc(txt)}"></div>
    <svg class="pulso-svg" width="320" height="60" viewBox="0 0 320 60"><path d="M0 30 H110 L125 30 L135 8 L150 52 L162 22 L172 30 H320" fill="none" stroke="#3ee0ff" stroke-width="2.5"/></svg>
    <div class="vita entrar" style="max-width:560px;text-align:left;animation-delay:2.4s"><div class="ojo">V</div><div class="t">${esc(vita)}</div></div>
    <button class="btn entrar" style="animation-delay:2.8s" data-acc="seguir">${t("empezar_dia", { d: 9 })}</button></div>`;
}
function vistaBitacora() {
  return `<div class="escena"><div class="panel entrar" style="max-width:720px;margin:0 auto;width:100%"><div class="pcab"><span>${t("bitacora")}</span><span class="acc">${t("viaje")} ${S.dia}</span></div>
    <div style="font-family:var(--m);line-height:1.7;font-size:14px">${esc(L(DIAS[S.dia].bitacora))}</div>
    <div class="fila-btn"><button class="btn" data-acc="seguir">${t("continuar")}</button></div></div></div>`;
}
function vistaDiario() {
  const e = escena(), a = TRIPULACION[e.autor];
  return `<div class="escena"><div style="max-width:640px;margin:10px auto;width:100%"><div class="diario"><div class="df">${t("diario_de", { n: a.nombre.split(" ")[0] })} · ${t("viaje")} ${S.dia - 1}</div>
    ${esc(L(e.texto))}</div><div class="fila-btn" style="justify-content:flex-end"><button class="btn" data-acc="seguir">${t("empezar_dia", { d: S.dia })}</button></div></div></div>`;
}
function vistaManana() {
  const e = escena();
  const tierra = apagonHoy() || !e.tierra
    ? `<div class="vita"><div class="ojo" style="color:var(--critico);border-color:var(--critico)">📵</div><div class="t">${t("sin_contacto")} · ${t("cola")}</div></div>`
    : `<div class="dice" style="margin-top:0"><span class="gesto">${t("mensaje_tierra")} · Dra. Rosa Ibáñez · ${t("retraso", { m: e.retraso })}</span>${esc(L(e.tierra))}</div>`;
  const obj = (e.objetivos || []).map(([a, txt]) => `<div class="obj"><span class="who" style="--col:${TRIPULACION[a].col}"><i>${TRIPULACION[a].ini}</i>${esc(L(txt))}</span><span style="color:var(--apagado);font-size:11px">${TRIPULACION[a].nombre.split(" ")[0]}</span></div>`).join("");
  return `<div class="escena"><div class="panel entrar"><div class="pcab"><span>${t("informe_vita")}</span><span class="acc">07:00</span></div>
      <div class="vita"><div class="ojo">V</div><div class="t">${esc(L(e.vita))}</div></div>
      <div class="dos" style="margin-top:14px"><div>${tierra}</div><div>${obj ? `<div class="pcab"><span>${t("objetivos")}</span></div><div class="objetivos">${obj}</div>` : ""}</div></div>
      <div class="fila-btn"><button class="btn" data-acc="seguir">${t("continuar")}</button></div></div></div>`;
}

/* ---------- vistas: turno de un tripulante ---------- */
function vistaTurno() {
  const e = escena(), a = e.astro, T = TRIPULACION[a];
  const cab = `<div class="quien"><div class="retrato" style="--col:${T.col}">${T.ini}</div><div><div class="n">${T.nombre}</div><div class="r">${esc(L(T.rol))} · ${a}</div></div></div>`;
  if (S.fase === "apertura") {
    return `<div class="escena"><div class="panel entrar"><div class="pcab"><span>${esc(L(MODULOS.find((m) => m.id === S.pos[a]).n))}</span><span class="acc">${t("dia")} ${S.dia}</span></div>${cab}
      <div class="dice">${e.gesto ? `<span class="gesto">${esc(L(e.gesto))}</span>` : ""}«${esc(L(e.apertura))}»</div>
      <div class="fila-btn"><button class="btn" data-acc="ir">${t("ir_medirse")}</button></div></div></div>`;
  }
  if (S.fase === "mover" || S.fase === "llegando") {
    return `<div class="escena"><div class="panel entrar">${cab}<div class="dice">${esc(t("mover", { n: T.nombre.split(" ")[0], m: L(MODULOS.find((m) => m.id === (e.en || "medica")).n).toLowerCase() }))} ← →</div></div></div>`;
  }
  if (S.fase === "medir") return vistaMedir(a);
  if (S.fase === "subir") {
    return `<div class="escena"><div class="panel entrar">${cab}<div class="pcab" style="margin-top:14px"><span>${t("subiendo")}</span><span class="acc">VITA</span></div>
      <div class="subida"><i id="barra-subida"></i></div></div></div>`;
  }
  if (S.fase === "ficha") return vistaFicha(a);
  if (S.fase === "decision") return `<div class="escena">${vistaCarta(e.decision)}</div>`;
  return "";
}

/* La estación médica: el monigote se mide con cada aparato */
const APARATOS = ["pa", "ox", "te", "gl", "re", "an"];
const ICONOS = { pa: "🩺", ox: "🫀", te: "🌡️", gl: "🩸", re: "⌚", an: "🙂" };
const GUIA_DE = { pa: "pas_mmhg", ox: "fc_lpm", te: "temp_c", gl: "glucosa_mgdl", re: "sueno_h", an: "animo_1a5" };
function lecturaAparato(a, k) {
  const v = trip(a).valores, e = trip(a).estados;
  if (k === "pa") return [`${fmt(v.pas_mmhg, 0)}/${fmt(v.pad_mmhg, 0)} mmHg`, peor(e.pas_mmhg, e.pad_mmhg)];
  if (k === "ox") return [`${fmt(v.fc_lpm, 0)} lpm · SpO₂ ${fmt(v.spo2_pct)} %`, peor(e.fc_lpm, e.spo2_pct)];
  if (k === "te") return [`${fmt(v.temp_c)} °C`, e.temp_c];
  if (k === "gl") return [`${fmt(v.glucosa_mgdl, 0)} mg/dL`, e.glucosa_mgdl];
  if (k === "re") return [`${fmt(v.sueno_h)} h`, e.sueno_h];
  if (k === "an") { const n = S.medidas.an; return n ? [CARITAS[n - 1], n <= 2 ? "amarillo" : "verde"] : ["", "verde"]; }
}
function vistaMedir(a) {
  const T = TRIPULACION[a];
  const tiles = APARATOS.map((k) => {
    const hecho = k === "an" ? !!S.medidas.an : !!S.medidas[k];
    const [val, est] = hecho ? lecturaAparato(a, k) : ["", "verde"];
    const guia = DATA.guia[GUIA_DE[k]] || "";
    if (k === "an") {
      return `<div class="aparato ${hecho ? "hecho" : ""}" style="--est:${COLORES[est]}"><div class="ai">${ICONOS[k]}</div><div class="an">${t("ap").an}</div>
        <div class="caritas">${CARITAS.map((c, i) => `<button data-animo="${i + 1}" class="${S.medidas.an === i + 1 ? "sel" : ""}" aria-label="${i + 1}">${c}</button>`).join("")}</div>
        <div class="ah">${esc(guia)}</div></div>`;
    }
    return `<button class="aparato ${hecho ? "hecho" : ""}" data-ap="${k}" style="--est:${COLORES[est]}"><div class="ai">${ICONOS[k]}</div><div class="an">${t("ap")[k]}</div>
      ${hecho ? `<div class="av">${val}</div>` : `<div class="ah" style="color:var(--cian)">${k === "pa" ? t("mantener") : t("tocar")}</div>`}
      <div class="ah">${esc(guia.length > 120 ? guia.slice(0, 118) + "…" : guia)}</div><div class="prog"></div></button>`;
  }).join("");
  const listos = APARATOS.every((k) => (k === "an" ? !!S.medidas.an : !!S.medidas[k]));
  return `<div class="escena"><div class="panel entrar"><div class="pcab"><span>${esc(t("medir_t", { n: T.nombre.split(" ")[0] }))}</span><span class="acc">${a}</span></div>
    <div class="estacion"><div class="figura">${svgFigura(T.col, S.medidas)}<div class="lector" id="lector">${esc(t("medir_s"))}</div></div>
    <div><div class="aparatos">${tiles}</div>
    <div class="fila-btn">${S.yaMidio && !listos ? `<button class="btn2" data-acc="medir_todo">${t("medir_todo")}</button>` : ""}
      <button class="btn" data-acc="subir" ${listos ? "" : "disabled"}>📡 ${t("subir")}</button></div></div></div></div></div>`;
}
function svgFigura(col, m) {
  const curva = m.an ? [-9, -4, 0, 5, 9][m.an - 1] : 2;
  const on = (k) => (m[k] || m.activo === k ? "on" : "");
  return `<svg viewBox="0 0 200 290" aria-hidden="true">
    <defs><linearGradient id="traje" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2d4566"/><stop offset="1" stop-color="#1b2c45"/></linearGradient></defs>
    <ellipse cx="100" cy="282" rx="70" ry="6" fill="#3ee0ff" opacity=".18"/>
    <line x1="74" y1="98" x2="42" y2="168" stroke="url(#traje)" stroke-width="17" stroke-linecap="round"/>
    <line x1="126" y1="98" x2="158" y2="168" stroke="url(#traje)" stroke-width="17" stroke-linecap="round"/>
    <circle cx="40" cy="172" r="9" fill="#9fb3cc"/><circle cx="160" cy="172" r="9" fill="#9fb3cc"/>
    <line x1="88" y1="180" x2="82" y2="268" stroke="url(#traje)" stroke-width="20" stroke-linecap="round"/>
    <line x1="112" y1="180" x2="118" y2="268" stroke="url(#traje)" stroke-width="20" stroke-linecap="round"/>
    <rect x="68" y="84" width="64" height="104" rx="22" fill="url(#traje)" stroke="${col}" stroke-width="2"/>
    <circle cx="86" cy="106" r="7" fill="${col}"/><rect x="104" y="100" width="18" height="4" rx="2" fill="#9fb3cc" opacity=".6"/>
    <rect x="93" y="70" width="14" height="16" rx="5" fill="#9fb3cc"/>
    <circle cx="100" cy="50" r="27" fill="#a9bdd6" stroke="${col}" stroke-width="2"/>
    <circle cx="90" cy="46" r="3" fill="#13263f"/><circle cx="110" cy="46" r="3" fill="#13263f"/>
    <path d="M89 ${62 - curva / 3} Q100 ${62 + curva} 111 ${62 - curva / 3}" stroke="#13263f" stroke-width="2.6" fill="none" stroke-linecap="round"/>
    <g class="disp ${on("pa")}"><rect class="manguito ${m.activo === "pa" ? "inflando" : ""}" x="47" y="112" width="24" height="26" rx="6" fill="#3a6ea5" stroke="#9fd9ff" stroke-width="1.5" transform="rotate(24 59 125)"/>
      <path d="M52 132 C40 150 30 150 24 140" stroke="#9fd9ff" stroke-width="1.5" fill="none"/><circle cx="20" cy="134" r="10" fill="#0b1828" stroke="#9fd9ff" stroke-width="1.5"/>
      <line x1="20" y1="134" x2="26" y2="128" stroke="#ffb547" stroke-width="2"/></g>
    <g class="disp ${on("ox")}"><rect x="152" y="174" width="18" height="12" rx="4" fill="#e9eef5" stroke="#3ee0ff"/><circle class="led-ox ${on("ox")}" cx="161" cy="180" r="2.6" fill="#ff5a5f"/></g>
    <g class="disp ${on("te")}"><line x1="108" y1="61" x2="140" y2="70" stroke="#e9eef5" stroke-width="5" stroke-linecap="round"/>
      <line x1="112" y1="62" x2="${m.te || m.activo === "te" ? 136 : 114}" y2="${m.te || m.activo === "te" ? 69 : 63}" stroke="#ff5a5f" stroke-width="2.4" stroke-linecap="round" class="mercurio"/></g>
    <g class="disp ${on("gl")}"><circle class="gota ${on("gl")}" cx="30" cy="166" r="4" fill="#ff3b3b"/><rect x="14" y="176" width="16" height="22" rx="4" fill="#e9eef5" stroke="#3ee0ff"/>
      <rect x="17" y="180" width="10" height="6" rx="1" fill="#0b1828"/></g>
    <g class="disp ${on("re")}"><rect class="reloj ${on("re")}" x="40" y="153" width="13" height="11" rx="3" fill="#0b1828" stroke="#3ee0ff" stroke-width="1.5" transform="rotate(24 46 158)"/></g>
  </svg>`;
}
function medir(k, el) {
  const a = S.actual; if (!a || S.medidas[k]) return;
  const dur = k === "pa" ? 1400 : 1100;
  const prog = el.querySelector(".prog"); const t0 = performance.now();
  S.medidas.activo = k; refrescarFigura(); el.classList.add("midiendo");
  const lector = $("#lector");
  if (lector) lector.textContent = k === "pa" ? t("mantener") + "…" : "…";
  clearInterval(medicionTimer);
  medicionTimer = setInterval(() => {
    const p = Math.min(1, (performance.now() - t0) / dur);
    prog.style.width = p * 100 + "%";
    if (p >= 1) {
      clearInterval(medicionTimer); medicionTimer = null;
      S.medidas[k] = true; S.medidas.activo = null;
      const [val] = lecturaAparato(a, k);
      render(); const l2 = $("#lector"); if (l2) l2.textContent = `${t("ap")[k]}: ${val}`;
    }
  }, 30);
}
function cancelarMedicion(k, el) {
  if (!medicionTimer || S.medidas.activo !== k) return;
  clearInterval(medicionTimer); medicionTimer = null; S.medidas.activo = null;
  el.classList.remove("midiendo"); el.querySelector(".prog").style.width = "0";
  refrescarFigura(); const l = $("#lector"); if (l) l.textContent = t("soltaste");
}
function refrescarFigura() { const f = $(".figura"); if (f) f.querySelector("svg").outerHTML = svgFigura(TRIPULACION[S.actual].col, S.medidas); }

/* La ficha de VITA (estilo documento) con el sello */
function filaFicha(var_, valor, est, normal, i) {
  const marca = { verde: "✓", amarillo: "!", rojo: "✕", sensor: "?" }[est] || "✓";
  const delay = `animation-delay:${0.25 + i * 0.12}s`;
  return `<tr><td>${esc(var_)}</td><td class="v"><span class="${est !== "verde" ? "circulo" : ""}" style="${delay}">${valor}</span></td>
    <td class="n">${normal != null ? `${t("tu_normal")} ${fmt(normal)}` : ""}</td>
    <td class="m"><span class="marca" style="background:${TINTA[est]};${delay}">${marca}</span></td></tr>`;
}
function vistaFicha(a) {
  const T = TRIPULACION[a], tr = trip(a), v = tr.valores, e = tr.estados, nm = tr.normales;
  const animo = S.medidas.an || v.animo_1a5;
  const filas = [
    [LANG === "es" ? "Presión arterial (mmHg)" : "Blood pressure (mmHg)", `${fmt(v.pas_mmhg, 0)}/${fmt(v.pad_mmhg, 0)}`, peor(e.pas_mmhg, e.pad_mmhg), null],
    [nv("fc_lpm"), fmt(v.fc_lpm, 0), e.fc_lpm, nm.fc_lpm], [nv("spo2_pct"), fmt(v.spo2_pct), e.spo2_pct, nm.spo2_pct],
    [nv("temp_c"), fmt(v.temp_c), e.temp_c, nm.temp_c], [nv("glucosa_mgdl"), fmt(v.glucosa_mgdl, 0), e.glucosa_mgdl, null],
    [nv("sueno_h"), fmt(v.sueno_h), e.sueno_h, nm.sueno_h], [nv("animo_1a5"), CARITAS[Math.round(animo) - 1], animo <= 2 ? "amarillo" : "verde", null],
  ];
  const auto = [[nv("resp_rpm"), fmt(v.resp_rpm), e.resp_rpm, nm.resp_rpm], [nv("cefalea_0a10"), fmt(v.cefalea_0a10), e.cefalea_0a10, nm.cefalea_0a10],
    [nv("reaccion_ms"), fmt(v.reaccion_ms, 0), e.reaccion_ms, nm.reaccion_ms], [nv("orina_l"), fmt(v.orina_l), e.orina_l, null],
    [nv("ejercicio_min"), fmt(v.ejercicio_min, 0), e.ejercicio_min, null]];
  let i = 0;
  const tabla = filas.map((f) => filaFicha(f[0], f[1], f[2], f[3], i++)).join("")
    + `<tr class="sep"><td colspan="4">${t("sensores")}</td></tr>` + auto.map((f) => filaFicha(f[0], f[1], f[2], f[3], i++)).join("");
  const ocultas = escena().ocultar || [];
  const notas = D().alertas.filter((al) => al.afectados.includes(a) && !ocultas.includes(al.codigo)).map(notaAlerta).join("")
    || `<div class="nota" style="--col:${TINTA.verde}"><div class="nt">✓ ${t("todo_normal")}</div></div>`;
  const sellado = S.sello ? `<div class="sellado" style="--col:${S.sello === "apto" ? TINTA.verde : TINTA.rojo}">${S.sello === "apto" ? t("apto") : t("no_apto")}</div>` : "";
  let veredicto = "";
  if (S.sello) {
    const ok = (S.sello === "apto") === tr.apto;
    const roja = D().alertas.some((al) => al.afectados.includes(a) && al.nivel === "rojo" && al.origen !== "sensor");
    const vars = { p: tr.prep, c: tr.prep >= 70 ? "≥" : "<", a: roja ? t("con_roja") : t("sin_roja"), s: tr.apto ? t("apto") : t("no_apto") };
    veredicto = `<div class="vita entrar" style="margin-top:12px"><div class="ojo">V</div><div class="t">${ok ? "✅ " : "⚠️ "}${esc(t(ok ? "regla_ok" : "regla_mal", vars))}</div></div>
      <div class="fila-btn"><button class="btn" data-acc="tras_ficha">${t("continuar")}</button></div>`;
  }
  return `<div class="escena"><div class="escritorio"><div class="papel">
    <div class="enc"><div><div class="t1">${t("ficha")}</div><div class="t2">${t("nave")} · ${t("viaje")} ${S.dia} · ${D().fecha}</div>
      <div style="font-family:var(--t);font-weight:700;font-size:18px;margin-top:6px">${T.nombre}</div><div class="t2">${esc(L(T.rol))} · ${a} · ${t("hoy")}</div></div>
      <div class="foto" style="background:${T.col}">${T.ini}</div></div>
    <div class="ficha-cuerpo"><div><table class="tabla"><colgroup><col class="c1"><col class="c2"><col class="c3"><col class="c4"></colgroup>${tabla}</table></div>
      <div class="cuerpo-mini">${svgCuerpo(ocultas.length ? tr.niveles_propios : tr.niveles)}<div class="parte-info" id="parte-info">${t("toca_parte")}</div></div></div>
    <div class="notas">${notas}</div>
    <div class="sellos-zona"><span class="q">${t("apto_q")}</span><span class="fila-btn" style="margin:0">
      <button class="sello-btn" style="--col:${TINTA.verde}" data-sello="apto" ${S.sello ? "disabled" : ""}>${t("apto")}</button>
      <button class="sello-btn" style="--col:${TINTA.rojo}" data-sello="no" ${S.sello ? "disabled" : ""}>${t("no_apto")}</button></span></div>
    ${sellado}</div>${veredicto}</div></div>`;
}
function notaAlerta(al) {
  const enCola = apagonHoy() && al.triaje === "tierra";
  const col = al.origen === "sensor" ? TINTA.sensor : TINTA[al.nivel];
  const accion = enCola ? al.accion_apagon : al.accion;
  const triaje = enCola ? TX[LANG].triaje.cola : TX[LANG].triaje[al.triaje];
  return `<div class="nota" style="--col:${col}"><div class="nt">${al.origen === "sensor" ? "🔧" : al.nivel === "rojo" ? "🔴" : "🟡"} ${esc(al.titulo)}</div>
    <div class="chips"><span class="chip" style="color:${COL_ORIGEN[al.origen]}">${TX[LANG].origen[al.origen]}</span><span class="chip" style="color:${col}">${triaje}</span></div>
    <div>➡️ ${esc(accion)}</div>
    <details><summary>🔎 ${t("por_que")}</summary><div><b>${t("regla")}:</b> ${esc(al.regla)}</div>
      ${al.evidencia.length ? `<div><b>${t("datos")}:</b> ${al.evidencia.map(esc).join(" · ")}</div>` : ""}
      <div><b>${t("fuente")}:</b> ${al.fuentes.map((f) => `<a href="${esc(f.u)}" target="_blank" rel="noopener">${esc(f.n)}</a>`).join(" · ")}</div></details></div>`;
}
function svgCuerpo(niv) {
  const c = (p) => COLORES[niv[p]] || COLORES.verde;
  const st = (p, o) => `fill="${c(p)}" fill-opacity="${o}" stroke="${c(p)}" stroke-width="1.6" data-parte="${p}"`;
  return `<svg viewBox="0 0 240 340"><circle cx="120" cy="52" r="38" fill="none" stroke="#7f8ea3" stroke-width="2.5"/>
    <circle cx="120" cy="52" r="30" ${st("cabeza", 0.5)}/>
    <rect x="58" y="100" width="22" height="110" rx="11" ${st("huesos", 0.25)}/><rect x="160" y="100" width="22" height="110" rx="11" ${st("huesos", 0.25)}/>
    <rect x="82" y="94" width="76" height="130" rx="22" ${st("cuerpo", 0.18)}/>
    <ellipse cx="103" cy="132" rx="13" ry="20" ${st("pulmones", 0.5)}/><ellipse cx="137" cy="132" rx="13" ry="20" ${st("pulmones", 0.5)}/>
    <path d="M120 150 c-10 -14 -26 -2 -14 10 l14 12 l14 -12 c12 -12 -4 -24 -14 -10z" ${st("corazon", 0.75)}/>
    <ellipse cx="106" cy="192" rx="8" ry="11" ${st("rinones", 0.6)}/><ellipse cx="134" cy="192" rx="8" ry="11" ${st("rinones", 0.6)}/>
    <rect x="88" y="228" width="28" height="96" rx="12" ${st("huesos", 0.25)}/><rect x="124" y="228" width="28" height="96" rx="12" ${st("huesos", 0.25)}/></svg>`;
}

/* ---------- tarjeta de decisión (estilo Reigns) ---------- */
function vistaDecisionEscena(e) { return `<div class="escena">${vistaCarta(e)}</div>`; }
function vistaCarta(dec) {
  const quien = dec.quien === "grupo"
    ? `<div class="quien">${ASTROS.map((a) => `<div class="retrato" style="--col:${TRIPULACION[a].col};width:38px;height:38px;font-size:16px;border-radius:11px">${TRIPULACION[a].ini}</div>`).join("")}</div>`
    : `<div class="quien"><div class="retrato g" style="--col:${TRIPULACION[dec.quien].col}">${TRIPULACION[dec.quien].ini}</div><div><div class="n">${TRIPULACION[dec.quien].nombre}</div><div class="r">${esc(L(TRIPULACION[dec.quien].rol))}</div></div></div>`;
  if (S.decRes) {
    return `<div class="mesa-carta"><div class="carta">${quien}<div class="pregunta">${esc(L(dec.pregunta))}</div>
      <div class="resultado entrar"><b>${esc(S.decRes.elegida)}</b><br>${esc(S.decRes.txt)}${chipsDeltas(S.decRes.deltas)}</div>
      <div class="fila-btn"><button class="btn" data-acc="tras_decision">${t("continuar")}</button></div></div></div>`;
  }
  const conTiempo = dec.tiempo && !S.sinTiempo && !dec.sinPrisa;
  const reloj = conTiempo ? `<div class="reloj-t"><svg width="52" height="52"><circle cx="26" cy="26" r="22" fill="none" stroke="rgba(120,160,200,.2)" stroke-width="4"/>
      <circle id="aro" cx="26" cy="26" r="22" fill="none" stroke="#ff5a5f" stroke-width="4" stroke-dasharray="138.2" stroke-dashoffset="0" stroke-linecap="round"/></svg>
      <div class="num" id="num">${dec.tiempo}</div></div>` : "";
  const dos = dec.opciones.length === 2;
  return `<div class="mesa-carta"><div class="carta" id="carta" data-dos="${dos ? 1 : 0}">${reloj}
    ${dos ? `<div class="lado i" id="lado-i">← ${esc(L(dec.opciones[0].txt))}</div><div class="lado d" id="lado-d">${esc(L(dec.opciones[1].txt))} →</div>` : ""}
    ${quien}<div class="pregunta">${esc(L(dec.pregunta))}</div>
    <div class="opciones">${dec.opciones.map((o, i) => `<button class="btn2" data-op="${i}">${esc(L(o.txt))}</button>`).join("")}</div>
    <div class="piensa" id="piensa"><span style="opacity:.6">${t("piensas")}…</span></div>
    ${conTiempo ? `<div class="deslizar-ayuda">${esc(t("tiempo", { o: L(dec.opciones[dec.defecto || 0].txt) }))}</div>` : dos ? `<div class="deslizar-ayuda">${t("desliza")}</div>` : ""}
  </div></div>`;
}
function decisionActual() {
  const e = escena();
  if (e.tipo === "turno") return e.decision;
  if (e.tipo === "alarma") return e.decision;
  return e;
}
function mostrarPiensa(dec, i) {
  const o = dec.opciones[i]; const el = $("#piensa"); if (!el) return;
  const ef = typeof o.ef === "function" ? o.ef(S, D()) : o.ef || {};
  const fichas = Object.entries(ef).filter(([, v]) => v).map(([k, v]) => {
    const b = BARRAS.find((x) => x.id === k); return `<span class="ficha-b" style="--col:${b.col}">${esc(L(b.n))} ${v > 0 ? "↑" : "↓"}</span>`;
  }).join("");
  el.innerHTML = `${t("piensas")}: «${esc(L(o.piensa) || L(o.txt))}»<div class="fichas">${fichas}</div>`;
  S.puntos = {}; Object.entries(ef).forEach(([k, v]) => { if (v) S.puntos[k] = Math.abs(v) >= G ? 14 : Math.abs(v) >= M ? 10 : 7; });
  renderTop();
}
function elegir(dec, i, porTiempo) {
  limpiarTemporizador();
  const o = dec.opciones[i];
  const deltas = aplicar(o.ef);
  if (o.flag) Object.assign(S.flags, o.flag);
  if (S.dia === 21 && dec.quien === "A3") S.flags.filtro_ok = true;
  S.puntos = {};
  S.decRes = { elegida: (porTiempo ? "⏱ " : "") + L(o.txt), txt: L(o.res) || "", deltas };
  if (escena().tipo === "alarma") { render(); return; }
  render();
}
function iniciarTemporizador(seg, alAcabar) {
  limpiarTemporizador();
  const t0 = performance.now();
  temporizador = setInterval(() => {
    const rest = Math.max(0, seg - (performance.now() - t0) / 1000);
    const aro = $("#aro"), num = $("#num");
    if (aro) aro.setAttribute("stroke-dashoffset", String(138.2 * (1 - rest / seg)));
    if (num) num.textContent = Math.ceil(rest);
    if (rest <= 0) { limpiarTemporizador(); alAcabar(); }
  }, 100);
}
function limpiarTemporizador() { if (temporizador) { clearInterval(temporizador); temporizador = null; } }
function activarCarta(dec) {
  const carta = $("#carta"); if (!carta) return;
  carta.querySelectorAll("[data-op]").forEach((b) => {
    const i = +b.dataset.op;
    b.addEventListener("mouseenter", () => mostrarPiensa(dec, i));
    b.addEventListener("focus", () => mostrarPiensa(dec, i));
    b.addEventListener("click", () => elegir(dec, i));
  });
  if (dec.tiempo && !S.sinTiempo && !dec.sinPrisa) iniciarTemporizador(dec.tiempo, () => elegir(dec, dec.defecto || 0, true));
  if (carta.dataset.dos === "1") {
    let x0 = null, dx = 0;
    carta.addEventListener("pointerdown", (ev) => { if (ev.target.closest("button")) return; x0 = ev.clientX; carta.setPointerCapture(ev.pointerId); carta.style.transition = "none"; });
    carta.addEventListener("pointermove", (ev) => {
      if (x0 === null) return; dx = ev.clientX - x0;
      carta.style.transform = `translateX(${dx}px) rotate(${dx / 18}deg)`;
      $("#lado-i").style.opacity = dx < -30 ? 1 : 0; $("#lado-d").style.opacity = dx > 30 ? 1 : 0;
      if (Math.abs(dx) > 30) mostrarPiensa(dec, dx < 0 ? 0 : 1);
    });
    const soltar = () => {
      if (x0 === null) return; x0 = null; carta.style.transition = "";
      if (Math.abs(dx) > 90) elegir(dec, dx < 0 ? 0 : 1);
      else { carta.style.transform = ""; $("#lado-i").style.opacity = 0; $("#lado-d").style.opacity = 0; }
      dx = 0;
    };
    carta.addEventListener("pointerup", soltar); carta.addEventListener("pointercancel", soltar);
  }
}

/* ---------- alarmas e imprevistos (ventanas) ---------- */
function vistaAlarmaBase() { return `<div class="escena"><div class="panel" style="min-height:420px"></div></div>`; }
function mostrarAlarma(e) {
  const dec = e.decision;
  let cuerpo;
  if (!dec) cuerpo = `<div class="fila-btn"><button class="btn" data-acc="seguir">${t("continuar")}</button></div>`;
  else if (S.decRes) cuerpo = `<div class="resultado entrar"><b>${esc(S.decRes.elegida)}</b><br>${esc(S.decRes.txt)}${chipsDeltas(S.decRes.deltas)}</div>
      <div class="fila-btn"><button class="btn" data-acc="seguir">${t("continuar")}</button></div>`;
  else cuerpo = vistaCarta(dec).replace('class="mesa-carta"', 'class="mesa-carta" style="padding:0"');
  $("#capa").innerHTML = `<div class="velo"><div class="modal roja"><div class="mt">⚠ ${esc(L(e.titulo))}</div>
    <div class="vita" style="margin:10px 0"><div class="ojo" style="color:var(--critico);border-color:var(--critico)">V</div><div class="t">${esc(L(e.texto))}</div></div>${cuerpo}</div></div>`;
  enlazar($("#capa"));
  if (dec && !S.decRes) activarCarta(dec);
}
function vistaImprevistoBase() { return `<div class="escena"><div class="panel" style="min-height:360px"></div></div>`; }
function mostrarImprevisto(e) {
  let cuerpo;
  if (e.opciones && !S.decRes) cuerpo = `<div class="opciones">${e.opciones.map((o, i) => `<button class="btn2" data-imp="${i}">${esc(L(o.txt))}</button>`).join("")}</div>`;
  else cuerpo = `${S.decRes && S.decRes.txt ? `<div class="resultado">${esc(S.decRes.txt)}</div>` : ""}${chipsDeltas((S.decRes && S.decRes.deltas) || [])}
    <div class="fila-btn"><button class="btn" data-acc="seguir">${t("continuar")}</button></div>`;
  $("#capa").innerHTML = `<div class="velo"><div class="modal"><div class="mt">${t("imprevisto")}</div><h3>${esc(L(e.titulo))}</h3>
    <div style="line-height:1.55">${esc(L(e.texto))}</div>${cuerpo}</div></div>`;
  enlazar($("#capa"));
  $("#capa").querySelectorAll("[data-imp]").forEach((b) => (b.onclick = () => {
    const o = e.opciones[+b.dataset.imp]; S.decRes = { txt: L(o.res), deltas: aplicar(o.ef) }; render();
  }));
}

/* ---------- grupo: moverse y medirse ---------- */
function vistaMoverGrupo() {
  const e = escena();
  return `<div class="escena"><div class="panel entrar"><div class="vita"><div class="ojo">V</div><div class="t">${ASTROS.map((a) => TRIPULACION[a].nombre.split(" ")[0]).join(", ")} → ${esc(L(MODULOS.find((m) => m.id === e.destino).n))}</div></div>
    <div class="fila-btn"><button class="btn" data-acc="seguir">${t("continuar")}</button></div></div></div>`;
}
function vistaMedicionGrupo() {
  const e = escena();
  const tarjetas = ASTROS.map((a) => {
    const T = TRIPULACION[a], tr = trip(a), hecho = S.medidas[a];
    const senales = hecho ? [["resp_rpm", 1], ["spo2_pct", 1], ["fc_lpm", 0], ["cefalea_0a10", 1]].map(([v, d]) =>
      `<div class="senal" style="--col:${COLORES[tr.estados[v]]}"><span><i></i>${esc(nv(v))}</span><b>${fmt(tr.valores[v], d)}</b></div>`).join("")
      : `<button class="btn2" data-grupo="${a}" style="width:100%;text-align:center;margin-top:6px">🫀 ${t("tocar")}</button>`;
    return `<div class="perfil"><div class="pn"><span class="retrato" style="--col:${T.col}">${T.ini}</span>${T.nombre.split(" ")[0]}</div>${senales}</div>`;
  }).join("");
  const todos = ASTROS.every((a) => S.medidas[a]);
  return `<div class="escena"><div class="panel entrar"><div class="pcab"><span>${t("mediciones_grupo")}</span><span class="acc">03:14</span></div>
    <div class="dice" style="margin:0 0 12px">${esc(L(e.texto))}</div><div class="pizarra">${tarjetas}</div>
    <div class="fila-btn"><button class="btn" data-acc="seguir" ${todos ? "" : "disabled"}>${t("continuar")}</button></div></div></div>`;
}

/* ---------- pizarra de VITA ---------- */
function causaCorrecta() {
  const al = D().alertas.find((a) => ["nave", "persona", "sensor"].includes(a.origen) && a.codigo !== "tormenta") || D().alertas[0];
  return [CAUSA_DE_ORIGEN[al.origen], al];
}
function vistaPizarra() {
  const e = escena(), d = D();
  const perfiles = ASTROS.map((a) => {
    const T = TRIPULACION[a], tr = trip(a);
    return `<div class="perfil"><div class="pn"><span class="retrato" style="--col:${T.col}">${T.ini}</span>${T.nombre.split(" ")[0]}</div>${e.vars.map((v) => {
      const c = tr.cambio[v]; const cam = c != null && v !== "cefalea_0a10" && v !== "temp_c" ? ` <small style="color:var(--apagado)">${c > 0 ? "+" : ""}${c}%</small>` : "";
      return `<div class="senal" style="--col:${COLORES[tr.estados[v]]}"><span><i></i>${esc(nv(v).split("(")[0])}</span><b>${fmt(tr.valores[v])}${cam}</b></div>`;
    }).join("")}</div>`;
  }).join("");
  const pct = Math.min(100, (d.co2 / 6) * 100), lim = (d.co2_limite / 6) * 100;
  const aire = `<div class="aire"><b style="font-family:var(--t)">${t("aire")}</b><div class="bt"><div class="bf" style="width:${pct}%;background:${d.co2 > d.co2_limite ? COLORES.rojo : COLORES.verde}"></div><div class="lim" style="left:${lim}%"></div></div>
    <span style="font-family:var(--m);font-size:12px">${fmt(d.co2)} mmHg · ${t("limite")} ${d.co2_limite}</span></div>`;
  let cierre;
  if (S.decRes) {
    const [ok, al] = causaCorrecta();
    cierre = `<div class="resultado entrar"><b>${S.decRes.elegida}</b> ${S.decRes.acierto ? "✅" : "❌"}<br>${esc(S.decRes.txt)}${chipsDeltas(S.decRes.deltas)}
      <div style="margin-top:8px;font-size:13px;color:var(--apagado)"><b>${t("regla")}:</b> ${esc(al.regla)} · ${al.fuentes.map((f) => `<a style="color:var(--cian)" href="${esc(f.u)}" target="_blank" rel="noopener">${esc(f.n)}</a>`).join(" · ")}</div></div>
      <div class="fila-btn"><button class="btn" data-acc="seguir">${t("continuar")}</button></div>`;
  } else {
    const conTiempo = e.tiempo && !S.sinTiempo;
    cierre = `<div class="causas">${["tripulante", "nave", "sensor"].map((c) => `<button class="btn2" data-causa="${c}">${TX[LANG].causa[c]}</button>`).join("")}</div>
      ${conTiempo ? `<div class="deslizar-ayuda" style="display:flex;align-items:center;gap:8px;justify-content:center"><span class="reloj-t" style="position:relative;right:auto;top:auto;width:40px;height:40px">
        <svg width="40" height="40" viewBox="0 0 52 52"><circle cx="26" cy="26" r="22" fill="none" stroke="rgba(120,160,200,.2)" stroke-width="4"/><circle id="aro" cx="26" cy="26" r="22" fill="none" stroke="#ff5a5f" stroke-width="4" stroke-dasharray="138.2" stroke-dashoffset="0"/></svg><span class="num" id="num" style="font-size:12px">${e.tiempo}</span></span>${esc(L(e.defecto_txt))}</div>` : ""}`;
  }
  return `<div class="escena"><div class="panel entrar"><div class="pcab"><span>${t("pizarra")}</span><span class="acc">${t("dia")} ${S.dia}</span></div>
    <div class="pizarra">${perfiles}</div>${aire}
    <div class="vita" style="margin-top:12px"><div class="ojo">V</div><div class="t">${esc(L(e.vita))}</div></div>${cierre}</div></div>`;
}
function elegirCausa(c, porTiempo) {
  limpiarTemporizador();
  const e = escena(); const [ok] = causaCorrecta(); const r = e.res[c];
  const deltas = aplicar(r.ef); if (r.flag) Object.assign(S.flags, r.flag);
  S.flags["causa" + S.dia] = c; S.causas.total += 1; if (c === ok) S.causas.ok += 1;
  S.decRes = { elegida: (porTiempo ? "⏱ " + L(e.defecto_txt) + " " : "") + TX[LANG].causa[c], txt: L(r.t), deltas, acierto: c === ok };
  render();
}

/* ---------- plan a bordo ---------- */
function vistaPlan() {
  const e = escena();
  const al = D().alertas.find((a) => a.afectados.includes(e.quien) && a.triaje === "tierra");
  const prot = al ? `<div class="vita"><div class="ojo">V</div><div class="t">${esc(al.accion_apagon)}</div></div>` : "";
  if (S.decRes) {
    return `<div class="escena"><div class="panel entrar"><div class="pcab"><span>${esc(L(e.titulo))}</span></div>
      <div class="objetivos">${S.plan.map((i, n) => `<div class="obj"><span>${n + 1}. ${esc(L(e.cartas[i].txt))}</span></div>`).join("")}</div>
      ${chipsDeltas(S.decRes.deltas)}<div class="fila-btn"><button class="btn" data-acc="seguir">${t("continuar")}</button></div></div></div>`;
  }
  return `<div class="escena"><div class="panel entrar"><div class="pcab"><span>${esc(L(e.titulo))}</span><span class="acc">${esc(t("plan", { n: e.max }))}</span></div>${prot}
    <div class="dos" style="margin-top:12px"><div class="opciones">${e.cartas.map((c, i) => `<button class="btn2 ${S.plan.includes(i) ? "sel" : ""}" data-carta="${i}">${esc(L(c.txt))}</button>`).join("")}</div>
    <div class="objetivos">${[0, 1, 2].slice(0, e.max).map((n) => `<div class="obj" style="min-height:38px"><span>${n + 1}. ${S.plan[n] != null ? esc(L(e.cartas[S.plan[n]].txt)) : "<span style='color:var(--apagado)'>…</span>"}</span></div>`).join("")}
      <div class="fila-btn"><button class="btn" data-acc="aplicar_plan" ${S.plan.length ? "" : "disabled"}>${t("dar_plan")}</button></div></div></div></div></div>`;
}

/* ---------- noche ---------- */
function vistaNoche() {
  const e = escena();
  const enCola = apagonHoy();
  const nCola = D().alertas.filter((a) => a.triaje === "tierra").length + 1;
  const canal = `<div class="canal"><div class="a">🛰️</div><div class="b">🌍</div><div class="r"></div><div class="p ${enCola ? "cola" : "viaja"}"></div></div>
    <div style="font-size:12px;color:var(--apagado);margin-top:4px;font-family:var(--m)">${enCola ? t("informe_cola", { n: nCola }) : t("informe", { m: S.retraso })}</div>`;
  const diarios = ASTROS.map((a) => `<div class="diario" style="--col:${TRIPULACION[a].col};animation-delay:${0.15 * ASTROS.indexOf(a)}s"><div class="df"><i></i>${t("diario_de", { n: TRIPULACION[a].nombre.split(" ")[0] })}</div>${esc(L(e.diarios[a]))}</div>`).join("");
  const deltas = Object.entries(S.deltas).filter(([, v]) => v).map(([k, v]) => { const b = BARRAS.find((x) => x.id === k); return `<span class="delta" style="--col:${b.col}">${v > 0 ? "▲" : "▼"} ${esc(L(b.n))}</span>`; }).join("");
  const ult = S.dia === 29;
  return `<div class="escena"><div class="panel entrar"><div class="pcab"><span>${t("noche", { d: S.dia })}</span><span class="acc">22:30</span></div>
    <div class="vita"><div class="ojo">V</div><div class="t">${esc(L(e.vita))}</div></div>${canal}<div class="deltas" style="margin-top:10px">${deltas}</div></div>
    <div class="panel entrar"><div class="pcab"><span>${t("diarios")}</span></div><div class="diarios">${diarios}</div>
    <div class="fila-btn" style="justify-content:flex-end"><button class="btn" data-acc="seguir">${ult ? t("al_final") : t("siguiente_dia", { d: ORDEN_DIAS[ORDEN_DIAS.indexOf(S.dia) + 1] })}</button></div></div></div>`;
}

/* ---------- lista de descenso y final ---------- */
function vistaDescenso() {
  const todos = ASTROS.every((a) => S.desc[a]);
  const cards = ASTROS.map((a) => {
    const T = TRIPULACION[a], tr = trip(a);
    const als = D().alertas.filter((al) => al.afectados.includes(a));
    const chips = !todos ? "" : als.map((al) => `<div style="color:${al.origen === "sensor" ? TINTA.sensor : TINTA[al.nivel]};font-weight:700;margin-top:4px">${al.origen === "sensor" ? "🔧" : "⚠"} ${esc(al.titulo)}</div>`).join("");
    const s = S.desc[a];
    let ver = "";
    if (todos) {
      const ok = (s === "apto") === tr.apto;
      const sensor = als.find((al) => al.origen === "sensor");
      ver = `<div style="margin-top:8px;font-family:var(--c);font-size:12px;color:${ok ? TINTA.verde : TINTA.rojo}">${ok ? "✓" : "✕"} ${tr.apto ? t("apto") : t("no_apto")} · ${tr.prep}/100${sensor ? ` · ${esc(sensor.regla)}` : ""}</div>`;
    }
    return `<div class="cred"><div class="foto" style="background:${T.col};width:44px;height:52px;font-size:20px">${T.ini}</div><div class="cn">${T.nombre}</div>
      <div style="opacity:.75">${esc(L(T.rol))}</div><div style="margin-top:6px">${t("preparacion")}: <b>${tr.prep}</b>/100</div>
      <div>SpO₂ <b style="color:${TINTA[tr.estados.spo2_pct]}">${fmt(tr.valores.spo2_pct)}%</b> · ${fmt(tr.valores.fc_lpm, 0)} lpm · ${fmt(tr.valores.resp_rpm)} rpm</div>${chips}
      ${s ? `<div class="sellado" style="--col:${s === "apto" ? TINTA.verde : TINTA.rojo}">${s === "apto" ? t("apto") : t("no_apto")}</div>` : ""}
      ${!s ? `<div class="fila-btn"><button class="sello-btn" style="--col:${TINTA.verde}" data-desc="${a}|apto">${t("apto")}</button><button class="sello-btn" style="--col:${TINTA.rojo}" data-desc="${a}|no">${t("no_apto")}</button></div>` : ""}${ver}</div>`;
  }).join("");
  return `<div class="escena"><div class="panel entrar"><div class="pcab"><span>${t("descenso")}</span><span class="acc">${D().fecha}</span></div>
    <div style="margin-bottom:10px;color:var(--apagado)">${t("descenso_s")} (${t("preparacion")} ≥ 70 ${t("sin_roja")})</div>
    <div class="credenciales">${cards}</div>
    <div class="fila-btn" style="justify-content:flex-end"><button class="btn" data-acc="ver_final" ${todos ? "" : "disabled"}>${t("ver_final")}</button></div></div></div>`;
}
function calcularFinal() {
  const b = S.bars, marcados = ASTROS.filter((a) => S.desc[a] === "apto").length;
  if (marcados === 4 && b.dosis <= 60 && b.nave >= 30 && b.nave <= 85 && b.mision >= 40) return "botas";
  if (S.flags.causa26 === "tripulante" && S.flags.causa29 === "sensor" && marcados >= 3) return "solos";
  if (marcados === 3) return "arriba";
  if (b.nave < 35) return "resistio";
  return "ajustada";
}
function vistaFinal() {
  const f = FINALES[S.final];
  return `<div class="escena"><div class="panel entrar" style="text-align:center;padding:40px 20px;background:radial-gradient(ellipse at 50% 100%, rgba(255,120,60,.18), rgba(11,24,40,.9) 70%)">
    <div style="font-size:54px">🪐</div><div class="final-t">${esc(L(f.t))}</div>
    <div style="max-width:620px;margin:0 auto;line-height:1.65;font-size:16px">${esc(L(f.x))}</div>
    <div class="fila-btn" style="justify-content:center;margin-top:22px"><button class="btn" data-acc="revelar">${t("revelar")}</button></div></div></div>`;
}
function vistaRevelacion() {
  const r = DATA.reales;
  const titulo = LANG === "es" ? "FIN DEL ESCENARIO CÓNDOR-31" : "END OF SCENARIO CONDOR-31";
  const sub = LANG === "es"
    ? "Simulación de entrenamiento para tripulaciones. Las tormentas solares de este escenario ocurrieron de verdad: NASA las registró en mayo de 2024."
    : "Crew training simulation. The solar storms in this scenario really happened: NASA recorded them in May 2024.";
  return `<div class="escena"><div class="rev entrar"><h2>${titulo}</h2><div>${sub}</div>
    <div class="pcab" style="margin-top:16px;color:#999"><span>${t("tus_resultados")}</span></div>
    <div class="stats"><div class="stat"><small>${t("causas_ok")}</small><span class="grande">${S.causas.ok}/${S.causas.total}</span></div>
      <div class="stat"><small>${t("sellos_ok")}</small><span class="grande">${S.sellos.ok}/${S.sellos.total}</span></div></div>
    <div class="pcab" style="color:#999"><span>${t("app_real")}</span></div>
    <div class="stats"><div class="stat"><small>${t("eventos")}</small><span class="grande">${r.eventos}</span></div>
      <div class="stat"><small>${t("dias_ev")}</small><span class="grande">${r.dias}</span></div>
      ${r.recall ? `<div class="stat"><small>${t("robustez")}</small><span class="grande">${r.recall}% · ${r.precision}%</span></div>` : ""}
      <div class="stat"><small>${t("rad_evitada")}</small><span class="grande">${r.rad_evitada} mSv (−${r.rad_pct}%)</span></div></div>
    <div style="font-size:18px;color:#fff;margin:10px 0"><i>${t("lema")}</i></div><div>${t("quinto")}</div>
    <div class="fila-btn"><button class="btn" data-acc="otra">${t("jugar_otra")}</button></div></div></div>`;
}

/* ---------- eventos ---------- */
function enlazar(raiz = document) {
  raiz.querySelectorAll("[data-acc]").forEach((b) => (b.onclick = () => accion(b.dataset.acc)));
  const e = escena();
  if (raiz === document && e && e.tipo === "turno" && S.fase === "medir") {
    document.querySelectorAll("[data-ap]").forEach((el) => {
      const k = el.dataset.ap;
      if (k === "pa") {
        el.addEventListener("pointerdown", (ev) => { ev.preventDefault(); medir(k, el); });
        el.addEventListener("pointerup", () => cancelarMedicion(k, el));
        el.addEventListener("pointerleave", () => cancelarMedicion(k, el));
        el.addEventListener("keydown", (ev) => { if (ev.key === " " || ev.key === "Enter") { ev.preventDefault(); if (!medicionTimer) medir(k, el); } });
        el.addEventListener("keyup", (ev) => { if (ev.key === " " || ev.key === "Enter") cancelarMedicion(k, el); });
      } else el.addEventListener("click", () => medir(k, el));
    });
    document.querySelectorAll("[data-animo]").forEach((b) => (b.onclick = () => { S.medidas.an = +b.dataset.animo; render(); }));
  }
  if (raiz === document && e && e.tipo === "turno" && S.fase === "ficha") {
    document.querySelectorAll("[data-sello]").forEach((b) => (b.onclick = () => {
      S.sello = b.dataset.sello; S.sellos.total += 1; if ((S.sello === "apto") === trip(S.actual).apto) S.sellos.ok += 1; render();
    }));
    document.querySelectorAll("[data-parte]").forEach((p) => (p.onclick = () => {
      const parte = p.dataset.parte, n = (escena().ocultar ? trip(S.actual).niveles_propios : trip(S.actual).niveles)[parte];
      $("#parte-info").innerHTML = `<b>${esc(DATA.partes[parte])}</b> · <span style="color:${TINTA[n]}">${esc(DATA.estado[n])}</span><br>${esc(DATA.que_hace[parte])}`;
    }));
  }
  if (raiz === document && e && ((e.tipo === "turno" && S.fase === "decision") || e.tipo === "decision") && !S.decRes) activarCarta(decisionActual());
  if (raiz === document && e && e.tipo === "pizarra" && !S.decRes) {
    document.querySelectorAll("[data-causa]").forEach((b) => (b.onclick = () => elegirCausa(b.dataset.causa)));
    if (e.tiempo && !S.sinTiempo) iniciarTemporizador(e.tiempo, () => elegirCausa(e.defecto, true));
  }
  if (raiz === document && e && e.tipo === "medicion_grupo") document.querySelectorAll("[data-grupo]").forEach((b) => (b.onclick = () => { S.medidas[b.dataset.grupo] = true; render(); }));
  if (raiz === document && e && e.tipo === "plan") document.querySelectorAll("[data-carta]").forEach((b) => (b.onclick = () => {
    const i = +b.dataset.carta; const k = S.plan.indexOf(i);
    if (k >= 0) S.plan.splice(k, 1); else if (S.plan.length < e.max) S.plan.push(i);
    render();
  }));
  if (raiz === document && e && e.tipo === "descenso") document.querySelectorAll("[data-desc]").forEach((b) => (b.onclick = () => {
    const [a, s] = b.dataset.desc.split("|"); S.desc[a] = s;
    if (ASTROS.every((x) => S.desc[x])) ASTROS.forEach((x) => { S.sellos.total += 1; if ((S.desc[x] === "apto") === trip(x).apto) S.sellos.ok += 1; });
    render();
  }));
  if (raiz === document && e && e.tipo === "prologo") escribirMaquina();
  if (raiz === document && e && e.tipo === "turno" && S.fase === "subir") {
    setTimeout(() => { const b = $("#barra-subida"); if (b) b.style.width = "100%"; }, 30);
    setTimeout(() => { if (S.fase === "subir") { S.fase = "ficha"; render(); } }, 1750);
  }
}
function accion(a) {
  const e = escena();
  if (a === "seguir") return siguienteEscena();
  if (a === "ir") {
    const destino = e.en || "medica";
    S.fase = S.pos[e.astro] === destino ? "medir" : "mover"; return render();
  }
  if (a === "medir_todo") { APARATOS.forEach((k) => { if (k !== "an") S.medidas[k] = true; }); S.medidas.an = S.medidas.an || Math.round(trip(S.actual).valores.animo_1a5); return render(); }
  if (a === "subir") { S.fase = "subir"; S.yaMidio = true; return render(); }
  if (a === "tras_ficha") { S.sello = null; if (e.decision) { S.fase = "decision"; return render(); } return terminarTurno(); }
  if (a === "tras_decision") { if (e.tipo === "turno") return terminarTurno(); return siguienteEscena(); }
  if (a === "aplicar_plan") {
    const ef = {}; S.plan.forEach((i) => Object.entries(e.cartas[i].ef).forEach(([k, v]) => (ef[k] = (ef[k] || 0) + v)));
    S.decRes = { deltas: aplicar(ef) };
    if (S.plan.includes(0) || S.flags.mei === "aislada") { S.pos.A3 = "camarotes"; S.aislado.A3 = true; }
    return render();
  }
  if (a === "ver_final") { S.final = calcularFinal(); S.fin = "final"; return render(); }
  if (a === "revelar") {
    const app = document.getElementById("app"); app.classList.add("gris");
    setTimeout(() => { app.classList.remove("gris"); S.fin = "revelacion"; render(); enviar("streamlit:setComponentValue", { value: { final: S.final, causas: S.causas, sellos: S.sellos, barras: S.bars }, dataType: "json" }); }, 1600);
    return;
  }
  if (a === "otra") { S = nuevoEstado(9, true); construir(); entrarEscena(); render(); return; }
}
function terminarTurno() {
  const e = escena();
  if (!(S.dia === 9 && S.flags.refugio)) S.pos[e.astro] = S.dia === 26 && e.astro === "A3" ? "camarotes" : TRIPULACION[e.astro].casa;
  siguienteEscena();
}

/* ---------- tutoriales ---------- */
function tutoriales() {
  const e = escena(); if (!e || S.fin || document.querySelector(".tuto")) return;
  let k = null;
  if (e.tipo === "manana" && !S.tutos.barras) k = "barras";
  else if (e.tipo === "turno" && S.fase === "mover") k = "mover";
  else if (e.tipo === "turno" && S.fase === "medir") k = "medir";
  else if (e.tipo === "turno" && S.fase === "ficha") k = S.tutos.ficha ? "sello" : "ficha";
  else if ((e.tipo === "turno" && S.fase === "decision") || e.tipo === "decision") k = "decision";
  else if (e.tipo === "pizarra") k = "pizarra";
  if (!k || S.tutos[k]) return;
  const [tt, txt] = TX[LANG].tutos[k];
  const box = document.createElement("div"); box.className = "tuto";
  box.innerHTML = `<div class="tt">TUTORIAL</div><h4>${esc(tt)}</h4><p>${esc(txt)}</p><button>${t("entendido")}</button>`;
  box.querySelector("button").onclick = () => { S.tutos[k] = true; box.remove(); tutoriales(); };
  document.getElementById("app").appendChild(box);
}

/* ---------- máquina de escribir del prólogo ---------- */
function escribirMaquina() {
  const el = $("#maquina"); if (!el) return;
  const txt = el.dataset.txt; let i = 0;
  const paso = () => { if (!document.body.contains(el)) return; el.textContent = txt.slice(0, i); i += 2; if (i <= txt.length + 1) setTimeout(paso, 18); };
  paso();
}

/* ---------- arranque ---------- */
new ResizeObserver(ajustarAltura).observe(document.getElementById("app"));
enviar("streamlit:componentReady", { apiVersion: 1 });
