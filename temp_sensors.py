

import math
from machine import ADC


def read_temperature(pin, vcc=3.3, r_pullup=10000):
    """
    Lee un sensor de temperatura NTC conectado a un pin analógico.

    Args:
        pin: Número del pin analógico (ej: 'A0', 0, etc.)
        vcc: Voltaje de alimentación del ADC (3.3V o 5V)
        r_pullup: Valor del resistor pull-up en ohms (típicamente 10kΩ)

    Returns:
        Temperatura en grados Celsius
    """

    valor_adc = get_adc_value(pin)
    print(f"  Pin {pin} - ADC raw (12-bit): {valor_adc}")

    if valor_adc <= 0:
        print(f"  Pin {pin} - ERROR: ADC = 0")
        return None

    v_adc = (valor_adc / 4096) * vcc
    print(f"  Pin {pin} - Voltaje ADC: {v_adc:.3f}V")
    
    # Evitar división por cero o valores muy cercanos a VCC
    if v_adc >= (vcc - 0.05):  # Margen de 50mV
        print(f"  Pin {pin} - ADVERTENCIA: V_ADC muy cerca de VCC ({v_adc:.3f}V >= {vcc-0.05:.3f}V)")
        print(f"  Pin {pin} - Posible circuito abierto o NTC desconectado")
        return None
    
    if v_adc <= 0.01:  # Voltaje muy bajo
        print(f"  Pin {pin} - ERROR: V_ADC muy bajo (cortocircuito?)")
        return None
    
    # Fórmula del divisor de voltaje: R_NTC = R_pullup * (VCC - V_ADC) / V_ADC
    r_ntc = r_pullup * ((vcc - v_adc) / v_adc)
    print(f"  Pin {pin} - R_NTC calculado: {r_ntc:.2f}Ω (R_pullup={r_pullup}Ω)")

    temp = calculate_ntc_temperature(r_ntc)
    print(f"  Pin {pin} - Temperatura: {temp}°C")
    
    return temp


def get_adc_value(pin):
    """
    Lee el valor del ADC del RP2040.
    
    Args:
        pin: Número del pin GPIO (26, 27, 28, o 29)
    
    Returns:
        Valor del ADC de 12 bits (0-4095)
    """
    adc = ADC(pin)
    # RP2040 ADC es de 16 bits (0-65535), convertir a 12 bits (0-4095)
    raw_value = adc.read_u16()
    return raw_value >> 4  # Shift right 4 bits para convertir de 16 a 12 bits


def calculate_ntc_temperature(r_ntc):
    """
    Calcula la temperatura desde la resistencia del NTC usando Steinhart-Hart.

    Args:
        r_ntc: Resistencia del sensor en ohms

    Returns:
        Temperatura en grados Celsius
    """
    if r_ntc <= 0:
        return None
    
    # Parámetros del NTC típico 10kΩ @ 25°C
    r0 = 10000      # Resistencia a 25°C
    b_value = 3950  # Coeficiente B típico
    t0 = 298.15     # Temperatura de referencia en Kelvin (25°C)

    # Ecuación simplificada de Steinhart-Hart usando coeficiente B
    # 1/T = 1/T0 + (1/B) * ln(R/R0)
    try:
        inv_t = (1 / t0) + (1 / b_value) * math.log(r_ntc / r0)
        t_kelvin = 1 / inv_t
        t_celsius = t_kelvin - 273.15
        return round(t_celsius, 2)
    except (ValueError, ZeroDivisionError):
        return None


def read_multiple_sensors(sensors):
    """Lee múltiples sensores de temperatura."""
    import sys
    temperatures = {}

    for sensor in sensors:
        pin = sensor.get('pin', 0)
        name = sensor.get('name', f'sensor_{pin}')
        vcc = sensor.get('vcc', 3.3)
        r_pullup = sensor.get('r_pullup', 10000)

        print(f"\n--- Leyendo {name} (Pin {pin}) ---")
        sys.stdout.flush()  # Forzar salida inmediata
        
        try:
            temp = read_temperature(pin, vcc, r_pullup)
            sys.stdout.flush()
            temperatures[name] = {
                'temperature': temp,
                'status': 'ok' if temp is not None else 'error'
            }
        except Exception as e:
            import traceback
            print(f"  EXCEPCIÓN CAPTURADA: {type(e).__name__}: {e}")
            traceback.print_exc()
            sys.stdout.flush()
            temperatures[name] = {
                'temperature': None,
                'status': 'error',
                'message': str(e)
            }

    return temperatures


def setup_temperature_sensors():
    """Configura los sensores de temperatura."""
    print("Configuración de sensores de temperatura...")
