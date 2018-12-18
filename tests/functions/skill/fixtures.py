import json
import os
from string import Template
from unittest.mock import Mock

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.serialize import DefaultSerializer
from ask_sdk_model import RequestEnvelope
import pytest


serializer = DefaultSerializer()


@pytest.fixture
def dynamodb_client():
    # pylint: disable=invalid-name
    item_storage = {}

    def get_item(Key=None, **_kwargs):
        item_key = Key['id']
        if item_key in item_storage:
            return {'Item': {'attributes': item_storage[item_key]}}
        return {}

    def put_item(Item=None):
        item_key = Item['id']
        item_value = Item['attributes']
        item_storage[item_key] = item_value

    table_mock = Mock(get_item=get_item, put_item=put_item)
    mock_client = Mock()
    mock_client.Table.return_value = table_mock

    return mock_client

def load_event(event_name, as_json=True) -> dict:
    here = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(here, 'events', f'{event_name}.json')
    with open(path) as f:
        if as_json:
            return json.load(f)
        return f.read()

def build_intent_event(intent_name) -> dict:
    here = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(here, 'events', 'intent_template.json')
    with open(path) as f:
        mold = Template(f.read())
        product = mold.substitute(intent_name=intent_name)
        return json.loads(product)

@pytest.fixture
def launch_request() -> dict:
    return load_event('launch_request')

@pytest.fixture
def session_ended_request() -> dict:
    return load_event('session_ended_request')

@pytest.fixture
def did_select_operation_intent() -> dict:
    return load_event('did_select_operation')

@pytest.fixture
def did_select_difficulty_intent() -> dict:
    return load_event('did_select_difficulty')

@pytest.fixture
def did_answer_intent_correct() -> dict:
    return load_event('did_answer_correct')

@pytest.fixture
def did_answer_intent_wrong() -> dict:
    return load_event('did_answer_wrong')

@pytest.fixture
def unhandled_intent() -> dict:
    return load_event('unhandled_intent')

@pytest.fixture(params=['launch_request',
                        'session_ended_request',
                        'did_select_operation',
                        'did_select_difficulty',
                        'did_answer_correct',
                        'did_answer_wrong'])
def handler_input(request) -> HandlerInput:
    event_name = request.param
    event = load_event(event_name, as_json=False)
    request_envelope = serializer.deserialize(event, RequestEnvelope)
    return HandlerInput(request_envelope)

@pytest.fixture(params=['en-US'])
def locale(request) -> str:
    return request.param
