"""
main.py - Punto de entrada del sistema de monitoreo

Loop principal pensado para HARDWARE DESATENDIDO:

  - Lee dos termopares (OIL / REF) cada UPDATE_INTERVAL_MS.
  - Activa de forma INDEPENDIENTE dos ventiladores cuando su sensor
    supera FAN_THRESHOLD_TEMP (con histeresis).
  - Actualiza la pantalla OLED con temperaturas y estado de ventiladores.
  - Watchdog opcional para reinicio automatico ante un bloqueo.
  - El loop nunca debe terminar; cualquier excepcion se captura y se sigue
    ejecutando.

Pines y parametros se configuran en config.py.
"""
import time
from machine import SPI, Pin

try:
    from machine import WDT
    _HAS_WDT = True
except ImportError:  # algun port que no soporte WDT
    _HAS_WDT = False

import config
from modules.temperature import TemperatureSensor
from modules.fan_control import FanController
from modules.display import DisplayManager


# ----------------------------------------------------------------------------
# Inicializacion del hardware
# ----------------------------------------------------------------------------
def init_hardware():
    """Inicializa todos los perifericos y devuelve los objetos creados."""
    print("=== INICIALIZANDO HARDWARE ===")

    # Display OLED
    display = DisplayManager(
        width=config.SCREEN_WIDTH,
        height=config.SCREEN_HEIGHT,
        sda_pin=config.PIN_I2C_SDA,
        scl_pin=config.PIN_I2C_SCL,
        addr=config.DISPLAY_I2C_ADDR,
        freq=config.DISPLAY_I2C_FREQ,
    )
    display.show_message("BOOT", "...")
    print("Display OLED OK")

    # Bus SPI compartido por ambos MAX6675
    spi = SPI(
        0,
        baudrate=config.SPI_BAUDRATE,
        polarity=0,
        phase=0,
        sck=Pin(config.PIN_SPI_SCK),
        mosi=Pin(config.PIN_SPI_MOSI),
        miso=Pin(config.PIN_SPI_MISO),
    )
    print("SPI OK:", spi)

    sensor_oil = TemperatureSensor(spi, cs_pin=config.PIN_CS_OIL, name="OIL")
    sensor_ref = TemperatureSensor(spi, cs_pin=config.PIN_CS_REF, name="REF")

    # Espera de estabilizacion del MAX6675
    time.sleep_ms(config.SENSOR_WARMUP_MS)
    print("Sensores MAX6675 OK")

    # Controlador de ventiladores
    fans = FanController(
        pin_oil=config.PIN_FAN_OIL,
        pin_ref=config.PIN_FAN_REF,
        threshold=config.FAN_THRESHOLD_TEMP,
        hysteresis=config.FAN_HYSTERESIS,
        min_run_ms=config.FAN_MIN_RUN_MS,
        lockout_ms=config.FAN_LOCKOUT_MS,
    )
    print("Ventiladores OK (umbral {}C, min_run {}ms, lockout {}ms)".format(
        config.FAN_THRESHOLD_TEMP,
        config.FAN_MIN_RUN_MS,
        config.FAN_LOCKOUT_MS,
    ))

    print("=== HARDWARE LISTO ===\n")
    return display, sensor_oil, sensor_ref, fans


# ----------------------------------------------------------------------------
# Loop principal
# ----------------------------------------------------------------------------
def main_loop(display, sensor_oil, sensor_ref, fans, wdt=None):
    """Bucle infinito de lectura, control y visualizacion."""
    interval = config.UPDATE_INTERVAL_MS

    while True:
        try:
            # 1. Lectura de temperaturas
            temp_oil = sensor_oil.read()
            temp_ref = sensor_ref.read()

            # 2. Control de ventiladores (independiente por sensor)
            fans.update(temp_oil, temp_ref)

            # 3. Actualizar display
            display.render(
                temp_oil, temp_ref,
                fans.fan_oil.state, fans.fan_ref.state,
            )

            # 4. Log a UART (debugging via consola)
            print("OIL={} REF={}  FAN_OIL={} FAN_REF={}".format(
                temp_oil, temp_ref,
                "ON" if fans.fan_oil.state else "OFF",
                "ON" if fans.fan_ref.state else "OFF",
            ))

            # 5. Watchdog feed
            if wdt is not None:
                wdt.feed()

        except Exception as e:
            # Nunca dejamos morir el loop en hardware desatendido.
            print("ERROR en loop principal:", e)
            try:
                display.show_message("LOOP ERR", str(e)[:10])
            except Exception:
                pass
            if wdt is not None:
                wdt.feed()

        time.sleep_ms(interval)


# ----------------------------------------------------------------------------
# Arranque
# ----------------------------------------------------------------------------
def run():
    display = sensor_oil = sensor_ref = fans = None
    wdt = None

    try:
        display, sensor_oil, sensor_ref, fans = init_hardware()
    except Exception as e:
        # Si la inicializacion falla, no podemos hacer mucho mas que loggear
        # y reiniciar el dispositivo via watchdog.
        print("FATAL: fallo de inicializacion:", e)
        time.sleep(2)
        if _HAS_WDT and config.WATCHDOG_ENABLED:
            # Watchdog con timeout corto para forzar reinicio.
            WDT(timeout=1000)
            while True:
                time.sleep(1)
        raise

    if _HAS_WDT and config.WATCHDOG_ENABLED:
        wdt = WDT(timeout=config.WATCHDOG_TIMEOUT_MS)
        print("Watchdog activo ({} ms)".format(config.WATCHDOG_TIMEOUT_MS))

    main_loop(display, sensor_oil, sensor_ref, fans, wdt=wdt)


if __name__ == "__main__":
    run()
