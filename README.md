# Crew Health Monitor 🛰️

**NASA Space Apps Challenge 2026 – Create Health Monitoring Software for Astronauts on Space Missions**

Health monitoring software for a crew of four on a simulated Mars transit mission. In **Astronaut mode** each astronaut enters their own measurements (blood pressure, heart rate, blood sugar, temperature, sleep, mood) through a check-in, a clickable **health twin** body, a reaction-time mini-game (**Catch the meteor**) and a camera vision check, and gets an instant assessment. **Mission mode** shows the whole crew. It learns each astronaut's **personal baseline**, cross-checks variables across the whole crew to tell whether a problem comes from **the spacecraft** (e.g. high cabin CO₂ affecting everyone), from **the astronaut** (e.g. a possible infection in one person) or from **a faulty sensor**, explains **why** each alert fired with its NASA source, tells the crew **what to do**, decides whether each issue is **handled on board or sent to Earth**, and gives each astronaut a **readiness index** for critical tasks.

- **NASA data:** solar energetic particle (SEP) events from NASA's **DONKI** space weather database drive the radiation scenario (real storms of May 2024).
- **NASA reference values:** NASA-STD-3001 (600 mSv career limit, 3 mmHg CO₂), NASA Human Research Program risks (bone loss 1–1.5 %/month, kidney stones, sleep, CO₂), Curiosity RAD (1.8 mSv/day in transit).
- **Validated:** detects 98.7 % of event days with 93.1 % correct alerts across 30 randomized missions.
- **Simulated data:** physiological data are simulated from those reference values, following a mission script, because astronaut medical data are not public.

---

## Cómo correrlo en tu computadora

1. Abrir esta carpeta en **VS Code** (Archivo → Abrir carpeta).
2. Abrir una terminal (Terminal → Nueva terminal) e instalar las librerías, una sola vez:
   ```
   pip install -r requirements.txt
   ```
3. Correr la página:
   ```
   streamlit run app.py
   ```
   (si no se reconoce el comando: `python -m streamlit run app.py`)

Atajos en la dirección: `?dia=21` abre ese día · `?lang=en` abre en inglés · `?astro=A3` elige astronauta · `?estacion=checkin` abre esa estación (escaner, checkin, reaccion, tierra, vision, logros) · `?modo=mision` abre el Modo misión · `?modo=juego&dia=21` abre el juego en ese día (9, 21, 26, 29 o 31) · `?apagon=1` activa el apagón.

### Cambiar valores y regenerar los datos

Los parámetros están al principio de `generador.py`. Después de cambiarlos:
```
python generador.py
```

## Publicarlo gratis (link público para la entrega)

**Paso 1 – Subir la carpeta a GitHub**
1. Crear una cuenta en github.com (si no tienen).
2. Botón **New repository** → nombre `crew-health-monitor` → **Public** → **Create repository**.
3. En la página del repositorio: **uploading an existing file** → arrastrar **todo el contenido** de esta carpeta (`app.py`, `astronauta.py`, `tema.py`, `generador.py`, `requirements.txt`, `README.md`, y las carpetas `.streamlit`, `componentes`, `data`, `notebooks` y `hardware`) → **Commit changes**.
   ⚠️ La carpeta **`.streamlit`** tiene el tema oscuro de la nave: si no se sube, la página publicada se ve con colores claros.

**Paso 2 – Publicarlo en Streamlit Community Cloud**
1. Entrar a **share.streamlit.io** e iniciar sesión con la cuenta de GitHub.
2. **Create app** → elegir el repositorio `crew-health-monitor`, rama `main`, archivo principal `app.py`.
3. **Deploy**. En unos minutos queda un link público, por ejemplo `https://crew-health-monitor.streamlit.app`.
4. Para la entrega usar el link en inglés: agregar `?lang=en` al final.

Cada vez que se sube un cambio a GitHub, la página se actualiza sola.

## Funciones principales

| Función | Qué hace |
|---|---|
| Modo juego · Misión Cóndor | Juego narrativo (estilo *Papers, Please* y *Reigns*) con los días 9, 21, 26 y 29 y la llegada a Marte: mover al tripulante por la nave, medirse en la estación médica, subir los datos a VITA, sellar apto/no apto, decidir con tarjetas y la pizarra «¿un tripulante, la nave o el sensor?». Usa los mismos datos y alertas |
| Interfaz de la nave | Barra de misión (día, nave, enlace con la Tierra, dosis), estaciones (Escáner, Check-in, Reacción, Tierra, Visión, Logros), check-in en 4 tarjetas, alertas como tarjetas con botón «Entendido», sellos de apto/no apto y animaciones |
| Modo astronauta | Gemelo de salud (cuerpo clickeable), check-in con los 6 indicadores que pide NASA y guía "cómo medirlo", minijuego "Atrapa el meteorito", misiones del día con racha y Escudo de la tripulación, mensaje a la Tierra animado y visión con cámara |
| Tu normal | Aprende los valores normales de cada astronauta en los primeros 7 días |
| ¿Eres tú, es la nave o es el sensor? | Compara a la tripulación: si cambian todos, es la nave; si cambia uno, es esa persona; si el sensor marca algo grave sin síntomas, es el sensor |
| ¿Por qué? | Cada alerta muestra la regla, los datos que la dispararon y la fuente de NASA |
| Triaje y modo apagón | Cada alerta dice si se resuelve a bordo o con la Tierra; en apagón (conjunción solar) todo pasa a protocolos a bordo |
| Índice de preparación | 0–100 por astronauta; ≥ 70 sin alerta roja = apto para tareas críticas |
| Validación | Compara las alertas con el guion y repite la misión 30 veces (`data/robustez.csv`) |
| Sensor en vivo | MAX30102 + ESP32 envía pulso y SpO₂ reales (tarjeta "A5 en vivo") |

## Sensor en vivo (opcional, solo en la computadora)

1. Conectar el MAX30102 al ESP32: VIN→3V3, GND→GND, SDA→GPIO 21, SCL→GPIO 22.
2. En el Arduino IDE instalar la librería **SparkFun MAX3010x Pulse and Proximity Sensor Library** y la placa ESP32.
3. Subir `hardware/esp32_max30102/esp32_max30102.ino` al ESP32 y **cerrar el Monitor Serie**.
4. En una terminal: `python sensor_en_vivo.py --puerto COM3` (el puerto que muestre el Arduino IDE).
5. En otra terminal: `streamlit run app.py`. La tarjeta "A5 en vivo" aparece sola.

Para probar sin sensor: `python sensor_en_vivo.py --simular`.
La versión publicada en Streamlit Cloud no puede leer el USB de la computadora: el sensor en vivo se muestra corriendo la app localmente.

## Archivos

| Archivo | Qué es |
|---|---|
| `app.py` | La página (dashboard): panel, bitácora y "cómo funciona", en español e inglés |
| `generador.py` | Genera la misión simulada y contiene el motor de alertas |
| `astronauta.py` | El Modo astronauta (gemelo, check-in, juego, misiones, Tierra, visión) |
| `juego.py` | Prepara los datos del Modo juego (Misión Cóndor) desde la misión y el motor de alertas |
| `componentes/juego/` | El juego: `guion.js` (historia ES/EN), `motor.js` (pantallas y reglas del juego) y `estilo.css` |
| `tema.py` | Solo apariencia: colores, tipografías, animaciones, barra de misión y tarjetas |
| `.streamlit/config.toml` | Tema oscuro de la página (colores base) |
| `componentes/meteorito/` | El minijuego "Atrapa el meteorito" |
| `data/registros.csv` | Los check-in que ingresan los astronautas (se crea al usar la app) |
| `data/mision.csv` | Datos de la misión: 31 días × 4 astronautas |
| `data/alertas.csv` | Alertas detectadas |
| `notebooks/` | Cuadernos de Colab (radiación y generador de misión) |
| `sensor_en_vivo.py` | Puente entre el sensor (USB) y el dashboard |
| `hardware/` | Programa del ESP32 + MAX30102 |
| `data/robustez.csv` | Resultados de la prueba con 30 misiones |
| `requirements.txt` | Librerías necesarias |

## AI use disclosure

Parts of the code and documentation were developed with the help of an AI assistant (Claude, by Anthropic). The team reviewed, tested and adapted all outputs.
