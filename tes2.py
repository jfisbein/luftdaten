from datetime import datetime, timezone


def ts_to_rfc3339(ts_in_nanos):
    ts_in_seconds = ts_in_nanos / (1000 * 1000 * 1000)
    ts = datetime.utcfromtimestamp(ts_in_seconds).astimezone(timezone.utc).isoformat()
    ts = ts.replace('+00:00', 'Z')

    return ts


print(ts_to_rfc3339(1579094549584333171))
