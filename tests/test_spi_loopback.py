"""
Test SPI Loopback - Verificar que el SPI funciona
Conecta temporalmente MOSI (GP3) a MISO (GP4) con un cable
"""
from machine import Pin, SPI
import time

print("\n" + "="*40)
print("TEST SPI LOOPBACK")
print("="*40)
print("INSTRUCCIONES:")
print("1. Conecta GP3 (MOSI) a GP4 (MISO) con un cable")
print("2. Presiona Enter cuando esté listo...")
input()

# Configurar SPI
spi = SPI(0,
          baudrate=1000000,
          polarity=0,
          phase=0,
          sck=Pin(2),
          mosi=Pin(3),
          miso=Pin(4))

print("\nEnviando datos de prueba...")
# Escribir y leer simultáneamente
test_data = bytearray([0xAA, 0x55])
result = bytearray(2)

spi.write_readinto(test_data, result)

print(f"\nDatos enviados: 0x{test_data[0]:02X} 0x{test_data[1]:02X}")
print(f"Datos recibidos: 0x{result[0]:02X} 0x{result[1]:02X}")

if result[0] == 0xAA and result[1] == 0x55:
    print("\n✓ SPI FUNCIONA CORRECTAMENTE")
    print("El problema está en el MAX6675 o sus conexiones.")
else:
    print("\n✗ SPI NO FUNCIONA")
    print("Verifica que GP3 y GP4 estén conectados.")

print("\nQuita el cable entre GP3 y GP4 antes de continuar.")
print("="*40)
