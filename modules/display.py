"""
display.py - Gestion de la pantalla OLED SSD1306

Muestra las temperaturas de ambos sensores junto con el estado de los
ventiladores en una pantalla de 128x32 pixeles.
"""
from machine import I2C, Pin
from framebuf import FrameBuffer, MONO_HLSB

from lib.ssd1306 import SSD1306_I2C


class DisplayManager:
    """Encapsula el display OLED y las primitivas de dibujo del sistema."""

    def __init__(self, width, height, sda_pin, scl_pin, addr=0x3C, freq=400_000):
        """
        Args:
            width:   Ancho del display en pixeles.
            height:  Alto del display en pixeles.
            sda_pin: GPIO del SDA del bus I2C.
            scl_pin: GPIO del SCL del bus I2C.
            addr:    Direccion I2C del display.
            freq:    Frecuencia del bus I2C.
        """
        self.width = width
        self.height = height
        self._i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=freq)
        self._display = SSD1306_I2C(width, height, self._i2c, addr=addr)
        self.clear()

    # ------------------------------------------------------------------
    # Primitivas
    # ------------------------------------------------------------------
    def clear(self):
        """Limpia el buffer del display."""
        self._display.fill(0)

    def show(self):
        """Envia el buffer al display."""
        self._display.show()

    def big_text(self, text, x, y, scale=2):
        """
        Dibuja texto escalado en el display.

        Usa un FrameBuffer temporal para renderizar el texto en tamano base
        (8x8 por caracter) y luego lo replica pixel a pixel al tamano deseado.
        """
        width = len(text) * 8
        buf = bytearray(width * 8)
        fb = FrameBuffer(buf, width, 8, MONO_HLSB)
        fb.fill(0)
        fb.text(text, 0, 0, 1)

        for yy in range(8):
            for xx in range(width):
                if fb.pixel(xx, yy):
                    self._display.fill_rect(
                        x + xx * scale,
                        y + yy * scale,
                        scale, scale, 1
                    )

    # ------------------------------------------------------------------
    # Render del sistema
    # ------------------------------------------------------------------
    def render(self, temp_oil, temp_ref, fan_oil_on, fan_ref_on):
        """
        Dibuja el estado completo del sistema y lo envia al display.

        Layout (128x32):
          Linea 1 (y=0):  OIL  <temp>C  [*]
          Linea 2 (y=16): REF  <temp>C  [*]

        Un asterisco al final indica que el ventilador de esa linea esta ON.
        Si la temperatura es None, se muestra "ERR".
        """
        self.clear()

        oil_str = self._format_line("OIL", temp_oil, fan_oil_on)
        ref_str = self._format_line("REF", temp_ref, fan_ref_on)

        self.big_text(oil_str, 0, 0, scale=2)
        self.big_text(ref_str, 0, 16, scale=2)
        self.show()

    @staticmethod
    def _format_line(label, temp, fan_on):
        """Construye la cadena de una linea de temperatura."""
        mark = "*" if fan_on else " "
        if temp is None:
            return "{} ERR  {}".format(label, mark)
        return "{} {}C{}".format(label, int(temp), mark)

    def show_message(self, line1, line2=""):
        """Muestra dos lineas de texto (util para mensajes de arranque/error)."""
        self.clear()
        self.big_text(line1, 0, 0, scale=2)
        if line2:
            self.big_text(line2, 0, 16, scale=2)
        self.show()
