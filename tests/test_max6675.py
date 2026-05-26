"""
Test simple para MAX6675 - Diagnóstico de conexión
"""
from machine import Pin, SPI
import time

print("\n" + "="*40)
print("TEST MAX6675 - DIAGNÓSTICO")
print("="*40)

# Configurar SPI
print("\n1. Configurando SPI...")
spi = SPI(0,
          baudrate=1000000,
          polarity=0,
          phase=0,
          sck=Pin(2),
          mosi=Pin(3),
          miso=Pin(4))
print(f"   SPI: {spi}")

# Configurar CS
print("\n2. Configurando pines CS...")
cs_oil = Pin(5, Pin.OUT)
cs_ref = Pin(6, Pin.OUT)
cs_oil.value(1)  # Desactivado
cs_ref.value(1)  # Desactivado
print("   CS OIL (GP5): HIGH")
print("   CS REF (GP6): HIGH")

# Esperar estabilización
print("\n3. Esperando 500ms para estabilización...")
time.sleep_ms(500)

# Leer sensor OIL
print("\n4. Leyendo MAX6675 OIL (CS=GP5)...")
cs_oil.value(0)  # Activar
time.sleep_us(100)
data_oil = spi.read(2)
cs_oil.value(1)  # Desactivar
time.sleep_ms(10)

print(f"   Byte 0: 0x{data_oil[0]:02X} = {data_oil[0]:08b}")
print(f"   Byte 1: 0x{data_oil[1]:02X} = {data_oil[1]:08b}")
raw_oil = (data_oil[0] << 8) | data_oil[1]
print(f"   Raw value: {raw_oil} = 0b{raw_oil:016b}")

# Analizar bits
bit_15 = (raw_oil >> 15) & 1
bit_2 = (raw_oil >> 2) & 1
bit_1 = (raw_oil >> 1) & 1
bit_0 = raw_oil & 1

print("\n   Análisis de bits:")
print(f"   - Bit 15 (dummy): {bit_15}")
status_oil = "ERROR: DESCONECTADO" if bit_2 else "OK"
print(f"   - Bit 2 (termopar abierto): {bit_2} <- {status_oil}")
print(f"   - Bit 1 (device ID): {bit_1}")
print(f"   - Bit 0 (input): {bit_0}")

if bit_2 == 0:
    temp_raw = raw_oil >> 3
    temp = temp_raw * 0.25
    print(f"   - Temperatura: {temp}°C (raw={temp_raw})")
else:
    print("   - Temperatura: NO DISPONIBLE (termopar desconectado)")

# Leer sensor REF
print("\n5. Leyendo MAX6675 REF (CS=GP6)...")
cs_ref.value(0)  # Activar
time.sleep_us(100)
data_ref = spi.read(2)
cs_ref.value(1)  # Desactivar

print(f"   Byte 0: 0x{data_ref[0]:02X} = {data_ref[0]:08b}")
print(f"   Byte 1: 0x{data_ref[1]:02X} = {data_ref[1]:08b}")
raw_ref = (data_ref[0] << 8) | data_ref[1]
print(f"   Raw value: {raw_ref} = 0b{raw_ref:016b}")

# Analizar bits
bit_15 = (raw_ref >> 15) & 1
bit_2 = (raw_ref >> 2) & 1
bit_1 = (raw_ref >> 1) & 1
bit_0 = raw_ref & 1

print("\n   Análisis de bits:")
print(f"   - Bit 15 (dummy): {bit_15}")
status_ref = "ERROR: DESCONECTADO" if bit_2 else "OK"
print(f"   - Bit 2 (termopar abierto): {bit_2} <- {status_ref}")
print(f"   - Bit 1 (device ID): {bit_1}")
print(f"   - Bit 0 (input): {bit_0}")

if bit_2 == 0:
    temp_raw = raw_ref >> 3
    temp = temp_raw * 0.25
    print(f"   - Temperatura: {temp}°C (raw={temp_raw})")
else:
    print("   - Temperatura: NO DISPONIBLE (termopar desconectado)")

print("\n" + "="*40)
print("FIN DEL TEST")
print("="*40)
