"""
Test básico de pines - Verificar que los pines GPIO funcionan
"""
from machine import Pin
import time

print("\n" + "="*40)
print("TEST DE PINES GPIO")
print("="*40)

# Test de pines de salida (CS)
print("\n1. Probando pines CS (salida)...")
cs5 = Pin(5, Pin.OUT)
cs6 = Pin(6, Pin.OUT)

print("   Alternando GP5...")
for i in range(3):
    cs5.value(1)
    print(f"   GP5 = HIGH")
    time.sleep_ms(200)
    cs5.value(0)
    print(f"   GP5 = LOW")
    time.sleep_ms(200)

print("\n   Alternando GP6...")
for i in range(3):
    cs6.value(1)
    print(f"   GP6 = HIGH")
    time.sleep_ms(200)
    cs6.value(0)
    print(f"   GP6 = LOW")
    time.sleep_ms(200)

# Test de pin MISO (entrada)
print("\n2. Probando GP4 (MISO - entrada)...")
miso = Pin(4, Pin.IN, Pin.PULL_UP)
print(f"   GP4 con pull-up: {miso.value()}")

miso_down = Pin(4, Pin.IN, Pin.PULL_DOWN)
print(f"   GP4 con pull-down: {miso_down.value()}")

print("\n" + "="*40)
print("Si ves valores alternando, los pines funcionan.")
print("Verifica las conexiones físicas del MAX6675.")
print("="*40)
