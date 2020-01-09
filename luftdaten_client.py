import requests


class LuftdatenClient:
    def __init__(self, sensor_id: str) -> None:
        self.sensor_id = sensor_id

    def send_to_luftdaten(self, values) -> bool:
        resp_1 = requests.post("https://api.luftdaten.info/v1/push-sensor-data/",
                               json={
                                   "software_version": "enviro-plus 0.0.1",
                                   "sensordatavalues": [
                                       {'value_type': 'P1', 'value': str(values['P10'])},
                                       {'value_type': 'P2', 'value': str(values['P2.5'])}
                                   ]
                               },
                               headers={
                                   "X-PIN": "1",
                                   "X-Sensor": self.sensor_id,
                                   "Content-Type": "application/json",
                                   "cache-control": "no-cache"
                               }
                               )

        resp_2 = requests.post("https://api.luftdaten.info/v1/push-sensor-data/",
                               json={
                                   'software_version': '"enviro-plus 0.0.1',
                                   'sensordatavalues': [
                                       {'value_type': 'temperature', 'value': str(values['temperature'])},
                                       {'value_type': 'humidity', 'value': str(values['humidity'])},
                                       {'value_type': 'pressure', 'value': str(values['pressure'])}
                                   ]
                               },
                               headers={
                                   "X-PIN": "11",
                                   "X-Sensor": self.sensor_id,
                                   "Content-Type": "application/json",
                                   "cache-control": "no-cache"
                               }
                               )

        if resp_1.ok and resp_2.ok:
            return True
        else:
            return False
