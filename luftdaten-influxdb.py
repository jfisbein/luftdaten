#!/usr/bin/env python

import logging
import time
from logging.handlers import MemoryHandler, TimedRotatingFileHandler
from subprocess import check_output

import yaml
from PIL import ImageFont

import enviroplus_lcd
import enviroplus_reader
import influxdb_local_weather_client
import luftdaten_client

config = yaml.safe_load(open("config.yml"))

print("""luftdaten-influxdb.py - Reads temperature, pressure, humidity,
PM 1.0, PM2.5, and PM10 from Enviro plus and sends data to InfluxDB and Luftdaten,
the citizen science air quality project.

Note: you'll need to register with Luftdaten at:
https://meine.luftdaten.info/ and enter your Raspberry Pi
serial number that's displayed on the Enviro plus LCD along
with the other details before the data appears on the
Luftdaten map.

Press Ctrl+C to exit!

""")


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


# Raspberry Pi ID to send to Luftdaten
id = "raspi-" + get_serial_number()

# Logger
logger = get_logger('/var/log/luftdaten.log')

# Text settings
font_size = 16
font = ImageFont.truetype("fonts/Asap/Asap-Bold.ttf", font_size)

# Display Raspberry Pi serial and Wi-Fi status
logger.info("Raspberry Pi serial: {}".format(get_serial_number()))
logger.info(
  "Wi-Fi: {}\n".format('connected' if check_wifi() else 'disconnected'))

time_since_update = 0
update_time = time.time()

influxdb_cfg = config['influxdb']
reader = enviroplus_reader.EnviroPlusReader()
luftdaten_client = luftdaten_client.LuftdatenClient(id)

influxdb_weather = influxdb_local_weather_client.InfluxDbWeather(
    influxdb_cfg['host'], influxdb_cfg['port'], influxdb_cfg['database'],
    influxdb_cfg['username'], influxdb_cfg['password'], logger)
enviroplus_lcd = enviroplus_lcd.EnviroplusLCD(font)

wifi_status = 'connected' if check_wifi() else 'disconnected'
enviroplus_lcd.display_status(wifi_status, 'waiting')
# Main loop to read data, display, and send to Luftdaten
while True:
  try:
    time_since_update = time.time() - update_time
    values = reader.read_values()
    logger.debug(values)
    influxdb_weather.send_to_influxdb(values)
    if time_since_update > 120:
      wifi_status = 'connected' if check_wifi() else 'disconnected'
      resp = luftdaten_client.send_to_luftdaten(values)
      response = 'ok' if resp else 'failed'
      update_time = time.time()
      logger.info("Response: {}".format(response))
      enviroplus_lcd.display_status(wifi_status, response)
  except KeyboardInterrupt:
    enviroplus_lcd.turnoff()
    raise
  except Exception as e:
    logger.exception(e)
