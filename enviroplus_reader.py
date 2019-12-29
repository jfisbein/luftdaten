import time
from subprocess import PIPE, Popen

from bme280 import BME280
from enviroplus import gas
from pms5003 import PMS5003, ReadTimeoutError

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559

    ltr559 = LTR559()
except ImportError:
    import ltr559


class EnviroPlusReader:
    def __init__(self, comp_factor: float = 1.2) -> object:
        self.bus = SMBus(1)

        # Create BME280 (temp, humidity and pressure sensor) instance
        self.bme280 = BME280(i2c_dev=self.bus)

        # Create PMS5003 dust sensor instance
        self.pms5003 = PMS5003()
        self.comp_factor = comp_factor

    def read_values(self):
        values = {}
        cpu_temp = self.get_cpu_temperature()
        raw_temp = self.bme280.get_temperature()
        comp_temp = raw_temp - ((cpu_temp - raw_temp) / self.comp_factor)
        values['temperature'] = round(comp_temp, 2)
        values['pressure'] = round(self.bme280.get_pressure(), 2)
        values['humidity'] = round(self.bme280.get_humidity(), 2)
        data = gas.read_all()
        values['oxidising'] = round(data.oxidising / 1000, 4)
        values['reducing'] = round(data.reducing / 1000, 4)
        values['nh3'] = round(data.nh3 / 1000, 4)
        values['lux'] = round(ltr559.get_lux(), 2)
        try:
            pm_values = self.pms5003.read()
            values['P2.5'] = pm_values.pm_ug_per_m3(2.5)
            values['P10'] = pm_values.pm_ug_per_m3(10)
            values['P1.0'] = pm_values.pm_ug_per_m3(1.0)
        except ReadTimeoutError:
            self.pms5003.reset()
            pm_values = self.pms5003.read()
            values['P2.5'] = pm_values.pm_ug_per_m3(2.5)
            values['P10'] = pm_values.pm_ug_per_m3(10)
            values['P1.0'] = pm_values.pm_ug_per_m3(1.0)

        values['ts'] = time.time_ns()
        return values

    @staticmethod
    def get_cpu_temperature():
        process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE, universal_newlines=True)
        output, _error = process.communicate()
        return float(output[output.index('=') + 1:output.rindex("'")])
