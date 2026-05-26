from machine import I2C, Pin, SPI
from ssd1306 import SSD1306_I2C
from max6675 import MAX6675
import time

from framebuf import FrameBuffer, MONO_HLSB

def big_text(display, text, x, y, scale=2):
    width = len(text) * 8
    temp = bytearray(width * 8)
    fb = FrameBuffer(temp, width, 8, MONO_HLSB)
    fb.fill(0)
    fb.text(text, 0, 0, 1)

    for yy in range(8):
        for xx in range(width):
            if fb.pixel(xx, yy):
                display.fill_rect(
                    x + xx * scale,
                    y + yy * scale,
                    scale,
                    scale,
                    1
                )



SCREEN_WIDTH = 128
SCREEN_HEIGHT = 32

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
display = SSD1306_I2C(SCREEN_WIDTH, SCREEN_HEIGHT, i2c, addr=0x3C)

# Configuración SPI para los MAX6675
# SPI0: SCK=GP2, MISO=GP4 (MOSI no se usa, MAX6675 es solo lectura)
print("=== INICIALIZANDO SPI ===")
spi = SPI(0,
          baudrate=1000000,
          polarity=0,
          phase=0,
          sck=Pin(2),
          mosi=Pin(3),
          miso=Pin(4))
print(f"SPI configurado: {spi}")

# Dos termopares con CS diferentes
print("Creando sensores MAX6675...")
sensor_oil = MAX6675(spi, cs_pin=5)  # Termopar OIL - CS en GP5
sensor_ref = MAX6675(spi, cs_pin=6)  # Termopar REF - CS en GP6

# Esperar estabilización inicial (MAX6675 necesita ~250ms)
print("Esperando estabilización (300ms)...")
time.sleep_ms(300)

# Leer temperaturas
print("\n=== LEYENDO SENSOR OIL ===")
temp_oil = sensor_oil.read_temperature()

print("\n=== LEYENDO SENSOR REF ===")
temp_ref = sensor_ref.read_temperature()

print("\n=== LECTURAS TERMOPARES ===")
print(f"OIL: {temp_oil}°C" if temp_oil is not None else "OIL: DESCONECTADO")
print(f"REF: {temp_ref}°C" if temp_ref is not None else "REF: DESCONECTADO")
print("===========================")

display.fill(0)

# Mostrar temperatura OIL
if temp_oil is not None:
    big_text(display, f"OIL {int(temp_oil)}C", 0, 0, scale=2)
else:
    big_text(display, "OIL ERR", 0, 0, scale=2)

# Mostrar temperatura REF
if temp_ref is not None:
    big_text(display, f"REF {int(temp_ref)}C", 0, 16, scale=2)
else:
    big_text(display, "REF ERR", 0, 16, scale=2)

display.show()