"""
Test para UN SOLO MAX6675
Configuración de pines: [GND] [VCC] [SCK] [CS] [SO]
"""
from machine import Pin, SPI
import time

print("\n" + "="*50)
print("TEST MAX6675 - UN SOLO SENSOR")
print("="*50)

print("\nCONEXIONES:")
print("  MAX6675 Pin 1 [GND] -> Pico Pin 38 (GND)")
print("  MAX6675 Pin 2 [VCC] -> Pico Pin 36 (3.3V)")
print("  MAX6675 Pin 3 [SCK] -> Pico Pin 4  (GP2)")
print("  MAX6675 Pin 4 [CS]  -> Pico Pin 7  (GP5)")
print("  MAX6675 Pin 5 [SO]  -> Pico Pin 6  (GP4/MISO)")

# Configurar SPI
print("\n1. Inicializando SPI...")
spi = SPI(0,
          baudrate=1000000,
          polarity=0,
          phase=0,
          sck=Pin(2),
          mosi=Pin(3),
          miso=Pin(4))

# Configurar CS
print("2. Configurando CS en GP5...")
cs = Pin(5, Pin.OUT)
cs.value(1)  # Desactivado

# Esperar estabilización
print("3. Esperando 500ms para que el MAX6675 se estabilice...")
time.sleep_ms(500)

# Hacer varias lecturas
print("\n4. Realizando 5 lecturas consecutivas...\n")
for i in range(5):
    print(f"--- Lectura {i+1} ---")
    
    # Activar CS
    cs.value(0)
    time.sleep_us(100)
    
    # Leer 2 bytes
    data = spi.read(2)
    
    # Desactivar CS
    cs.value(1)
    time.sleep_ms(250)  # MAX6675 necesita 220ms entre lecturas
    
    # Procesar datos
    byte0 = data[0]
    byte1 = data[1]
    raw = (byte0 << 8) | byte1
    
    print(f"  Bytes: 0x{byte0:02X} 0x{byte1:02X}")
    print(f"  Raw: {raw} = 0b{raw:016b}")
    
    # Analizar bits importantes
    bit_15 = (raw >> 15) & 1  # Dummy bit
    bit_2 = (raw >> 2) & 1     # Thermocouple open
    bit_1 = (raw >> 1) & 1     # Device ID
    bit_0 = raw & 1            # Input state
    
    print(f"  Bit 15 (dummy): {bit_15}")
    print(f"  Bit 2 (termopar abierto): {bit_2}", end="")
    
    if bit_2 == 1:
        print(" <- ERROR: TERMOPAR DESCONECTADO")
    else:
        print(" <- OK")
        temp_raw = raw >> 3
        temp = temp_raw * 0.25
        print(f"  Temperatura: {temp}°C")
    
    print()

print("="*50)
print("DIAGNÓSTICO:")
if all(data[0] == 0 and data[1] == 0 for _ in range(1)):
    print("✗ Todos los bytes son 0x00")
    print("  Posibles causas:")
    print("  - MAX6675 no tiene alimentación (verifica 3.3V)")
    print("  - Cable SO (MISO) desconectado o en pin incorrecto")
    print("  - Cable SCK desconectado")
    print("  - MAX6675 defectuoso")
else:
    print("✓ MAX6675 responde correctamente")
print("="*50)
