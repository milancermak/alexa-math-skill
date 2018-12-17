import json


def load_log_events(caplog):
    return [json.loads(record[2]) for record in caplog.record_tuples]
