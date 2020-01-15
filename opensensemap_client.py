from datetime import datetime, timezone
from logging import Logger

import requests


class OpenSenseMapClient:
    def __init__(self, sensebox_id: str, temperature_sensor_id: str, humidity_sensor_id: str,
                 pressure_sensor_id: str, pm_1_0_sensor_id: str, pm_2_5_sensor_id: str, pm_10_sensor_id: str,
                 logger: Logger, buffer_size: int = 100) -> None:
        self.logger = logger
        self.buffer_size = buffer_size
        self.pm_10_sensor_id = pm_10_sensor_id
        self.pm_2_5_sensor_id = pm_2_5_sensor_id
        self.pm_1_0_sensor_id = pm_1_0_sensor_id
        self.pressure_sensor_id = pressure_sensor_id
        self.humidity_sensor_id = humidity_sensor_id
        self.temperature_sensor_id = temperature_sensor_id
        self.sensebox_id = sensebox_id
        self.values_buffer = []

    def map_values(self, values):
        opensensemap_messages = []
        for value in values:
            ts = value["ts"] / (1000 * 1000 * 1000)  # to seconds
            ts = datetime.utcfromtimestamp(ts).astimezone(timezone.utc).isoformat()
            opensensemap_messages.append(
                {"sensor": self.temperature_sensor_id, "value": value['temperature'], "createdAt": ts})
            opensensemap_messages.append(
                {"sensor": self.humidity_sensor_id, "value": value['humidity'], "createdAt": ts})
            opensensemap_messages.append(
                {"sensor": self.pressure_sensor_id, "value": value['pressure'], "createdAt": ts})
            opensensemap_messages.append({"sensor": self.pm_1_0_sensor_id, "value": value['P1.0'], "createdAt": ts})
            opensensemap_messages.append({"sensor": self.pm_2_5_sensor_id, "value": value['P2.5'], "createdAt": ts})
            opensensemap_messages.append({"sensor": self.pm_10_sensor_id, "value": value['P10'], "createdAt": ts})

        return opensensemap_messages

    def send_to_opensensemap(self, values):
        self.values_buffer.append(values)
        if len(self.values_buffer) >= self.buffer_size:
            self.logger.info("Sending data to OpenSenseMap")
            resp = requests.post("https://api.opensensemap.org/boxes/{}/data".format(self.sensebox_id),
                                 json=self.map_values(self.values_buffer),
                                 headers={
                                     "Content-Type": "application/json",
                                     "Connection": "close"
                                 })

            self.values_buffer = []
            self.logger.info("Sent data to OpenSenseMap, ok: {}".format(resp))
