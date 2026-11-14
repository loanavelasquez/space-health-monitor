/*
  CREW HEALTH MONITOR - Sensor en vivo (pulso y SpO2)
  NASA Space Apps Challenge 2026

  Placa:   ESP32 (por ejemplo "ESP32 Dev Module")
  Sensor:  MAX30102 (pulso + oxigenación)

  Conexiones (I2C):
    MAX30102 VIN  -> ESP32 3V3
    MAX30102 GND  -> ESP32 GND
    MAX30102 SDA  -> ESP32 GPIO 21
    MAX30102 SCL  -> ESP32 GPIO 22

  Librería (Arduino IDE -> Administrador de librerías):
    "SparkFun MAX3010x Pulse and Proximity Sensor Library"

  Qué hace:
    Lee el sensor y, más o menos una vez por segundo, envía por el puerto USB
    (Serial, 115200 baudios) una línea en formato JSON, por ejemplo:
      {"fc":72,"spo2":97,"valido":1,"dedo":1}
    El programa sensor_en_vivo.py (en la carpeta del proyecto) lee esas
    líneas y las pasa al dashboard.

  Basado en el ejemplo "Example8_SPO2" de la librería de SparkFun.
*/

#include <Wire.h>
#include "MAX30105.h"
#include "spo2_algorithm.h"

MAX30105 sensor;

const int32_t LARGO = 100;     // 100 muestras = ~4 s de señal (a 25 muestras/s)
uint32_t bufferIR[LARGO];
uint32_t bufferRojo[LARGO];

int32_t spo2;
int8_t spo2Valida;
int32_t pulso;
int8_t pulsoValido;

void leerMuestra(int i) {
  while (!sensor.available()) sensor.check();   // espera una muestra nueva
  bufferRojo[i] = sensor.getRed();
  bufferIR[i] = sensor.getIR();
  sensor.nextSample();
}

void setup() {
  Serial.begin(115200);
  Wire.begin();   // ESP32: SDA = 21, SCL = 22

  if (!sensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("{\"error\":\"MAX30102 no encontrado: revisar cables\"}");
    while (true) delay(1000);
  }

  // Configuración recomendada por el ejemplo de SparkFun para SpO2
  byte brillo = 60;        // 0 a 255
  byte promedio = 4;       // promedia 4 lecturas -> 25 muestras/s
  byte modo = 2;           // 2 = LED rojo + infrarrojo
  int frecuencia = 100;
  int anchoPulso = 411;
  int rango = 4096;
  sensor.setup(brillo, promedio, modo, frecuencia, anchoPulso, rango);

  // Primeras 100 muestras para arrancar
  for (int i = 0; i < LARGO; i++) leerMuestra(i);
  maxim_heart_rate_and_oxygen_saturation(bufferIR, LARGO, bufferRojo, &spo2, &spo2Valida, &pulso, &pulsoValido);
}

void loop() {
  // Desplaza la ventana: descarta las 25 muestras más viejas...
  for (int i = 25; i < LARGO; i++) {
    bufferRojo[i - 25] = bufferRojo[i];
    bufferIR[i - 25] = bufferIR[i];
  }
  // ...y lee 25 nuevas (~1 segundo)
  for (int i = LARGO - 25; i < LARGO; i++) leerMuestra(i);

  maxim_heart_rate_and_oxygen_saturation(bufferIR, LARGO, bufferRojo, &spo2, &spo2Valida, &pulso, &pulsoValido);

  bool hayDedo = bufferIR[LARGO - 1] > 50000;   // sin dedo, la luz infrarroja reflejada es baja
  bool valido = pulsoValido && spo2Valida;

  Serial.print("{\"fc\":");
  Serial.print((long)pulso);
  Serial.print(",\"spo2\":");
  Serial.print((long)spo2);
  Serial.print(",\"valido\":");
  Serial.print(valido ? 1 : 0);
  Serial.print(",\"dedo\":");
  Serial.print(hayDedo ? 1 : 0);
  Serial.println("}");
}
