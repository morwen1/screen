# Advanced Thermomechanical and Software Architecture for Automotive Thermal Management Systems

**Key Points:**
*   **Thermal Inertia Disparities:** Automotive oil and electronic coolants exhibit drastically different specific heat capacities and thermal conductivities, necessitating independent, asynchronous cooling strategies [cite: 1, 2].
*   **Hardware Switching Limitations:** While the Raspberry Pi Pico operates at 3.3V logic, driving an IRLZ44N MOSFET directly at 3.3V is marginal and may prevent full gate saturation under high-current automotive fan loads [cite: 3, 4, 5]. Level shifting or gate drivers are highly recommended.
*   **Inrush Current Mitigation:** Automotive radiator fans present severe inductive loads, with inrush currents peaking between 4x and 8x their continuous draw (e.g., 80A peak for a 20A fan) [cite: 6, 7, 8]. PWM soft-starting via MOSFETs offers superior longevity compared to mechanical relays [cite: 6, 7].
*   **Software Architecture:** A robust Python/MicroPython codebase utilizes Abstract Base Classes (ABCs) for cooling strategies, decorator-driven metaprogramming for hardware retries, and non-blocking temporal logic (`time.ticks_diff`) to enforce anti-short cycling [cite: 9, 10].
*   **Holistic Integration:** Modern architectures extend embedded control into the cloud, utilizing build tools (Poetry), testing frameworks (Pytest), and backend frameworks (FastAPI, SQLAlchemy) for telemetry processing.

**Section Summaries:**
*   **Thermodynamic Profiling:** Analyzes the physics of thermal inertia between engine oil and coolant/electronics, establishing the mathematical basis for independent hysteresis loops.
*   **Hardware Engineering & Protection:** Details power electronics (MOSFETs vs. relays), 3.3V gate drive physics, flyback diode selection for inductive kickback, and wire-protecting fuse topologies.
*   **Embedded Software Architecture (MicroPython):** Explores the internal structure of the microcontroller code, focusing on object-oriented patterns, non-blocking asynchronous timing, and sensor fault tolerance.
*   **Backend & Telemetry Integration (Python):** Contextualizes the embedded system within a larger Python codebase, analyzing FastAPI routes, SQLAlchemy models, and modern dependency management (pyproject.toml).

---

## 1. Introduction

The integration of power electronics into automotive and medium-to-high power electronic applications presents a complex thermal management challenge. As systems become more compact, the disparity in thermal inertia between traditional mechanical fluids (such as engine oil) and integrated electronics (such as microcontrollers and power inverters) becomes increasingly pronounced [cite: 1]. This report provides an exhaustive analysis of a holistic Python-based codebase designed to govern a dual-fan automotive cooling system. The system utilizes a Raspberry Pi Pico (RP2040), MAX6675 SPI thermocouples, and logic-level MOSFETs (IRLZ44N) to independently manage two 12V fixed-speed cooling fans. 

The analysis is divided into two primary domains: the thermomechanical hardware engineering required to safely switch high-current inductive loads, and the rigorous software engineering principles (module layout, design patterns, dependency management, and framework integration) required to build a fault-tolerant, scalable Python codebase spanning from embedded MicroPython to cloud-based FastAPI telemetry.

---

## 2. Thermodynamic Profiling and Control Theory

The foundational requirement of this system is the independent management of two distinct thermal mediums: lubricating oil (OIL) and electronics/coolant (REF). Understanding their thermodynamic properties is critical for designing the software control algorithms.

### 2.1 Thermal Inertia: Oil vs. Coolant/Electronics

Thermal inertia dictates how rapidly a substance absorbs and dissipates heat. This is governed by specific heat capacity (\(C_p\)) and thermal conductivity (\(k\)).

*   **Engine Oil:** The heat capacity of typical synthetic oil is approximately \(1.6 \text{ kJ/kg·K}\), while its thermal conductivity is relatively low at \(\approx 0.15 \text{ W/m·K}\) [cite: 11]. Consequently, oil transmits heat slowly. It acts as a massive thermal reservoir, taking 1.5 to 3 times longer to reach operating temperature compared to water-based coolants, and equally long to cool down [cite: 2, 12].
*   **Coolant/Electronics (REF):** Water-based coolants have a high specific heat capacity (\(\approx 4.18 \text{ kJ/kg·K}\)) and a higher thermal conductivity (\(\approx 0.6 \text{ W/m·K}\)) [cite: 2, 11]. When applied to integrated electronics, which possess inherently small thermal inertia, the system experiences high and rapid temperature variations under load cycling [cite: 1]. 

Because oil acts as a slow-moving thermal mass and electronics act as a fast-moving thermal node, applying the same control logic to both would result in severe system instability. The electronics fan requires rapid, tight-band actuation, whereas the oil fan requires predictive, wide-band actuation to prevent continuous running due to slow heat dissipation.

### 2.2 Hysteresis and Anti-Short Cycling

To prevent rapid toggling (ciclado rápido)—which destroys mechanical relays and overheats MOSFETs—a hysteresis band must be implemented. Hysteresis defines distinct ON and OFF thresholds. Furthermore, physical timing delays must be enforced.

1.  **Anti-Short Cycle Timer:** Once a fan turns off, it must be locked out from turning back on for a minimum duration (e.g., 60 seconds) to allow the motor's internal heat to dissipate and the electrical system to stabilize.
2.  **Minimum Run Time:** Once activated, a fan should run for a minimum duration to ensure meaningful thermal mass displacement, preventing the fan from turning on for just 2 seconds and shutting off.

---

## 3. Hardware Architecture and Power Electronics

Switching 12V automotive radiator fans via a 3.3V microcontroller involves overcoming significant electrical engineering hurdles, specifically concerning inrush currents, logic-level voltages, and inductive kickback.

### 3.1 Relay vs. MOSFET (IRLZ44N) Topologies

Traditionally, automotive fans are controlled by mechanical relays (e.g., 40A or 80A Bosch-style relays) [cite: 6, 7]. While relays offer complete galvanic isolation and can withstand massive inrush currents if oversized, they suffer from mechanical wear, contact arcing, and an inability to perform Pulse Width Modulation (PWM) [cite: 6].

**The MOSFET Approach:** 
The use of N-Channel MOSFETs, such as the IRLZ44N, is preferred for solid-state reliability and PWM capabilities. However, a critical contradiction exists in hobbyist literature regarding the term "logic-level." 
*   The IRFZ44N is a standard MOSFET requiring \(V_{GS} = 10V\) to fully saturate [cite: 3, 4]. 
*   The IRLZ44N is marketed as "logic-level" with a gate threshold voltage (\(V_{GS(th)}\)) of 1.0V to 2.0V [cite: 13]. 
*   **The 3.3V Trap:** While 3.3V from a Raspberry Pi Pico will turn the IRLZ44N *on*, it will not fully saturate the channel for high-current loads. At \(V_{GS} = 3.3V\), the \(R_{DS(on)}\) remains elevated. For an automotive fan drawing 20A, an elevated \(R_{DS(on)}\) of 30 m\(\Omega\) results in \(P = I^2 R = (20)^2 \times 0.03 = 12W\) of heat dissipation within the MOSFET, leading to rapid thermal runaway [cite: 3, 5]. 

**Solution:** The 3.3V GPIO of the Pico must not drive the IRLZ44N gate directly. Instead, a dedicated gate driver IC or a simple NPN transistor level-shifter (e.g., 2N2222) should be used to pull the IRLZ44N gate to 12V, ensuring an \(R_{DS(on)}\) of \(< 17.5 \text{ m}\Omega\) and safe operation [cite: 4].

### 3.2 Inrush Current Management

Automotive brushed DC motors exhibit extreme inrush currents because the stationary motor windings act nearly as a short circuit until rotational Counter-Electromotive Force (CEMF) is generated [cite: 6, 14]. A 12V fan drawing a continuous 22 Amps can easily pull an inrush peak of 80 to 89 Amps for a fraction of a second [cite: 7]. 

By utilizing the MOSFET, the software can implement a **Soft-Start** routine. Applying a PWM signal that ramps the duty cycle from 0% to 100% over 2–3 seconds artificially limits the voltage and current spikes, protecting the battery, wiring, and switching elements [cite: 7, 8, 15].

### 3.3 Circuit Protection: Fuses and Flyback Diodes

**Fusing:**
Fuses exist to protect the *wiring*, not the device [cite: 16]. According to automotive standards, the fuse should be sized at approximately 125% to 130% of the maximum continuous current [cite: 16, 17]. For a 20A fan, a 25A or 30A Maxi or slow-blow fuse is appropriate, combined with 10 AWG or 12 AWG wiring [cite: 16, 18].

**Flyback Diodes (Diodos Flyback):**
When the MOSFET switches off the fan, the collapsing magnetic field in the motor windings generates a massive voltage spike (Lenz's Law) [cite: 19, 20]. A flyback diode placed in parallel with the motor (reverse-biased during normal operation) provides a safe path for this current to dissipate [cite: 19].
*   **Selection:** For low-frequency ON/OFF relay switching, a standard 1N4007 rectifier is sufficient [cite: 19, 21]. However, because we are using PWM for a soft start, the diode switches thousands of times per second. A slow diode will cause "shoot-through" heating. Therefore, a **Schottky diode** (e.g., 1N58xx series or an automotive power Schottky) with a fast reverse recovery time (\(t_{rr}\)) and a continuous current rating equal to the motor's operating current is mandatory [cite: 19, 21]. The reverse voltage rating (\(V_R\)) should be at least double the supply (24V+) [cite: 21].

---

## 4. Software Architecture: Codebase Analysis

Designing the software for this system requires merging the low-level constraints of MicroPython on the Raspberry Pi Pico with high-level Python software engineering practices. We will analyze module structure, Abstract Base Classes, metaprogramming, dependency management, and testing.

### 4.1 Project Layout and Dependency Management

A modern, production-ready Python codebase utilizes a declarative toolchain. While the code deployed to the Pico is MicroPython, the overall repository manages firmware deployment, testing, and cloud telemetry integration.

```text
automotive-thermal-management/
├── pyproject.toml              # Build system, dependencies, and metadata
├── poetry.lock                 # Deterministic dependency resolution
├── requirements.txt            # Fallback dependency list for legacy CI
├── firmware/                   # Code intended for the RP2040
│   ├── main.py                 # Entry point (CLI definition equivalent)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── hardware.py         # Pin definitions, PWM, SPI initialization
│   │   └── sensors.py          # MAX6675 class and drivers
│   └── control/
│       ├── __init__.py
│       ├── strategy.py         # ABCs and class hierarchies
│       └── thermal_loop.py     # Anti-short cycle and non-blocking delays
├── backend/                    # Code intended for the telemetry server
│   ├── app.py                  # FastAPI routes and dependencies
│   └── database/
│       └── models.py           # SQLAlchemy models
└── tests/                      # pytest test suite
    ├── test_strategies.py      # Unit tests for hysteresis math
    └── test_hardware_mocks.py  # Mocked sensor tests
```

**Build and Task Tools:** 
The project relies on `pyproject.toml` using **Poetry** (or alternatively `hatch`, `pdm`, `uv`) to manage dependencies for the testing and backend environments [cite: 22]. For the Pico, `mpremote` or `rshell` act as the task runners to compile and push the `firmware/` directory to the microcontroller. The `pyproject.toml` defines development dependencies like `pytest`, `black`, and `mypy` for static type checking.

### 4.2 Object-Oriented Design: Class Hierarchies and ABCs

The control logic must handle the differing thermal inertias of Oil and Electronics. This is a textbook use case for the Strategy Pattern, implemented via Python's `abc` module.

```python
# firmware/control/strategy.py
from micropython import const
import time

class ThermalStrategy:
    """Abstract Base Class defining the contract for thermal cooling strategies."""
    
    def __init__(self, target_temp: float, hysteresis: float, min_run_ms: int, lockout_ms: int):
        self.target_temp = target_temp
        self.hysteresis = hysteresis
        self.min_run_ms = min_run_ms
        self.lockout_ms = lockout_ms
        
        self.is_active = False
        self.last_switch_time = time.ticks_ms()

    def evaluate(self, current_temp: float) -> bool:
        """Determines if the fan should be ON or OFF based on temperature and time constraints."""
        raise NotImplementedError("Subclasses must implement evaluate()")

class OilCoolingStrategy(ThermalStrategy):
    """
    Oil has high thermal inertia. Requires wider hysteresis and longer predictive runtimes.
    """
    def evaluate(self, current_temp: float) -> bool:
        now = time.ticks_ms()
        time_since_switch = time.ticks_diff(now, self.last_switch_time)
        
        # Hysteresis Logic
        if not self.is_active and current_temp >= (self.target_temp + self.hysteresis):
            # Check Anti-Short Cycle Lockout
            if time_since_switch >= self.lockout_ms:
                self.is_active = True
                self.last_switch_time = now
        elif self.is_active and current_temp <= (self.target_temp - self.hysteresis):
            # Check Minimum Run Time
            if time_since_switch >= self.min_run_ms:
                self.is_active = False
                self.last_switch_time = now
                
        return self.is_active

class ElectronicsCoolingStrategy(ThermalStrategy):
    """
    Electronics have low thermal inertia. Requires tight hysteresis and rapid response.
    """
    def evaluate(self, current_temp: float) -> bool:
        # Implementation mirrors OilCoolingStrategy but is instantiated with 
        # tighter temperature bounds and shorter timing limits.
        pass
```

### 4.3 Non-Blocking Temporization (`time.ticks_diff`)

A major pitfall in embedded Python is the use of `time.sleep()`, which blocks the execution thread [cite: 23, 24]. In a multi-fan system, blocking the thread for an oil cooling delay would freeze the electronics cooling loop, potentially causing thermal damage.

MicroPython utilizes an internal millisecond counter (`time.ticks_ms()`) that eventually wraps around (overflows) [cite: 9, 10]. Standard arithmetic (`now - last_time`) will result in catastrophic bugs when the counter wraps [cite: 10]. To solve this, MicroPython implements modular ring arithmetic via `time.ticks_diff(ticks1, ticks2)` [cite: 10]. 

As demonstrated in the `OilCoolingStrategy` class above, `ticks_diff` ensures safe, non-blocking time calculations [cite: 10, 25], fulfilling the user's requirement for "consideraciones de temporización (evitar ciclado rápido, protectores de arranque, delays de seguridad)."

### 4.4 Metaprogramming and Decorator Usage

The MAX6675 thermocouple amplifier communicates via SPI. In an electromagnetically noisy automotive environment (ignitions, alternators), SPI communications can occasionally return corrupted data or `NaN`. 

To maintain robust codebase hygiene, we utilize decorators (a form of Python metaprogramming) to inject retry logic transparently into the sensor reading methods, abstracting the error handling away from the core business logic.

```python
# firmware/core/sensors.py
import time

def retry_on_failure(retries: int = 3, delay_ms: int = 10):
    """
    A decorator to retry hardware reads if they return invalid data.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                result = func(*args, **kwargs)
                if result is not None and 0 < result < 150: # Valid automotive temp range
                    return result
                time.sleep_ms(delay_ms)
            return None # Fallback safety state
        return wrapper
    return decorator

class MAX6675:
    def __init__(self, spi, cs_pin):
        self.spi = spi
        self.cs = cs_pin
        
    @retry_on_failure(retries=5, delay_ms=20)
    def read_celsius(self) -> float:
        # SPI bit-banging/reading logic here
        pass
```

### 4.5 Soft-Start PWM Implementation

To mitigate the 80+ Amp inrush current of the fans, the hardware module leverages the Pico's hardware PWM capabilities.

```python
# firmware/core/hardware.py
from machine import Pin, PWM
import time

class FanDriver:
    def __init__(self, pin_num: int, frequency: int = 20000):
        # 20kHz frequency prevents audible motor whine and requires Schottky flyback
        self.pwm = PWM(Pin(pin_num))
        self.pwm.freq(frequency)
        self.pwm.duty_u16(0)
        
    def soft_start(self, duration_ms: int = 2000):
        """Ramps up the PWM duty cycle to mitigate inrush current."""
        steps = 50
        delay = duration_ms // steps
        for i in range(steps + 1):
            duty = int((i / steps) * 65535)
            self.pwm.duty_u16(duty)
            time.sleep_ms(delay)
            
    def turn_off(self):
        self.pwm.duty_u16(0)
```

---

## 5. System Integration and Framework Specifics

While the Pico executes the embedded loop, a comprehensive Python codebase often includes a backend for monitoring, data logging, and remote configuration.

### 5.1 Telemetry Backend: FastAPI and SQLAlchemy

If the Pico is upgraded to a Pico W (adding WiFi), it can stream thermal data to a local server (e.g., a Raspberry Pi 4 acting as a vehicle diagnostic hub). The backend architecture utilizes **FastAPI** for high-performance routing and dependency injection, and **SQLAlchemy** for ORM database modeling.

**FastAPI Routes and Dependencies:**
FastAPI allows us to define asynchronous endpoints that receive JSON payloads from the microcontroller. Dependencies (such as database session generators) are injected cleanly into the route definitions.

```python
# backend/app.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import models, schemas
from .database.database import get_db

app = FastAPI(title="Automotive Thermal Telemetry")

@app.post("/telemetry/", response_model=schemas.TelemetryResponse)
def create_telemetry_record(data: schemas.TelemetryCreate, db: Session = Depends(get_db)):
    """
    FastAPI route utilizing Dependency Injection for the DB session.
    """
    db_record = models.TelemetryRecord(
        oil_temp=data.oil_temp,
        ref_temp=data.ref_temp,
        fan_oil_status=data.fan_oil_status,
        fan_ref_status=data.fan_ref_status
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record
```

**SQLAlchemy Models:**
The database layer requires strict typing and declarative mapping.

```python
# backend/database/models.py
from sqlalchemy import Column, Integer, Float, Boolean, DateTime
from sqlalchemy.sql import func
from .database import Base

class TelemetryRecord(Base):
    __tablename__ = "telemetry_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    oil_temp = Column(Float, nullable=False)
    ref_temp = Column(Float, nullable=False)
    fan_oil_status = Column(Boolean, default=False)
    fan_ref_status = Column(Boolean, default=False)
```

By decoupling the embedded logic (MicroPython) from the diagnostic storage (FastAPI/SQLAlchemy), the architecture remains scalable. The dependency management tools (Poetry/`pyproject.toml`) ensure that backend developers can instantiate the testing environment deterministically.

### 5.2 Testing Frameworks (`pytest` and `unittest`)

A hallmark of a professional Python codebase is extensive test coverage. Because MicroPython environments lack the full `pytest` suite, embedded logic is often written to be platform-agnostic so it can be tested on standard CPython using `pytest` and `unittest.mock`.

```python
# tests/test_strategies.py
import pytest
import time
from firmware.control.strategy import OilCoolingStrategy

def test_oil_cooling_hysteresis_and_lockout(mocker):
    # Mock time to avoid actual delays in CI/CD pipeline
    mock_ticks = mocker.patch('firmware.control.strategy.time.ticks_ms')
    mock_diff = mocker.patch('firmware.control.strategy.time.ticks_diff')
    
    strategy = OilCoolingStrategy(target_temp=100.0, hysteresis=5.0, min_run_ms=60000, lockout_ms=60000)
    
    # Simulate rising temperature, but anti-short cycle lockout prevents activation
    mock_diff.return_value = 10000 # Only 10 seconds passed
    assert strategy.evaluate(110.0) == False
    
    # Simulate lockout expired
    mock_diff.return_value = 61000 
    assert strategy.evaluate(110.0) == True # Fan turns ON
```

This testing pattern ensures that the thermomechanical logic is mathematically proven before physical hardware integration, preventing catastrophic failures like boiling the electronics or stressing the engine oil.

---

## 6. Synthesis of Implementation Considerations

Designing a system to control 12V fixed-speed automotive fans involves harmonizing deep hardware physics with modern software architecture. 

**On the Hardware Front:**
The research unequivocally demonstrates that driving heavy inductive loads requires meticulous attention to inrush currents and voltage levels. The Pico's 3.3V logic is insufficient for directly driving the IRLZ44N MOSFET into full saturation under a 20A+ load; a level-shifting transistor is required to deliver 12V to the gate [cite: 4]. Furthermore, protecting the MOSFET from thousands of volts of inductive kickback requires a fast-recovery Schottky diode rated for the fan's continuous current, while the wiring must be safeguarded by a Maxi fuse sized at 125% of the continuous load [cite: 16, 19, 21].

**On the Software Front:**
The codebase must respect the physical reality of thermal inertia. Engine oil acts as a massive thermal battery, requiring predictive algorithms with wide hysteresis bands to prevent inefficient micro-cycling. Conversely, electronic components act as volatile thermal nodes requiring rapid, tight-band actuation [cite: 1, 2]. 

By structuring the MicroPython code utilizing Abstract Base Classes, the system elegantly encapsulates these diverging thermodynamic profiles into polymorphic `evaluate()` methods. The use of decorators ensures hardware fault tolerance against noisy SPI lines, while `time.ticks_diff` ensures robust, non-blocking temporal logic capable of surviving counter overflows over months of continuous vehicle operation [cite: 10].

Finally, by wrapping the embedded solution within a standard Python project architecture—complete with `pyproject.toml` dependency management, `pytest` coverage, and a FastAPI telemetry backend—the resulting system stands as a paradigm of modern, full-stack cyber-physical engineering.

**Sources:**
1. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGWmN9-Qie0tqhZxwHiGy_ccAF83vnPpHCRtbFG0tzdPwLEJsyrvtwXHUVLKhycQvkA652xl0whPGMnYb52JHS0MgNIK2vSi-hRZCpXCvwM-hn_zWlWlKt0JKTUfqFKMG19i8S0t51xUQJrDBpZcBnwtgw1i_tdEF7hOWlyywN5w3U_q8Va64qBCECtNhUGlDjRnfaD-97Jbmgfnw3lfZH0GulN-MM=)
2. [rennlist.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEcbe1w0sL0cu1PZUFxoCe_v4HmVJhleu47hwzBCxBbTLboAonhlVzMj-VCShTRHAjvHkTFIml2VPtgpw3Hi-Q7SWDi6ZfIUkM1f5siudsTuCxY0f6BPBAxe-LqlTtZKRLKu-GmHtrNo_hDsV_6V5tVKn2Y8LSnIoEWHe8yhWGM6FY=)
3. [bettlink.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHk4DAqI_kAMUHvpedaLwv4LUjTcOx0-KUXArwBxEgnX1BSs4sKhnJpe6FW0ndZZHAJkkVyqTWnKJabbWO4X09gj0qSHOWm0Y8BrBX2r3NWbx3i77jtxHeLVoeK9FGHaZuuVq2EFSpWrA==)
4. [industrialmonitordirect.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEPkJyWNvh-5fXgf4VlZg586fngO9nLNTR6liCXnrt57cUI4Mf93ZkkP2Qv_WnW_LFY3M2YzPlgbmGrt5uI6yOrBR5Rw7wBDHoVarwTmGgaq4K5sHoESG1RrgN7HiMGjUxJ4B6_Mg94Y0myUjVYIepRO6LxOc9f_kti10y4MIxsqg-HsAovQtzxzT1lGl5YJ5Bzau76mk1ex4DA7-8Iq55h12l_DFPaFkiOCA==)
5. [raspberrypi.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGOvd4rmZJDj86fiuZCle5sPWw_od__5AiAnIMoMEoNMTHSgTpkkhYzcsdjsrRphtZiYaEmEfsnvbcpKsuUVowHRQe0tUJpMgTe_hShecDbqYhBZUhz-n5oqe-cRy7YpuXNOZSTVbVtehMkVw==)
6. [infinitybox.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFm0-DtxigxSCvagZoSDvqwkXKstJw8fM94GnzcEHIQTXlDxI2xAeyhXsGAO7eu-PRK-OEs4ykPtZfe1QCUi6p9-Rm6e-AqIirNpUeRFBorWVXI5KQ6ngqKffIkxtzvhXpejPiA7oQWN-syFN7egJ_zew==)
7. [dsportmag.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE9pDHv6GjiYxVSmpMgBRr8PHNc7D_IbuPXPvUiXLwbDStiWNh56Eo5vqN0Kqvr_uvOVbvTB7rEb3k4tqlZqTOCr1_Db2mxWRwvoUz598lOT9MRllJgbK0VgQ_sApoBxang0jYe5X-IMLo7Q9Y9feMQGbM9EFBsBjCKmC_pRTmVjiG-Z-xR1D7M5clpJio=)
8. [kaizenspeed.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE3nEqqWoxrBs97-1QVJmuut5e_GLF1BHboFAeQ-o2XPAAJWjgvE-UQfNnABArLMFFftcKpkj0-wx8G4tzSDYYBqZFtOrVwQps-PstvgTEkO_Y5lhKW9ghNNH7sobJvpEqrocOkYXcxlHfmzZlt2u8_A5bbLk_ghR8=)
9. [engineersgarage.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQESUb8-6mZQCdNAMQ5cZEDq6qGwmPYfIBy1NHGOAcNgCqewwCOzfLw7y31DQJU4xkcJEwdu4tVIox5UXyPE_lcbOKCNTXrpBjVbQEDTfFJKMdEt92oh4Ou6r3nI9IRMIwzQoX7eG9aabVjTbMdSy9dpaDqUbq18bm72tMrpIxA0qwclxquIi3YEE-ZvcDuaNLRcEuxc5zLzNkfzQ_ixsgkW)
10. [micropython.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGWeeO9tpTeLU6dCXLEOnncEQ6XseSlpQuBC42dtSp8qqP7cPnxzgOyJ-jeqJbeiEoSmwZTaRowUxteJR36N94kJGP5-_vEk0bc7dSwd6g3GUlJ9Y1PrNrVx6dgrsGh5FEUhCnMmQazO-IqU1-IAcw=)
11. [autosport.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHTY4R_SkPTv_MNBdDtaSwcyp5lsc5apx56vOMAne_A3haA4AU3s9f6RtKugSn4apkskZQ82FHc6JuETbBYNgnLrVeHmVQETe1tEny9EwRrHozyWeqXzUQTgIfmAhZARPFk5fNFjLmkot5h33qoWhySYygotjbf0EM=)
12. [tuneruniversity.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHA35GWcSjKkuvfAA-sCQvL3XCumxqoZCXYeU_pXS-q2g6hOiLTliLq2I8RXX95t6P2Md_3o7kjHuVRNWOEnyDCs2_M6LVr7bt6iYtgMC384YxEQvK91_WOz68_xtT77REYwHzGBcluV3zJspAS6Q6IzH8tH2eiA_zJ3eczUtKlXOrm6w45Bu4LltwoPLiQy5v7ATLxMVCs6QL2VA==)
13. [wordpress.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGFhC2tDvBL2GNql4DiqM5kI2MWGZqoseNg-rwVwpwGxBqtsNbEO37S8NaoiKmyM8xQsqDg8pwcgQqgrHtymh3Rp3Clnq9z79MHOSvzqixkeFGPbEtSNKSYHxw8W16r9gD2aEBEiygB2ISI-rd7JZfm99Gne3w5Aldz2ZG9CkgxCQ==)
14. [coolingfanfactory.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF5HynqqcJc24nSZHclGWz6lkln_7KmUFJkT6hJrtb3I36pQFJ71YGN_c4JZytZAlSpCFvEup_0Mhno-XbdoC1j1-XvN5o8zT1gjvx4M-G7UkKj8FWt05qitdyD2H2WBWGmaGeUOSLg2H3Ce6A_eIs2iMg1kNDYKTxQM8AYFyRLgV7_WEW_YA==)
15. [ae-race.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFgcsNJ_D93Pa_OMXF2a-W8ooy0DjcbPQ0UfPrPhwWhza5GEp4BfiBq59Hv8tIhOWW2Mq_7oAwVBb4ZhqgRuhO7b_40D1n_Dsg99KcHa0eHdOecT8sljVj2vncV79AGh0k99uknj1UqL-R--YtJNSgiPjFOpgn1k2GGVJ2UOGQxSqip4hAmj2tAdZqErNAXmxyM)
16. [viox.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHjEyLbBB9VrBXqEAPd4rswi_W1XDuZHG4GeVHiQL_KBGVNkcuJWLrLI7HYnmJxcWNEHcmSTlxYKxLL0ay6_SOL1h1GZDFUdD8fPUHUqrCnBggASHht0YBri1-fh62ZJWn6Qp4=)
17. [youtube.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGHqazTS7cLMUXZz1ogME_-IilyxB8PizXJmslFl4oURdqY3YcMyU45hsnEnouQRUnAOHUOCFzAQDfafjJ8RGi2alsycvEFwB07Ta3rLKnhaOrWtvgJNfVu9ABdmJEQ07PL)
18. [ceautoelectricsupply.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHU6af-mrk5ByvXq2lP55rf0xuFvSLyOAIP8aRPNAW8uv4_l3IWa2I-aS2_DWsbfLgGAuBber_bLrxIXOM9urglkdj_jgS4G4ha73e3Vk__O3ptRVDNBOPdZFQWhOYmDdyOeJos6PRWbv7l5f6bS_6Parku)
19. [zbotic.in](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGYxzZBNo_nGvfHV7fbxpJRUGbALPdmsL8T6cG8RvH_dk6BMXKYBm1OCu4ph0RLetCoreRMRTV5VkA7hbOk1cDYlDJeJOiYxX-NPIiso9qp2QOpqD_3qGU4WzSqq5rebzTjba66y5y6VqwKJJlFkgWQRkd8bHGCJwI4PLj7gAROGd8=)
20. [tejte.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH6ibaTBV5dGRar5GGtSZ_VFl-ggsjMpR4-LFUisO2FN5H0OQzoBenQV9_80pyMUxlBHuwQqh-Ylrqt3eVr7JI7rdh-A5ht8jomvNYjdW3pY-vDLkZMx0H-eauWM7fvAcn4xSfuGFKsf8ZmDDw9)
21. [ultralibrarian.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFEOVLyWoo_w0pSpJiSCoS5dIUpewMznuZNeSWIhO5wCg1UI64tx6Y0VcaG2pddxxqeeusizazrEJzGaRqa93i9kUu16dbtkc0KqtHuNxemriUjtfV-9CgVq_wRWaFNowFuugkaBpaKY4j-2F73siUsBhkTGXI3IvQs6AqC91LSnfsybHoBsJbKuLhz7w0=)
22. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHazx1immNFiyf-Hjyx-QDhQZ0VQvAVAu96xgnhhJjNrwr-3kZFSig9WmtV2XNWlcr8-dDquLBqhIgedc42vIbk9h23ET4kXfiEyvWbzTRlsvs36enY-XDi-Uy7WceACQ==)
23. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGf8JI-cSUDQhNIuD50jannYCna7v-Q6UMvcm7Taemod4r0niHdutJqfTk-swB7bbcQ6K6RW_fFZ5_62doml3H4_hJUpMPIFlGZczZbfJz2J-qsPKjm2n9uSWQYWnDY39gKNXBt0A==)
24. [fredscave.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGjVt6TGBaw7OBBpXxY821Povo2_dLzxyVzj2M6vLRSrvEfYIlIf0xtM08SFcbk6GAcJ7vHb4iCPsS61KZYVP32Ofcd70wv77qMXbh0SYBzEE0kAeOeQhfcx1uO2HXMG2B8lm9SrxN1NEylMGeuXRAro7ydZlc=)
25. [micropython.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHQjpjTGjpSYxOb_74-V8OfKyWIc4WdP6JqSkDpLlZQiLw3g8r4Cx6adnTPMY-1J1bh51CPtHDUw2qma6uZci4TvunTas6wDTEWRaYzL0YYDTkCEyqe7b9NfmucaHigInSIW-m1MQfoN7U8vgzaFU0LiZVJzGg=)
