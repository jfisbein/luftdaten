from logging import Logger

from influxdb import InfluxDBClient


class InfluxDbWeather:
    def __init__(self, host: str, port: int, database: str, username: str, password: str, logger: Logger, buffer_size: int = 100) -> object:
        self.values_buffer = []
        self.client = InfluxDBClient(host=host, port=port, database=database, username=username, password=password)
        self.buffer_size = buffer_size
        self.logger = logger

    @staticmethod
    def map_to_influxdb(values):
        influxdb_messages = []
        for value in values:
            influxdb_messages.append("weather,location=acacias temperature={},humidity={},pressure={} {}"
                                     .format(value['temperature'], value['humidity'], value['pressure'], value['ts']))
            influxdb_messages.append("particles,location=acacias P25={},P10={},P1={} {}"
                                     .format(value['P2.5'], value['P10'], value['P1.0'], value['ts']))
            influxdb_messages.append("gas,location=acacias oxidising={},reducing={},nh3={} {}"
                                     .format(value['oxidising'], value['reducing'], value['nh3'], value['ts']))

        return influxdb_messages

    def send_to_influxdb(self, values):
        self.values_buffer.append(values)
        if len(self.values_buffer) >= self.buffer_size:
            self.logger.info("Sending data to influxDB")
            self.client.write_points(points=self.map_to_influxdb(self.values_buffer), protocol='line')
            self.values_buffer = []
