#!/usr/bin/env python3
"""Log Sense HAT sensor readings to a timestamped CSV file.

Buffers readings in memory and writes them in batches, blinking the
corner pixel on each write and drawing a history of batch-average
temperatures on the LED grid.
"""
import argparse
import csv
from datetime import datetime
from statistics import mean
from time import sleep

from sense_hat import SenseHat

# Colour for each whole degree C on the LED grid
TEMP_COLORS = {
    10: (0, 200, 180),
    11: (0, 210, 150),
    12: (0, 220, 120),
    13: (20, 222, 80),
    14: (40, 225, 40),
    15: (75, 222, 20),
    16: (110, 220, 0),
    17: (185, 200, 0),
    18: (255, 180, 0),
    19: (255, 150, 0),
    20: (255, 120, 0),
    21: (255, 100, 0),
    22: (255, 80, 0),
    23: (255, 62, 0),
    24: (255, 45, 0),
    25: (248, 35, 0),
    26: (240, 25, 0),
    27: (225, 17, 0),
    28: (210, 10, 0),
    29: (190, 5, 0),
    30: (170, 0, 0),
}
OUT_OF_RANGE_COLOR = (0, 255, 183)


def add_toggle(parser, name, default, help_text):
    # --name / --no-name flag pair (argparse.BooleanOptionalAction needs 3.9+)
    dest = name.replace("-", "_")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--" + name, dest=dest, action="store_true",
                       help=help_text + (" (default)" if default else ""))
    group.add_argument("--no-" + name, dest=dest, action="store_false",
                       help="don't " + help_text + ("" if default else " (default)"))
    parser.set_defaults(**{dest: default})


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filename", default="SenseLog",
                        help="prefix for the CSV file (default: %(default)s)")
    parser.add_argument("--write-frequency", type=int, default=100,
                        help="rows to buffer before writing to disk (default: %(default)s)")
    parser.add_argument("--delay", type=float, default=5,
                        help="seconds between samples, 0 = as fast as possible (default: %(default)s)")
    add_toggle(parser, "temp-h", False, "log temperature from the humidity sensor")
    add_toggle(parser, "temp-p", True, "log temperature from the pressure sensor")
    add_toggle(parser, "humidity", True, "log relative humidity")
    add_toggle(parser, "pressure", True, "log air pressure")
    add_toggle(parser, "orientation", True, "log pitch/roll/yaw")
    add_toggle(parser, "mag", True, "log raw magnetometer x/y/z")
    add_toggle(parser, "accel", True, "log raw accelerometer x/y/z")
    add_toggle(parser, "gyro", True, "log raw gyroscope x/y/z")
    return parser.parse_args()


def build_header(args):
    header = []
    if args.temp_h:
        header.append("temp_h")
    if args.temp_p:
        header.append("temp_p")
    if args.humidity:
        header.append("humidity")
    if args.pressure:
        header.append("pressure")
    if args.orientation:
        header.extend(["pitch", "roll", "yaw"])
    if args.mag:
        header.extend(["mag_x", "mag_y", "mag_z"])
    if args.accel:
        header.extend(["accel_x", "accel_y", "accel_z"])
    if args.gyro:
        header.extend(["gyro_x", "gyro_y", "gyro_z"])
    header.append("timestamp")
    return header


def get_sense_data(sense, args):
    sense_data = []

    if args.temp_h:
        sense_data.append(sense.get_temperature_from_humidity())

    if args.temp_p:
        sense_data.append(sense.get_temperature_from_pressure())

    if args.humidity:
        sense_data.append(sense.get_humidity())

    if args.pressure:
        sense_data.append(sense.get_pressure())

    if args.orientation:
        o = sense.get_orientation()
        sense_data.extend([o["pitch"], o["roll"], o["yaw"]])

    if args.mag:
        mag = sense.get_compass_raw()
        sense_data.extend([mag["x"], mag["y"], mag["z"]])

    if args.accel:
        acc = sense.get_accelerometer_raw()
        sense_data.extend([acc["x"], acc["y"], acc["z"]])

    if args.gyro:
        gyro = sense.get_gyroscope_raw()
        sense_data.extend([gyro["x"], gyro["y"], gyro["z"]])

    sense_data.append(datetime.now().isoformat())

    return sense_data


def write_rows(filename, rows):
    with open(filename, "a", newline="") as f:
        csv.writer(f).writerows(rows)


def show_temp_history(sense, avg_temp):
    for i, value in enumerate(avg_temp):
        r, g, b = TEMP_COLORS.get(int(value), OUT_OF_RANGE_COLOR)
        x, y = divmod(i, 8)
        sense.set_pixel(x, y, r, g, b)


def blink(sense, r, g, b):
    for _ in range(2):
        sense.set_pixel(7, 7, r, g, b)
        sleep(0.25)
        sense.set_pixel(7, 7, 0, 0, 0)
        sleep(0.25)


def main():
    args = parse_args()
    temp_enabled = args.temp_h or args.temp_p

    sense = SenseHat()
    sense.clear()
    sense.low_light = True
    sense.show_message("Loading.........")
    blink(sense, 255, 0, 0)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = args.filename + "-" + timestamp + ".csv"
    with open(filename, "w", newline="") as f:
        csv.writer(f).writerow(build_header(args))

    if temp_enabled:
        startup_temp = (sense.get_temperature_from_humidity() if args.temp_h
                        else sense.get_temperature_from_pressure())
        sense.show_message(str(round(startup_temp, 1)))

    batch_data = []
    temp_batch = []
    avg_temp = []

    try:
        while True:
            row = get_sense_data(sense, args)
            batch_data.append(row)
            # temp_h/temp_p are always the first column when enabled
            if temp_enabled:
                temp_batch.append(row[0])

            if len(batch_data) >= args.write_frequency:
                blink(sense, 0, 255, 0)

                if temp_batch:
                    batch_avg = mean(temp_batch)
                    temp_batch = []
                    sense.show_message(str(round(batch_avg, 2)))
                    if len(avg_temp) >= 64:
                        avg_temp = []
                        sense.clear()
                    avg_temp.append(batch_avg)
                    show_temp_history(sense, avg_temp)

                write_rows(filename, batch_data)
                batch_data = []

            if args.delay > 0:
                sleep(args.delay)
    except KeyboardInterrupt:
        pass
    finally:
        # flush any rows still buffered so exiting doesn't lose them
        write_rows(filename, batch_data)
        sense.clear()


if __name__ == "__main__":
    main()
