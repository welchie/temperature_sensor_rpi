# Sense HAT Data Logger

Logs Raspberry Pi Sense HAT sensor readings to a timestamped CSV file. Readings
are buffered in memory and written to disk in batches. The LED matrix shows
progress: the corner pixel blinks green on each write, the batch-average
temperature scrolls across the display, and a colour-coded history of those
averages fills the grid over time.

> The script in this folder is `data_logger_orig.py`; on the Pi it is deployed
> as `data_logger_v4.py`. The examples below use the deployed name.

## Requirements

- Raspberry Pi with a Sense HAT
- Python 3 (any version; run with `python3`, not `python` — the script is not
  Python 2 compatible)
- The `sense_hat` library (preinstalled on Raspberry Pi OS, otherwise
  `sudo apt install sense-hat`)

## Usage

```bash
python3 data_logger_v4.py [options]
```

Run with no options to log all default sensors every 5 seconds, writing to disk
every 100 readings. Stop with `Ctrl+C` — any readings still buffered are
written to the file before the program exits, so no data is lost.

Each run creates a new file named `<prefix>-YYYYMMDD-HHMMSS.csv` in the current
directory (e.g. `SenseLog-20260730-104055.csv`).

### Examples

```bash
# Default logging: all sensors except temp-h, one reading every 5 seconds
python3 data_logger_v4.py
```

```bash
# Quick test run: small batches and fast sampling so you can watch it work
python3 data_logger_v4.py --write-frequency 5 --delay 1
```

```bash
# Environment-only logging: no motion sensors, custom file prefix
python3 data_logger_v4.py --no-orientation --no-mag --no-accel --no-gyro --filename EnvLog
```

```bash
# Sample as fast as possible (no pause between readings)
python3 data_logger_v4.py --delay 0
```

## Parameters

### General options

| Option | Default | Description |
|---|---|---|
| `--filename PREFIX` | `SenseLog` | Prefix for the output CSV file. The run's start timestamp and `.csv` are appended automatically. |
| `--write-frequency N` | `100` | Number of readings to buffer in memory before writing them to disk in one batch. Lower values write more often (safer against power loss, more SD-card wear); higher values write less often. |
| `--delay SECONDS` | `5` | Seconds to wait between readings. Accepts decimals (e.g. `0.5`). Use `0` to sample as fast as possible. |
| `-h`, `--help` | — | Show the built-in help and exit. |

### Sensor toggles

Each sensor has an on flag (`--temp-h`) and an off flag (`--no-temp-h`). You
only need to pass a flag to change a sensor from its default.

| Sensor | Default | CSV columns | Description |
|---|---|---|---|
| `--temp-h` / `--no-temp-h` | off | `temp_h` | Temperature (°C) from the humidity sensor |
| `--temp-p` / `--no-temp-p` | on | `temp_p` | Temperature (°C) from the pressure sensor |
| `--humidity` / `--no-humidity` | on | `humidity` | Relative humidity (%) |
| `--pressure` / `--no-pressure` | on | `pressure` | Air pressure (millibars) |
| `--orientation` / `--no-orientation` | on | `pitch`, `roll`, `yaw` | Orientation (degrees) |
| `--mag` / `--no-mag` | on | `mag_x`, `mag_y`, `mag_z` | Raw magnetometer (microteslas) |
| `--accel` / `--no-accel` | on | `accel_x`, `accel_y`, `accel_z` | Raw accelerometer (g) |
| `--gyro` / `--no-gyro` | on | `gyro_x`, `gyro_y`, `gyro_z` | Raw gyroscope (radians/sec) |

## Output format

The CSV starts with a header row. Columns appear in the table's order above
(only for enabled sensors), followed by a final `timestamp` column in ISO 8601
format (`2026-07-30T10:40:55.060626`, local time).

Example with default sensors:

```
temp_p,humidity,pressure,pitch,roll,yaw,mag_x,mag_y,mag_z,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,timestamp
21.3,45.0,1013.2,2.0,3.0,1.0,0.1,0.2,0.3,0.01,0.02,0.98,0.001,0.002,0.003,2026-07-30T10:40:55.060626
```

## LED display

- **Startup**: scrolls "Loading........." and blinks the corner pixel red, then
  scrolls the current temperature (skipped if both temperature sensors are
  disabled).
- **Each batch write**: the corner pixel (bottom-right) blinks green twice,
  then the batch's average temperature scrolls across the display.
- **Temperature history**: each batch average lights one pixel, filling the
  grid column by column. Colour maps 10 °C (teal) through 30 °C (dark red);
  values outside that range show as bright teal. After 64 batches the grid
  clears and starts over.
- The temperature display uses `temp_h` if enabled, otherwise `temp_p`. If
  both are disabled, the display is skipped and only logging happens.

Note that the LED animations pause sampling briefly (a few seconds per batch
write), so timestamps around a write are spaced slightly wider than `--delay`.
