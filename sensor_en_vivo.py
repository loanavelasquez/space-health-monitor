"""
PUENTE DEL SENSOR EN VIVO - Crew Health Monitor
Lee el pulso y la SpO2 que envía el ESP32 + MAX30102 por USB y los guarda en
data/en_vivo.csv. El dashboard muestra automáticamente la tarjeta "Sensor en vivo · A5"
mientras este programa esté corriendo.

Uso:
  Con el sensor conectado:   python sensor_en_vivo.py --puerto COM3
                             (en Mac/Linux: --puerto /dev/ttyUSB0)
  Sin sensor (para probar):  python sensor_en_vivo.py --simular

Necesita:  pip install pyserial
Para saber el puerto: en el Arduino IDE, menú Herramientas -> Puerto.
Importante: cerrar el Monitor Serie del Arduino IDE antes de correr esto
(solo un programa a la vez puede usar el puerto).
"""

import argparse
import json
import random
import time
from pathlib import Path

ARCHIVO = Path(__file__).parent / "data" / "en_vivo.csv"


def guardar(fc, spo2):
    nuevo = not ARCHIVO.exists()
    with ARCHIVO.open("a", encoding="utf-8") as f:
        if nuevo:
            f.write("hora,fc,spo2\n")
        f.write(f"{time.strftime('%H:%M:%S')},{fc},{spo2}\n")
    print(f"pulso {fc} lpm · SpO2 {spo2} %")


def lectura_valida(d):
    """Descarta lecturas sin dedo o con valores imposibles."""
    return (d.get("valido") == 1 and d.get("dedo") == 1
            and 30 <= d.get("fc", 0) <= 220 and 70 <= d.get("spo2", 0) <= 100)


def desde_sensor(puerto, baudios):
    import serial   # pip install pyserial
    with serial.Serial(puerto, baudios, timeout=5) as conexion:
        print(f"Conectado a {puerto}. Pon el dedo en el sensor (Ctrl+C para salir).")
        while True:
            linea = conexion.readline().decode("utf-8", errors="ignore").strip()
            if not linea.startswith("{"):
                continue
            try:
                d = json.loads(linea)
            except json.JSONDecodeError:
                continue
            if "error" in d:
                print("ESP32:", d["error"])
            elif lectura_valida(d):
                guardar(d["fc"], d["spo2"])
            else:
                print("…esperando una lectura estable (dedo quieto sobre el sensor)")


def simulado():
    """Datos de prueba: pulso ~72 y SpO2 ~97. Cada ~40 s simula que el sensor
    se suelta (SpO2 imposible con pulso normal) para probar la alerta de sensor."""
    print("Modo simulado (Ctrl+C para salir).")
    i = 0
    while True:
        fc = round(72 + random.gauss(0, 2))
        spo2 = round(97 + random.gauss(0, 0.6))
        if i % 40 in range(30, 35):
            spo2 = 86
        guardar(fc, min(spo2, 100))
        i += 1
        time.sleep(1)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Puente del sensor en vivo")
    p.add_argument("--puerto", help="puerto del ESP32, por ejemplo COM3 o /dev/ttyUSB0")
    p.add_argument("--baudios", type=int, default=115200)
    p.add_argument("--simular", action="store_true", help="usar datos de prueba, sin sensor")
    a = p.parse_args()

    ARCHIVO.parent.mkdir(exist_ok=True)
    if ARCHIVO.exists():
        ARCHIVO.unlink()   # empezar limpio: las primeras 20 lecturas serán "su normal"
    try:
        if a.simular:
            simulado()
        elif a.puerto:
            desde_sensor(a.puerto, a.baudios)
        else:
            p.error("indicar --puerto COM3 (o el que corresponda) o --simular")
    except KeyboardInterrupt:
        print("\nListo.")
