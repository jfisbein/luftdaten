import logging
import random as rnd
import time

import opensensemap_client

logger = logging.getLogger("test")
client = opensensemap_client.OpenSenseMapClient("5e1f03cdb459b2001ed44264", "5e1f03cdb459b2001ed4426a",
                                                "5e1f03cdb459b2001ed44269", "5e1f03cdb459b2001ed44268",
                                                "5e1f03cdb459b2001ed44265", "5e1f03cdb459b2001ed44267",
                                                "5e1f03cdb459b2001ed44266", logger, 10)

while True:
    try:
        values = {}
        values['temperature'] = rnd.randint(-10, 50)
        values['pressure'] = rnd.randint(900, 1000)
        values['humidity'] = rnd.randint(20, 100)
        values['P1.0'] = rnd.randint(20, 100)
        values['P2.5'] = rnd.randint(20, 100)
        values['P10'] = rnd.randint(20, 100)
        values['ts'] = time.time() * 1000 * 1000 * 1000
        client.send_to_opensensemap(values)
        time.sleep(5)
    except Exception as e:
        logger.exception(e)
        raise e
