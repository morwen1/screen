# Sistema de Monitoreo de Temperatura con Termopares Tipo K

Sistema **autónomo y desatendido** de monitoreo de temperatura para Raspberry Pi Pico (RP2040, MicroPython) con:

- Lectura continua de **2 termopares tipo K** vía MAX6675 (SPI compartido).
- Visualización en tiempo real en una **pantalla OLED SSD1306** (128×32).
- **Control automático e independiente de 2 ventiladores** con histéresis.
- **Watchdog timer** para reinicio automático ante bloqueos.
- Arquitectura **modular** y configuración centralizada en `config.py`.

---

## 📋 Tabla de Contenidos

1. [Hardware Requerido](#-hardware-requerido)
2. [Especificaciones Técnicas](#-especificaciones-técnicas)
3. [Diagrama de Conexiones](#-diagrama-de-conexiones)
4. [Configuración de Pines](#-configuración-de-pines)
5. [Instalación](#-instalación)
6. [Estructura del Proyecto](#-estructura-del-proyecto)
7. [Arquitectura del Software](#-arquitectura-del-software)
8. [Lógica de Control de Ventiladores](#-lógica-de-control-de-ventiladores)
9. [Operación Desatendida](#-operación-desatendida)
10. [Uso](#-uso)
11. [Troubleshooting](#-troubleshooting)
12. [Notas Importantes](#-notas-importantes)

---

## 🔧 Hardware Requerido

### Componentes principales
- **1x Raspberry Pi Pico** (RP2040) con MicroPython
- **2x Módulos MAX6675** (amplificador de termopar tipo K con interfaz SPI)
- **2x Termopares tipo K** con rosca M6 (rango 0-800°C)
- **1x Pantalla OLED SSD1306** (128x32 píxeles, interfaz I2C)
- **2x Ventiladores DC** (controlados por GPIO, vía MOSFET / relé / driver)
- **Cables jumper** (macho-hembra y macho-macho)
- **Protoboard** (opcional, para organizar conexiones)

> ⚠️ **Importante:** los pines GPIO del Pico **no pueden alimentar un ventilador directamente**. Se debe usar un MOSFET tipo N (ej. IRLZ44N), un módulo relé o un driver dedicado que conmute la alimentación del ventilador (5V / 12V) a partir de la señal de 3.3V del GPIO.

### Especificaciones de los termopares
- **Tipo:** Termopar Tipo K (Cromel/Alumel)
- **Rango:** 0°C a 800°C
- **Precisión:** ±1.5% (Clase 2)
- **Rosca:** M6 (métrica de 6mm)
- **Cable:** 3 metros con blindaje de acero inoxidable
- **Conectores:** T+ (amarillo), T- (rojo)

---

## 📊 Especificaciones Técnicas

### MAX6675
- **Interfaz:** SPI (solo lectura)
- **Resolución:** 0.25°C
- **Rango de medición:** 0-1024°C
- **Tiempo de conversión:** 220ms típico
- **Voltaje de operación:** 3.0V - 5.5V
- **Detección de termopar abierto:** Sí (bit 2)

### SSD1306 OLED
- **Resolución:** 128x32 píxeles
- **Interfaz:** I2C
- **Dirección I2C:** 0x3C
- **Voltaje:** 3.3V

### Raspberry Pi Pico (RP2040)
- **ADC:** 12-bit, pines GP26-GP29 (no usado en este proyecto)
- **SPI:** 2 controladores (usamos SPI0)
- **I2C:** 2 controladores (usamos I2C0)
- **Voltaje de operación:** 3.3V

---

## 🔌 Diagrama de Conexiones

### Conexión completa del sistema

```
Raspberry Pi Pico                MAX6675 #1 (OIL)       MAX6675 #2 (REF)
┌──────────────────┐            ┌──────────────┐       ┌──────────────┐
│ Pin 36 (3.3V) ───┼────┬───────┤ VCC          │       │ VCC          │
│                  │    └───────┼──────────────┼───────┤              │
│ Pin 38 (GND) ────┼────┬───────┤ GND          │       │ GND          │
│                  │    └───────┼──────────────┼───────┤              │
│ Pin 4  (GP2/SCK) ┼────┬───────┤ SCK          │       │ SCK          │
│                  │    └───────┼──────────────┼───────┤              │
│ Pin 6  (GP4/MISO)┼────┬───────┤ SO           │       │ SO           │
│                  │    └───────┼──────────────┼───────┤              │
│ Pin 7  (GP5/CS1) ┼────────────┤ CS           │       │              │
│ Pin 9  (GP6/CS2) ┼────────────────────────────────── ┤ CS           │
│                  │            │ T+ (amarillo)│       │ T+ (amarillo)│
│                  │            │ T- (rojo)    │       │ T- (rojo)    │
│                  │            └──────────────┘       └──────────────┘
│                  │
│ Pin 1  (GP0/SDA) ┼────────┐         OLED SSD1306 (128x32)
│ Pin 2  (GP1/SCL) ┼──────┐ │         ┌──────────────┐
│                  │      │ └─────────┤ SDA          │
│                  │      └───────────┤ SCL          │
│                  │                  │ VCC <- 3.3V  │
│                  │                  │ GND <- GND   │
│                  │                  └──────────────┘
│                  │
│ Pin 15 (GP11) ───┼──────► [MOSFET / RELÉ #1] ──► Ventilador OIL (+V)
│ Pin 16 (GP12) ───┼──────► [MOSFET / RELÉ #2] ──► Ventilador REF (+V)
└──────────────────┘
```

### Esquema de conexión de ventiladores (recomendado, con MOSFET)

```
               +12V (o +5V)                           +12V (o +5V)
                  │                                      │
                  │                                      │
              ┌───┴───┐                              ┌───┴───┐
              │ FAN 1 │ (OIL)                        │ FAN 2 │ (REF)
              └───┬───┘                              └───┬───┘
                  │                                      │
                  │ Drain                                │ Drain
              ┌───┴───┐                              ┌───┴───┐
   GP11 ──[R]─┤ Gate  │  IRLZ44N                GP12─┤ Gate  │  IRLZ44N
              │       │                              │       │
              └───┬───┘                              └───┬───┘
                  │ Source                               │ Source
                  └──────────────┬───────────────────────┘
                                 │
                                GND (común con GND del Pico)
```

Un diodo flyback en paralelo con cada ventilador (cátodo a +V) es **muy recomendable** para proteger el MOSFET ante la fuerza contra-electromotriz del motor.

---

## 📍 Configuración de Pines

### Tabla de pines del Raspberry Pi Pico

| Pin Físico | GPIO | Función | Conecta a |
|:----------:|:----:|---------|-----------|
| **Pin 1** | GP0 | I2C0 SDA | SDA de la pantalla OLED |
| **Pin 2** | GP1 | I2C0 SCL | SCL de la pantalla OLED |
| **Pin 4** | GP2 | SPI0 SCK | SCK de ambos MAX6675 |
| **Pin 5** | GP3 | SPI0 MOSI | (no usado, requerido por la API) |
| **Pin 6** | GP4 | SPI0 MISO | SO de ambos MAX6675 |
| **Pin 7** | GP5 | CS OIL | CS del MAX6675 OIL |
| **Pin 9** | GP6 | CS REF | CS del MAX6675 REF |
| **Pin 15** | GP11 | Salida digital | Gate MOSFET / IN del relé del **Ventilador OIL** |
| **Pin 16** | GP12 | Salida digital | Gate MOSFET / IN del relé del **Ventilador REF** |
| **Pin 36** | 3V3(OUT) | Alimentación 3.3V | VCC de ambos MAX6675 y OLED |
| **Pin 38** | GND | Tierra | GND de todos los componentes (incluye GND del lado de los ventiladores) |

> Todos los pines se centralizan en `config.py` y pueden cambiarse sin tocar el código de los módulos.

### Orden de pines del módulo MAX6675

```
Vista frontal del módulo:
┌─────────────────────┐
│  [1] [2] [3] [4] [5]  │
│  GND VCC SCK CS  SO   │
└─────────────────────┘
```

---

## 💾 Instalación

### 1. Preparar el Raspberry Pi Pico

1. Descarga MicroPython para Raspberry Pi Pico desde [micropython.org](https://micropython.org/download/rp2-pico/)
2. Mantén presionado el botón BOOTSEL del Pico mientras lo conectas al PC
3. Copia el archivo `.uf2` al dispositivo que aparece como unidad USB
4. El Pico se reiniciará automáticamente con MicroPython

### 2. Instalar bibliotecas

Copia estos archivos al Pico usando Thonny, rshell o ampy:

```bash
# Biblioteca SSD1306 (si no está incluida en tu MicroPython)
# Descarga desde: https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py
```

### 3. Copiar archivos del proyecto

Copia toda la estructura de carpetas al sistema de archivos del Pico (con Thonny, `mpremote` o la extensión MicroPico de VS Code), respetando los directorios `lib/` y `modules/`:

```
/  (raíz del filesystem del Pico)
├── main.py
├── config.py
├── lib/
│   ├── __init__.py
│   ├── max6675.py
│   └── ssd1306.py
└── modules/
    ├── __init__.py
    ├── temperature.py
    ├── fan_control.py
    └── display.py
```

Con **mpremote** (recomendado):

```bash
mpremote cp config.py main.py :
mpremote cp -r lib :
mpremote cp -r modules :
mpremote reset
```

Al reiniciarse, MicroPython ejecutará `main.py` automáticamente.

---

## 📁 Estructura del Proyecto

```
screen/
├── README.md                    # Este archivo
├── main.py                      # Punto de entrada (loop principal)
├── config.py                    # Configuración centralizada (pines, umbrales)
├── lib/                         # Drivers de hardware
│   ├── max6675.py               # Driver MAX6675 (termopar tipo K, SPI)
│   └── ssd1306.py               # Driver SSD1306 (OLED, I2C)
├── modules/                     # Módulos funcionales del sistema
│   ├── temperature.py           # TemperatureSensor (wrapper MAX6675)
│   ├── fan_control.py           # FanController (control con histéresis)
│   └── display.py               # DisplayManager (render OLED)
├── tests/                       # Scripts de diagnóstico
│   ├── test_max6675.py          # Test de los 2 sensores
│   ├── test_single_max6675.py   # Test individual
│   ├── test_pins.py             # Test de pines GPIO
│   └── test_spi_loopback.py     # Test SPI
├── screen.py                    # (Legacy) script original — reemplazado por main.py
└── temp_sensors.py              # (Legacy) driver NTC no usado
```

> Ver detalles de la arquitectura, lógica de control y operación desatendida en las secciones siguientes.

---

## 🧠 Arquitectura del Software

El sistema está organizado en **capas** para separar responsabilidades y facilitar mantenimiento:

```
            ┌──────────────┐
            │   main.py    │  ← Loop infinito + watchdog + manejo de errores
            └──────┬───────┘
                   │ usa
   ┌───────────────┼─────────────────┬──────────────────┐
   ▼               ▼                 ▼                  ▼
config.py   TemperatureSensor   FanController     DisplayManager
            (modules/             (modules/         (modules/
             temperature.py)       fan_control.py)   display.py)
                  │                  │                   │
                  ▼                  ▼                   ▼
            lib/max6675.py      machine.Pin         lib/ssd1306.py
```

### Responsabilidad de cada archivo

| Archivo                       | Responsabilidad |
|-------------------------------|------------------|
| `main.py`                     | Punto de entrada. Inicializa hardware, configura watchdog y ejecuta el loop infinito. |
| `config.py`                   | **Única fuente de verdad** para pines, umbrales y tiempos. |
| `lib/max6675.py`              | Driver de bajo nivel del MAX6675 (lectura SPI cruda + decodificación). |
| `lib/ssd1306.py`              | Driver de bajo nivel del display OLED (I2C). |
| `modules/temperature.py`      | Clase `TemperatureSensor`: encapsula `MAX6675`, agrega manejo de errores y conteo de fallos consecutivos. |
| `modules/fan_control.py`      | Clases `Fan` y `FanController`: control independiente con histéresis y modo failsafe. |
| `modules/display.py`          | Clase `DisplayManager`: render del estado del sistema, texto escalado y mensajes de estado. |

### Flujo de ejecución de `main.py`

1. Importar `config` y los módulos.
2. `init_hardware()`:
   - Inicializa el `DisplayManager` y muestra `BOOT…`.
   - Crea el bus SPI compartido y los dos `TemperatureSensor` (OIL, REF).
   - Espera `SENSOR_WARMUP_MS` para estabilización del MAX6675.
   - Crea el `FanController` (ambos ventiladores arrancan apagados).
3. Si `WATCHDOG_ENABLED`, activa el `WDT` con timeout `WATCHDOG_TIMEOUT_MS`.
4. **Loop infinito** (`main_loop`), cada `UPDATE_INTERVAL_MS` ms:
   1. `sensor_oil.read()` y `sensor_ref.read()`.
   2. `fans.update(temp_oil, temp_ref)` aplica la lógica con histéresis.
   3. `display.render(...)` redibuja la pantalla.
   4. `print(...)` envía un log por UART (debug vía REPL).
   5. `wdt.feed()` resetea el watchdog.
   6. Cualquier excepción en el loop se captura, se muestra en el OLED y se sigue ejecutando.

---

## 🌬️ Lógica de Control de Ventiladores

- **Independiente por sensor**: el ventilador **OIL (GP11)** responde al sensor OIL; el ventilador **REF (GP12)** responde al sensor REF.
- **Histéresis** para evitar oscilaciones rápidas alrededor del umbral:

  | Temperatura del sensor          | Acción sobre su ventilador |
  |---------------------------------|----------------------------|
  | `T ≥ FAN_THRESHOLD_TEMP`        | **ON**                     |
  | `T < FAN_THRESHOLD_TEMP - FAN_HYSTERESIS` | **OFF**          |
  | Zona intermedia                 | Mantiene el estado anterior |
  | `T is None` (sensor caído)      | **ON** (failsafe)          |

  Con los valores por defecto (`55 °C` y `2 °C`):
  - Enciende cuando `T ≥ 55 °C`.
  - Apaga cuando `T < 53 °C`.
  - Entre 53 y 55 °C mantiene el estado, evitando “chattering”.

- **Failsafe**: si un sensor devuelve `None` (termopar desconectado o error de lectura), su ventilador **se enciende** para proteger el hardware monitoreado.

---

## 🛡️ Operación Desatendida

El sistema está pensado para funcionar **24/7 sin supervisión**:

- **`try/except` en el loop principal**: ninguna excepción mata el programa. Si algo falla en una iteración, se loggea, se intenta mostrar en el OLED y se continúa con la siguiente.
- **Watchdog timer (WDT)**: si el loop se bloquea más de `WATCHDOG_TIMEOUT_MS` (8 s por defecto), el RP2040 se reinicia automáticamente. Configurable o desactivable desde `config.py` (`WATCHDOG_ENABLED`).
- **Failsafe de ventiladores**: ante un sensor caído, el ventilador correspondiente se enciende.
- **Arranque automático**: al alimentar el Pico, MicroPython ejecuta `main.py` desde la raíz del filesystem.

---

## 🚀 Uso

### Ejecución normal

El archivo `main.py` ejecuta el loop infinito: lee los dos termopares cada 0.5 s, controla los ventiladores y refresca la pantalla OLED.

```python
# Ejecutar desde el REPL del Pico
import main
main.run()
```

Al guardar `main.py` en la raíz del filesystem del Pico, se ejecuta automáticamente cada vez que se enciende el dispositivo.

### Ajustar parámetros

Editar **`config.py`** para cambiar pines, umbrales o intervalo de actualización sin tocar el resto del código. Parámetros clave:

| Constante              | Valor por defecto | Descripción                                                              |
|------------------------|-------------------|--------------------------------------------------------------------------|
| `FAN_THRESHOLD_TEMP`   | `55.0` °C         | Temperatura a la que se enciende el ventilador.                          |
| `FAN_HYSTERESIS`       | `2.0` °C          | Margen bajo el umbral para apagar el ventilador.                         |
| `UPDATE_INTERVAL_MS`   | `500` ms          | Periodo del loop principal (mínimo recomendado por MAX6675: ~250 ms).    |
| `SENSOR_WARMUP_MS`     | `300` ms          | Espera tras inicializar los MAX6675.                                     |
| `PIN_FAN_OIL`          | `11`              | GPIO del ventilador OIL.                                                 |
| `PIN_FAN_REF`          | `12`              | GPIO del ventilador REF.                                                 |
| `PIN_CS_OIL`           | `5`               | Chip-Select del MAX6675 OIL.                                             |
| `PIN_CS_REF`           | `6`               | Chip-Select del MAX6675 REF.                                             |
| `WATCHDOG_ENABLED`     | `True`            | Activa el reinicio automático ante bloqueo.                              |
| `WATCHDOG_TIMEOUT_MS`  | `8000` ms         | Timeout del WDT (máx. 8388 ms en RP2040).                                |

### Formato de pantalla

```
┌────────────────────────┐
│ OIL 125C*              │  <- Temp aceite  ( * = ventilador OIL ON )
│ REF  98C               │  <- Temp referencia
└────────────────────────┘
```

Si un sensor falla, se muestra `OIL ERR  *` / `REF ERR  *` (con `*` por failsafe).

### Tests de diagnóstico

Los scripts de la carpeta `tests/` ayudan a validar el hardware antes de ejecutar el sistema completo:

```python
# Desde el REPL del Pico, después de copiar el test correspondiente a la raíz:
import test_max6675           # 2 sensores
import test_single_max6675    # 1 sensor (debug de cableado)
import test_pins              # Pines GPIO
import test_spi_loopback      # Bus SPI
```

---

## 🔍 Troubleshooting

### Problema: Pantalla OLED no enciende

**Síntomas:**
- Pantalla negra, sin iluminación

**Soluciones:**
1. Verifica la alimentación (3.3V y GND)
2. Confirma la dirección I2C (puede ser 0x3C o 0x3D):
   ```python
   from machine import I2C, Pin
   i2c = I2C(0, sda=Pin(0), scl=Pin(1))
   print(i2c.scan())  # Debe mostrar [60] (0x3C) o [61] (0x3D)
   ```
3. Verifica las conexiones SDA (GP0) y SCL (GP1)

---

### Problema: MAX6675 retorna 0x00 0x00

**Síntomas:**
- Temperatura siempre 0.0°C
- Bytes crudos: `0x00 0x00`

**Soluciones:**
1. **Verifica alimentación:** MAX6675 debe tener 3.3V entre VCC y GND
2. **Verifica cable SO (MISO):** Debe estar conectado a GP4 (Pin 6)
3. **Verifica cable SCK:** Debe estar conectado a GP2 (Pin 4)
4. **Verifica cable CS:** Debe estar conectado a GP5 o GP6
5. **Ejecuta test de diagnóstico:**
   ```python
   import test_single_max6675
   ```

---

### Problema: Bit 2 = 1 (Termopar desconectado)

**Síntomas:**
- Mensaje: "ERROR: TERMOPAR DESCONECTADO"
- Temperatura: None o error

**Soluciones:**
1. **Verifica conexión del termopar al MAX6675:**
   - T+ (amarillo) debe estar en el terminal T+ del MAX6675
   - T- (rojo) debe estar en el terminal T- del MAX6675
2. **Verifica que el termopar no esté roto:**
   - Mide continuidad con multímetro entre los cables del termopar
3. **Espera 500ms después de encender:** El MAX6675 necesita tiempo de estabilización

---

### Problema: Temperatura incorrecta o errática

**Síntomas:**
- Temperatura muy alta o muy baja
- Valores que cambian drásticamente

**Soluciones:**
1. **Verifica el tipo de termopar:** Debe ser tipo K
2. **Compensación de unión fría:** El MAX6675 la hace automáticamente, pero necesita estar a temperatura ambiente estable
3. **Interferencia electromagnética:**
   - Usa cables blindados
   - Aleja los cables de fuentes de ruido (motores, relés, etc.)
4. **Espera entre lecturas:** Mínimo 220ms entre lecturas consecutivas

---

### Problema: Solo funciona un MAX6675

**Síntomas:**
- Un sensor lee correctamente, el otro retorna 0x00

**Soluciones:**
1. **Verifica que ambos compartan SCK y MISO:**
   - SCK (GP2) debe ir a ambos MAX6675
   - MISO (GP4) debe ir a ambos MAX6675
2. **Verifica que cada uno tenga su propio CS:**
   - MAX6675 #1: CS → GP5
   - MAX6675 #2: CS → GP6
3. **Verifica alimentación de ambos módulos**
4. **Prueba cada MAX6675 individualmente** con `test_single_max6675.py`

---

## 📝 Notas Importantes

### Sobre los termopares tipo K

1. **Polaridad:** Los termopares tipo K tienen polaridad. T+ es amarillo, T- es rojo.
2. **Rango de temperatura:** 0-800°C, pero el MAX6675 solo lee hasta 1024°C
3. **Precisión:** ±1.5% o ±2.2°C (lo que sea mayor)
4. **Tiempo de respuesta:** Depende de la masa térmica del sensor (típicamente 1-3 segundos)

### Sobre el MAX6675

1. **Tiempo de conversión:** 220ms típico, 250ms máximo
2. **No leer más rápido de 4Hz** (cada 250ms)
3. **Detección automática de termopar abierto:** Bit 2 = 1 indica desconexión
4. **Resolución:** 0.25°C (12 bits)
5. **Solo lectura:** El MAX6675 no tiene registros de configuración

### Sobre el protocolo SPI

1. **Modo SPI:** Mode 0 (CPOL=0, CPHA=0)
2. **Velocidad máxima:** 4.3 MHz (usamos 1 MHz para estabilidad)
3. **Orden de bits:** MSB primero
4. **Formato de datos:** 16 bits (2 bytes)

### Formato de datos del MAX6675

```
Bit 15: Dummy bit (siempre 0)
Bits 14-3: Temperatura (12 bits) en unidades de 0.25°C
Bit 2: Termopar abierto (1 = desconectado, 0 = OK)
Bit 1: Device ID (siempre 0)
Bit 0: Estado de entrada (siempre 0)
```

Ejemplo:
```
0b0001100100000000 = 0x1900
Temperatura = (0x1900 >> 3) * 0.25 = 200 * 0.25 = 50.0°C
```

---

## 🛠️ Ejemplos de Código

### Lectura usando los módulos del proyecto (recomendado)

```python
from machine import SPI, Pin
import time

import config
from modules.temperature import TemperatureSensor

spi = SPI(0,
          baudrate=config.SPI_BAUDRATE,
          polarity=0, phase=0,
          sck=Pin(config.PIN_SPI_SCK),
          mosi=Pin(config.PIN_SPI_MOSI),
          miso=Pin(config.PIN_SPI_MISO))

sensor_oil = TemperatureSensor(spi, cs_pin=config.PIN_CS_OIL, name="OIL")
time.sleep_ms(config.SENSOR_WARMUP_MS)

while True:
    t = sensor_oil.read()
    print("OIL =", t, "OK" if sensor_oil.is_ok else "ERR")
    time.sleep_ms(config.UPDATE_INTERVAL_MS)
```

### Control manual de un ventilador

```python
import config
from modules.fan_control import FanController

fans = FanController(
    pin_oil=config.PIN_FAN_OIL,
    pin_ref=config.PIN_FAN_REF,
    threshold=config.FAN_THRESHOLD_TEMP,
    hysteresis=config.FAN_HYSTERESIS,
)

fans.update(temp_oil=60.0, temp_ref=20.0)   # OIL ON, REF OFF
print(fans.fan_oil.state, fans.fan_ref.state)
fans.all_off()
```

### Lectura directa con el driver de bajo nivel (debug)

```python
from machine import Pin, SPI
from lib.max6675 import MAX6675
import time

spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
          sck=Pin(2), mosi=Pin(3), miso=Pin(4))
sensor = MAX6675(spi, cs_pin=5)
time.sleep_ms(500)

temp = sensor.read_temperature()
print("Temperatura:", temp, "°C" if temp is not None else "(termopar desconectado)")
```

---

## 📚 Referencias

- [MAX6675 Datasheet](https://datasheets.maximintegrated.com/en/ds/MAX6675.pdf)
- [Termopar Tipo K - Wikipedia](https://es.wikipedia.org/wiki/Termopar)
- [SSD1306 OLED Driver](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py)
- [MicroPython Documentation](https://docs.micropython.org/)
- [Raspberry Pi Pico Datasheet](https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf)

---

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

## 🔄 Historial de cambios

### v2.0 — Mayo 2026 (reestructuración + control de ventiladores)
- ♻️ **Arquitectura modular**: nuevos directorios `lib/` (drivers) y `modules/` (lógica de aplicación).
- 🆕 **`main.py`** como punto de entrada único con loop infinito y manejo de excepciones.
- 🆕 **`config.py`**: configuración centralizada de pines, umbrales y tiempos.
- 🆕 **`modules/temperature.py`**: clase `TemperatureSensor` con manejo de errores y conteo de fallos.
- 🆕 **`modules/fan_control.py`**: clases `Fan` y `FanController` con control independiente, histéresis y failsafe.
- 🆕 **`modules/display.py`**: clase `DisplayManager` con render del estado del sistema y mensajes de boot/error.
- 🆕 **Control automático de 2 ventiladores** en GP11 (OIL) y GP12 (REF), umbral configurable (55 °C por defecto).
- 🆕 **Watchdog timer** activable desde `config.py` para reinicio automático ante bloqueo.
- 🆕 **Lectura continua** cada 500 ms.
- 📁 Tests movidos a `tests/`.
- 📚 README completamente actualizado con la nueva arquitectura.

### v1.0 — Mayo 2026 (versión inicial)
- ✅ Implementación inicial con 2 termopares tipo K
- ✅ Driver MAX6675 con detección de errores
- ✅ Pantalla OLED SSD1306 con texto escalado
- ✅ Tests de diagnóstico completos
- ✅ Documentación completa

---

**¿Preguntas o problemas?** Revisa la sección de [Troubleshooting](#troubleshooting) o ejecuta los tests de diagnóstico.
# screen
