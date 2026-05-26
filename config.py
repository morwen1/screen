"""
config.py - Configuracion centralizada del sistema

Todas las constantes y parametros del sistema se definen aqui para facilitar
ajustes sin necesidad de modificar la logica del programa.
"""

# ============================================================================
# DISPLAY OLED SSD1306 (I2C)
# ============================================================================
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 32
DISPLAY_I2C_ADDR = 0x3C
DISPLAY_I2C_FREQ = 400_000
PIN_I2C_SDA = 0   # GP0
PIN_I2C_SCL = 1   # GP1

# ============================================================================
# SENSORES MAX6675 (SPI)
# ============================================================================
SPI_BAUDRATE = 1_000_000
PIN_SPI_SCK = 2    # GP2
PIN_SPI_MOSI = 3   # GP3 (no usado por MAX6675, requerido por API)
PIN_SPI_MISO = 4   # GP4

# Chip Select de cada termopar
PIN_CS_OIL = 5     # GP5  - Sensor OIL
PIN_CS_REF = 6     # GP6  - Sensor REF

# ============================================================================
# VENTILADORES (Salidas digitales)
# ============================================================================
PIN_FAN_OIL = 11   # GP11 - Ventilador asociado al sensor OIL
PIN_FAN_REF = 12   # GP12 - Ventilador asociado al sensor REF

# ============================================================================
# PARAMETROS DE CONTROL
# ============================================================================
# Umbral de temperatura para activar ventiladores (grados Celsius).
FAN_THRESHOLD_TEMP = 55.0

# Histeresis: el ventilador se apaga cuando la temperatura baja del umbral
# menos este valor. Evita oscilaciones (encendido/apagado constante).
FAN_HYSTERESIS = 2.0

# Tiempo minimo de marcha (ms): una vez encendido, el ventilador no puede
# apagarse hasta cumplir este tiempo. Evita ciclos cortos inutiles.
FAN_MIN_RUN_MS = 30_000

# Bloqueo anti-cortociclo (ms): una vez apagado, el ventilador no puede
# volver a encenderse hasta que pase este tiempo. Protege motor y switching.
# El failsafe (sensor caido) ignora este bloqueo.
FAN_LOCKOUT_MS = 60_000

# Intervalo entre lecturas del loop principal (milisegundos).
# MAX6675 requiere minimo ~220ms entre lecturas.
UPDATE_INTERVAL_MS = 500

# Tiempo de estabilizacion inicial del MAX6675 al arrancar (ms).
SENSOR_WARMUP_MS = 300

# ============================================================================
# WATCHDOG (operacion desatendida)
# ============================================================================
# Timeout del watchdog en ms. Si el loop principal no hace feed() en este
# tiempo, el Pico se reinicia automaticamente. Maximo 8388 ms en RP2040.
WATCHDOG_TIMEOUT_MS = 8000
WATCHDOG_ENABLED = True
