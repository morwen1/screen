"""
temperature.py - Gestion de sensores de temperatura MAX6675

Encapsula la lectura de termopares tipo K via MAX6675 con manejo de errores
robusto para operacion desatendida.
"""
from lib.max6675 import MAX6675


class TemperatureSensor:
    """Wrapper sobre MAX6675 con manejo de errores y estado."""

    def __init__(self, spi, cs_pin, name="sensor"):
        """
        Args:
            spi: Bus SPI ya inicializado y compartido.
            cs_pin: GPIO del Chip Select para este sensor.
            name: Nombre identificador (para logs).
        """
        self.name = name
        self._sensor = MAX6675(spi, cs_pin=cs_pin)
        self.last_temp = None        # Ultima lectura valida
        self.last_error = None       # Mensaje de error si la ultima lectura fallo
        self.consecutive_errors = 0  # Conteo de errores seguidos

    def read(self):
        """
        Lee la temperatura actual.

        Returns:
            float | None: Temperatura en grados Celsius, o None si hay error.
        """
        try:
            temp = self._sensor.read_temperature()
            if temp is None:
                self.consecutive_errors += 1
                self.last_error = "termopar desconectado"
                return None

            # Lectura valida: resetear contadores de error
            self.last_temp = temp
            self.last_error = None
            self.consecutive_errors = 0
            return temp

        except Exception as e:
            self.consecutive_errors += 1
            self.last_error = str(e)
            return None

    @property
    def is_ok(self):
        """True si la ultima lectura fue exitosa."""
        return self.last_error is None and self.last_temp is not None
