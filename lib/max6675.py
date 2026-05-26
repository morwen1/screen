"""
Driver para MAX6675 - Amplificador de termopar tipo K
Interfaz SPI (solo lectura)
Resolución: 0.25°C, Rango: 0-1024°C
"""
from machine import Pin, SPI
import time


class MAX6675:
    def __init__(self, spi, cs_pin):
        """
        Args:
            spi: Objeto SPI ya inicializado
            cs_pin: Número de pin GPIO para Chip Select
        """
        self.spi = spi
        self.cs = Pin(cs_pin, Pin.OUT)
        self.cs.value(1)  # CS desactivado por defecto

    def read_raw(self):
        """Lee los 16 bits crudos del MAX6675."""
        self.cs.value(0)  # Activar chip
        time.sleep_us(100)  # Esperar 100us para estabilización
        data = self.spi.read(2)
        self.cs.value(1)  # Desactivar chip
        time.sleep_us(100)  # Esperar antes de próxima lectura
        raw_value = (data[0] << 8) | data[1]
        print(f"  DEBUG MAX6675: raw bytes={data[0]:02X} {data[1]:02X}, raw_value={raw_value:016b} ({raw_value})")
        return raw_value

    def read_temperature(self):
        """
        Lee la temperatura del termopar en °C.
        
        Returns:
            Temperatura en °C, o None si hay error (termopar desconectado)
        """
        raw = self.read_raw()
        
        # Bit 2 = 1 indica termopar desconectado
        if raw & 0x4:
            print(f"  ERROR: Termopar desconectado (bit 2 = 1)")
            return None
        
        # Bits 15-3 contienen la temperatura (13 bits)
        # Shift right 3 bits y multiplicar por resolución (0.25°C)
        temp_raw = raw >> 3
        temp = temp_raw * 0.25
        print(f"  Temp raw: {temp_raw}, Temperatura: {temp}°C")
        return temp
