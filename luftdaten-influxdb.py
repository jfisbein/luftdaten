#!/usr/bin/env python

import datetime
import logging
import time
from logging.handlers import MemoryHandler, TimedRotatingFileHandler
from subprocess import PIPE, Popen, check_output

import ST7735
import requests
import yaml
from PIL import Image, ImageDraw, ImageFont
from bme280 import BME280
from enviroplus import gas
from influxdb_client import InfluxDBClient
from pms5003 import PMS5003, ReadTimeoutError

try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559

    ltr559 = LTR559()
except ImportError:
    import ltr559

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

config = yaml.safe_load(open("config.yml"))

print("""luftdaten.py - Reads temperature, pressure, humidity,
PM2.5, and PM10 from Enviro plus and sends data to Luftdaten,
the citizen science air quality project.

Note: you'll need to register with Luftdaten at:
https://meine.luftdaten.info/ and enter your Raspberry Pi
serial number that's displayed on the Enviro plus LCD along
with the other details before the data appears on the
Luftdaten map.

Press Ctrl+C to exit!

""")

bus = SMBus(1)

# Create BME280 (temp, humidity and pressure sensor) instance
bme280 = BME280(i2c_dev=bus)

# Create LCD instance
disp = ST7735.ST7735(
    port=0,
    cs=ST7735.BG_SPI_CS_FRONT,
    dc=9,
    backlight=12,
    rotation=270,
    spi_speed_hz=10000000
)

# Initialize display
disp.begin()

# Create PMS5003 (air quality sensor) instance
pms5003 = PMS5003()

values_buffer = []


# Create logger
def get_logger(path):
    rotating_handler = TimedRotatingFileHandler(path, when='d', backupCount=7)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    rotating_handler.setFormatter(formatter)
    memory_handler = MemoryHandler(capacity=512 * 1024, target=rotating_handler)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger = logging.getLogger("luftdaten")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(memory_handler)
    logger.addHandler(console_handler)
    return logger


# Read values from BME280 and PMS5003 and return as dict
def read_values():
    values = {}
    cpu_temp = get_cpu_temperature()
    raw_temp = bme280.get_temperature()
    comp_temp = raw_temp - ((cpu_temp - raw_temp) / comp_factor)
    values["temperature"] = "{:.2f}".format(comp_temp)
    values["pressure"] = "{:.2f}".format(bme280.get_pressure() * 100)
    values["humidity"] = "{:.2f}".format(bme280.get_humidity())
    data = gas.read_all()
    values["oxidising"] = round(data.oxidising / 1000, 4)
    values["reducing"] = round(data.reducing / 1000, 4)
    values["nh3"] = round(data.nh3 / 1000, 4)
    values["lux"] = ltr559.get_lux()
    try:
        pm_values = pms5003.read()
        values["P2"] = str(pm_values.pm_ug_per_m3(2.5))
        values["P1"] = str(pm_values.pm_ug_per_m3(10))
        values["p1.0"] = str(pm_values.pm_ug_per_m3(1.0))
    except ReadTimeoutError:
        pms5003.reset()
        pm_values = pms5003.read()
        values["P2"] = str(pm_values.pm_ug_per_m3(2.5))
        values["P1"] = str(pm_values.pm_ug_per_m3(10))
        values["p1.0"] = str(pm_values.pm_ug_per_m3(1.0))

    values['ts'] = time.time()
    return values


# Get CPU temperature to use for compensation
def get_cpu_temperature():
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE, universal_newlines=True)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1:output.rindex("'")])


# Get Raspberry Pi serial number to use as ID
def get_serial_number():
    with open('/proc/cpuinfo', 'r') as f:
        for line in f:
            if line[0:6] == 'Serial':
                return line.split(":")[1].strip()


# Check for Wi-Fi connection
def check_wifi():
    if check_output(['hostname', '-I']):
        return True
    else:
        return False


# Display Last request date, last request status and Wi-Fi status on LCD
def display_status(status=''):
    wifi_status = "connected" if check_wifi() else "disconnected"
    text_colour = (255, 255, 255)
    ok_back_colour = (0, 0, 0)  # Black
    error_back_colour = (85, 15, 15)  # Red
    back_colour = ok_back_colour if check_wifi() else error_back_colour
    message = "{:%Y-%m-%d %H:%M:%S}\nLast update: {}\nWi-Fi: {}".format(datetime.datetime.now(), status, wifi_status)
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    size_x, size_y = draw.textsize(message, font)
    x = (WIDTH - size_x) / 2
    y = (HEIGHT / 2) - (size_y / 2)
    draw.rectangle((0, 0, 160, 80), back_colour)
    draw.text((x, y), message, font=font, fill=text_colour)
    disp.display(img)


def send_to_luftdaten(values, id):
    logger.debug('Sending info to luftdaten')
    pm_values = dict(i for i in values.items() if i[0].startswith("P"))
    temp_values = dict(i for i in values.items() if not i[0].startswith("P"))

    resp_1 = requests.post("https://api.luftdaten.info/v1/push-sensor-data/",
                           json={
                               "software_version": "enviro-plus 0.0.1",
                               "sensordatavalues": [{"value_type": key, "value": val} for
                                                    key, val in pm_values.items()]
                           },
                           headers={
                               "X-PIN": "1",
                               "X-Sensor": id,
                               "Content-Type": "application/json",
                               "cache-control": "no-cache"
                           }
                           )

    resp_2 = requests.post("https://api.luftdaten.info/v1/push-sensor-data/",
                           json={
                               "software_version": "enviro-plus 0.0.1",
                               "sensordatavalues": [{"value_type": key, "value": val} for
                                                    key, val in temp_values.items()]
                           },
                           headers={
                               "X-PIN": "11",
                               "X-Sensor": id,
                               "Content-Type": "application/json",
                               "cache-control": "no-cache"
                           }
                           )

    if resp_1.ok and resp_2.ok:
        return True
    else:
        return False


def map_to_influxDB(values):
    influxDbMessages = []
    for value in values:
        influxDbMessages.append("weather,location=acacias temperature={} {}".format(value['temperature'], round(value['ts'])))
        influxDbMessages.append("weather,location=acacias humidity={} {}".format(value['humidity'], round(value['ts'])))
        influxDbMessages.append("weather,location=acacias pressure={} {}".format(value['pressure'], round(value['ts'])))
        influxDbMessages.append("particles,location=acacias P25={} {}".format(value['P2'], round(value['ts'])))
        influxDbMessages.append("particles,location=acacias P10={} {}".format(value['P1'], round(value['ts'])))

    return influxDbMessages


def send_to_influxDB(values):
    global values_buffer
    values_buffer.append(values)
    if len(values_buffer) > 100:
        logger.info("Sending data to influxDB")
        client = InfluxDBClient(url=config['influxdb']['url'], token=config['influxdb']['token'], enable_gzip=True)
        client.write('bucketID', config['influxdb']['bucket'], map_to_influxDB(values_buffer))
        values_buffer = []


# Compensation factor for temperature
comp_factor = 1.2

# Raspberry Pi ID to send to Luftdaten
id = "raspi-" + get_serial_number()

# Logger
logger = get_logger('/var/log/luftdaten.log')

# Width and height to calculate text position
WIDTH = disp.width
HEIGHT = disp.height

# Text settings
font_size = 16
font = ImageFont.truetype("fonts/Asap/Asap-Bold.ttf", font_size)

# Display Raspberry Pi serial and Wi-Fi status
logger.info("Raspberry Pi serial: {}".format(get_serial_number()))
logger.info("Wi-Fi: {}\n".format("connected" if check_wifi() else "disconnected"))

time_since_update = 0
update_time = time.time()

display_status('waiting')

# Main loop to read data, display, and send to Luftdaten
while True:
    try:
        time_since_update = time.time() - update_time
        values = read_values()
        logger.debug(values)
        send_to_influxDB(values)
        if time_since_update > 145:
            resp = send_to_luftdaten(values, id)
            response = "ok" if resp else "failed"
            update_time = time.time()
            logger.info("Response: {}".format(response))
            display_status(response)
    except KeyboardInterrupt:
        disp.set_backlight(0)
        raise
    except Exception as e:
        logger.exception(e)
