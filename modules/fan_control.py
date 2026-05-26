"""
fan_control.py - Control automatico de ventiladores

Activa cada ventilador de forma independiente segun la temperatura de su
sensor asociado, aplicando histeresis y temporizadores de proteccion:

  - Tiempo minimo de marcha: una vez encendido, no puede apagarse hasta
    cumplir min_run_ms. Evita ciclos cortos inutiles.
  - Bloqueo anti-cortociclo: una vez apagado, no puede volver a encenderse
    hasta que pase lockout_ms. Protege motor y elemento de switching.

Toda la temporizacion es no-bloqueante (time.ticks_diff), segura frente al
wrap-around del contador de ms de MicroPython.

Estado por defecto seguro: si un sensor falla, su ventilador SE ENCIENDE
(failsafe) IGNORANDO el lockout, para proteger el hardware ante una
posible sobrecalentamiento.
"""
import time
from machine import Pin


class Fan:
    """Representa un ventilador controlado por un pin digital.

    Rastrea el instante del ultimo cambio de estado (last_switch_time) para
    que FanController pueda aplicar los temporizadores de proteccion.
    """

    def __init__(self, pin_number, name="fan"):
        self.name = name
        self._pin = Pin(pin_number, Pin.OUT)
        self._pin.value(0)
        self.state = False  # False = apagado, True = encendido
        # Marca temporal de la ultima transicion (se inicializa fuera para
        # permitir que el primer encendido no quede bloqueado por lockout).
        self.last_switch_time = time.ticks_ms()

    def on(self):
        if not self.state:
            self._pin.value(1)
            self.state = True
            self.last_switch_time = time.ticks_ms()

    def off(self):
        if self.state:
            self._pin.value(0)
            self.state = False
            self.last_switch_time = time.ticks_ms()

    def set(self, on):
        if on:
            self.on()
        else:
            self.off()


class FanController:
    """
    Controla dos ventiladores de forma INDEPENDIENTE.

    - Ventilador OIL responde al sensor OIL.
    - Ventilador REF responde al sensor REF.

    Logica con histeresis + temporizadores:
      - temp >= threshold  Y  lockout expirado     -> encender
      - temp <  threshold - hyst  Y  min_run cumplido -> apagar
      - zona intermedia o timer activo             -> mantener estado
      - temp is None (sensor KO)                   -> ON (failsafe, sin timers)
    """

    def __init__(self, pin_oil, pin_ref, threshold, hysteresis=2.0,
                 min_run_ms=30_000, lockout_ms=60_000):
        """
        Args:
            pin_oil: GPIO del ventilador OIL.
            pin_ref: GPIO del ventilador REF.
            threshold: Temperatura de activacion en grados Celsius.
            hysteresis: Margen para apagar (grados Celsius).
            min_run_ms: Tiempo minimo encendido antes de poder apagar.
            lockout_ms: Bloqueo tras apagado antes de poder volver a encender.
        """
        self.fan_oil = Fan(pin_oil, "FAN_OIL")
        self.fan_ref = Fan(pin_ref, "FAN_REF")
        self.threshold = threshold
        self.hysteresis = hysteresis
        self.min_run_ms = min_run_ms
        self.lockout_ms = lockout_ms

        # Inicializar timestamps en el pasado para que el primer encendido
        # legitimo no quede bloqueado por un lockout fantasma al arrancar.
        past = time.ticks_add(time.ticks_ms(), -lockout_ms)
        self.fan_oil.last_switch_time = past
        self.fan_ref.last_switch_time = past

    def _evaluate(self, fan, temp):
        """Aplica la logica de control con histeresis y temporizadores."""
        if temp is None:
            # Failsafe: si no podemos leer la temperatura, encender ventilador
            # IGNORANDO el lockout. La seguridad termica gana al anti-ciclado.
            fan.on()
            return

        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, fan.last_switch_time)

        if not fan.state:
            # Apagado -> evaluar encendido (respeta lockout).
            if temp >= self.threshold and elapsed >= self.lockout_ms:
                fan.on()
        else:
            # Encendido -> evaluar apagado (respeta tiempo minimo de marcha).
            if temp < (self.threshold - self.hysteresis) and elapsed >= self.min_run_ms:
                fan.off()
        # En cualquier otro caso (zona muerta o timer activo): mantener estado.

    def update(self, temp_oil, temp_ref):
        """Actualiza el estado de ambos ventiladores segun las temperaturas."""
        self._evaluate(self.fan_oil, temp_oil)
        self._evaluate(self.fan_ref, temp_ref)

    def all_off(self):
        """Apaga ambos ventiladores (uso en shutdown)."""
        self.fan_oil.off()
        self.fan_ref.off()
