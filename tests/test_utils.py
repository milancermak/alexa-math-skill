import json

import jmespath


def assert_keypath(path, data, value):
    assert jmespath.search(path, data) == value

def load_log_events(caplog):
    return [json.loads(record[2]) for record in caplog.record_tuples]
