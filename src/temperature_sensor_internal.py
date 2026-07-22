import os
import sys
import glob
import time
import base64
from datetime import datetime
import urllib.request
from urllib.parse import urlencode
import logging

# Configure logging dynamically from environment
log_level_str = os.environ.get("SENSOR_LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Initialize 1-wire drivers
logging.info("Initializing 1-wire drivers...")
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# Allow base directory override for testing/dev environments
base_dir = os.environ.get("SENSOR_BASE_DIR", '/sys/bus/w1/devices/')
device_id = os.environ.get("SENSOR_DEVICE_ID", "28-000005a99b38")
device_name = os.environ.get("SENSOR_DEVICE_NAME", "Surface")

# Safely check for the device directory
device_folders = glob.glob(os.path.join(base_dir, device_id))
if not device_folders:
    logging.error(f"Device folder for '{device_id}' not found under '{base_dir}'. "
                  "Please check your sensor connection, base directory, or 1-wire drivers.")
    sys.exit(1)

device_folder = device_folders[0]
device_file = os.path.join(device_folder, 'w1_slave')

base_url = os.environ.get("SENSOR_DATA_URL", "http://ec2-54-229-82-10.eu-west-1.compute.amazonaws.com")

try:
    read_interval = float(os.environ.get("SENSOR_READ_INTERVAL", "360"))
except ValueError:
    logging.warning("Invalid SENSOR_READ_INTERVAL value. Defaulting to 360 seconds.")
    read_interval = 360.0


def read_temp_raw():
    try:
        with open(device_file, 'r') as f:
            return f.readlines()
    except Exception as e:
        logging.error(f"Failed to read device file: {e}")
        return []


def read_temp():
    lines = read_temp_raw()
    if not lines or len(lines) < 2:
        logging.warning("Sensor data is empty or unavailable.")
        return None

    # Wait for sensor to be ready (YES at the end of the first line)
    attempts = 0
    max_attempts = 10
    while lines[0].strip()[-3:] != 'YES':
        attempts += 1
        if attempts >= max_attempts:
            logging.warning("Sensor did not return success status 'YES' after multiple attempts.")
            return None
        time.sleep(0.2)
        lines = read_temp_raw()
        if not lines or len(lines) < 2:
            return None

    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        try:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
        except ValueError as e:
            logging.error(f"Failed to parse temperature string: {e}")
            return None

        currenttime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        params = {
            'id': device_id,
            'name': device_name,
            'date': currenttime,
            'tempC': temp_c,
            'tempF': temp_f
        }
        logging.info(f"Sending parameters: {params}")
        write_temp(params)
        return temp_c, temp_f, device_id, device_name, currenttime

    logging.warning("Temperature token 't=' not found in sensor output.")
    return None


def write_temp(params):
    target_url = base_url.rstrip('/') + '/sensordata/create?' + urlencode(params)
    logging.info(f"URL Command: {target_url}")

    req = urllib.request.Request(target_url)
    req.add_header('Accept', 'application/json')
    req.add_header('Content-Type', 'application/json')

    # Resolve authorization credentials
    auth_user = os.environ.get("SENSOR_AUTH_USER")
    auth_pass = os.environ.get("SENSOR_AUTH_PASSWORD")
    if auth_user and auth_pass:
        auth_str = f"{auth_user}:{auth_pass}"
        auth_b64 = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
        req.add_header('Authorization', f'Basic {auth_b64}')
    else:
        # Fallback to default hardcoded credentials (user:password)
        req.add_header('Authorization', 'Basic dXNlcjpwYXNzd29yZA==')

    max_retries = 3
    retry_delay = 5
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                response_code = response.getcode()
                logging.info(f"Response Code: {response_code}")
                return  # Success, exit function
        except Exception as e:
            logging.warning(f"Attempt {attempt}/{max_retries} failed to send request: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                logging.error("All retry attempts failed.")


# Main Loop
logging.info("Starting temperature sensor service. Press Ctrl+C to stop.")
try:
    while True:
        try:
            read_temp()
        except Exception as e:
            logging.error(f"Error reading temperature: {e}")
        time.sleep(read_interval)
except KeyboardInterrupt:
    logging.info("Shutdown requested by user. Exiting temperature sensor service.")
    sys.exit(0)
