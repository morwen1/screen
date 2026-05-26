# AGENTS.md — Temperature Monitor (Pico + MicroPython)

**Platform:** Raspberry Pi Pico RP2040, MicroPython. NOT standard CPython.
- `from machine import ...` is hardware-specific — cannot import/run on a PC.
- No pip, pytest, mypy, linter, typechecker, or CI. All code runs on-device.

## Entrypoints

- **Active:** `main.py` (v2.0 modular) — call `main.run()` from REPL.
- **Legacy (v1.0):** `screen.py`, `temp_sensors.py` — replaced, do not modify.

## Project structure

```
main.py            # Entry point, infinite loop, watchdog
config.py          # Single source of truth for pins, thresholds, timings
lib/               # Low-level hardware drivers
  max6675.py       # MAX6675 SPI driver (thermocouple)
  ssd1306.py       # SSD1306 I2C driver (OLED display)
modules/           # Application logic
  temperature.py   # TemperatureSensor wrapper with error tracking
  fan_control.py   # Fan + FanController with hysteresis & failsafe
  display.py       # DisplayManager rendering
tests/             # Diagnostic REPL scripts — NOT unit tests
```

## Deployment

Preferred method — VS Code + [MicroPico extension](https://marketplace.visualstudio.com/items?itemName=paulober.pico-w-go) (`paulober.pico-w-go`).

CLI alternative with `mpremote`:
```bash
mpremote cp config.py main.py :          # root files
mpremote cp -r lib : && mpremote cp -r modules :
mpremote reset                            # auto-runs main.py
```

## Tests

All in `tests/` — copy to Pico root and `import` from REPL:
- `test_max6675.py` / `test_single_max6675.py` — sensor diagnostics
- `test_pins.py` — GPIO toggle check
- `test_spi_loopback.py` — SPI bus check (requires jumper GP3↔GP4)

No automated test runner exists; run manually on device.

## Hardware quirks

| Detail | Value |
|--------|-------|
| Display I2C addr | `0x3C` (GP0=SDA, GP1=SCL) |
| SPI shared bus | SCK=GP2, MISO=GP4, MOSI=GP3 (unused by MAX6675) |
| CS pins | GP5=OIL, GP6=REF |
| Fan GPIOs | GP11=OIL, GP12=REF |
| MAX6675 min interval | ≥220ms between reads (`UPDATE_INTERVAL_MS=500`) |
| Warmup after init | `SENSOR_WARMUP_MS=300` |
| WDT max timeout | 8388 ms on RP2040 (`WATCHDOG_TIMEOUT_MS=8000`) |

## Fan control logic (in `fan_control.py`)

- Independent per sensor: oil↔oil fan, ref↔ref fan.
- Hysteresis: ON at ≥threshold, OFF at <threshold−hysteresis, hold in between.
- Failsafe: sensor returns `None` → fan turns ON.

## Style notes

- All hardware configuration in `config.py` only — never hardcode pins/values in logic.
- `lib/max6675.py` includes debug `print()` calls on every read — expect noisy output.
- Screen.py `big_text()` was moved into `modules/display.py` as `DisplayManager.big_text()`.
