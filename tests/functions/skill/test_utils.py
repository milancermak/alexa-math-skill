import json

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import RequestEnvelope, Response
import pytest

from src.functions.skill import utils
from .fixtures import handler_input, load_event, serializer # pylint: disable=unused-import


def test_build_response(handler_input):
    response = utils.build_response(handler_input, 'same same')
    assert isinstance(response, Response)
    assert response.output_speech.ssml == '<speak>same same</speak>'
    assert response.reprompt.output_speech.ssml == '<speak>same same</speak>'

    response = utils.build_response(handler_input, 'same same', 'but different')
    assert isinstance(response, Response)
    assert response.output_speech.ssml == '<speak>same same</speak>'
    assert response.reprompt.output_speech.ssml == '<speak>but different</speak>'

@pytest.mark.parametrize('messages, expected', [
    (('hi', 'there'), 'hi. there.'),
    (('working?', 'yes'), 'working? yes.'),
    (('jump!', 'jump', 'jump!'), 'jump! jump. jump!'),
    (('que¿', 'nada'), 'que¿ nada.'),
    (('que¡', 'nada'), 'que¡ nada.')
])
def test_combine_messages(messages, expected):
    assert utils.combine_messages(*messages) == expected

def test_randomize():
    @utils.randomize
    def five():
        return list(range(5))

    values = set()
    for _ in range(100):
        values.add(five())

    assert len(values) == 5

def test_speechcon():
    expected = '<say-as interpret-as="interjection">boom</say-as>'
    assert utils.speechcon('boom') == expected

@pytest.mark.parametrize('event_name, has_support', [
    ('launch_request', False),
    ('session_ended_request', False),
    ('did_select_operation', False),
    ('did_select_difficulty', True),
    ('did_answer_correct', True),
    ('did_answer_wrong', True)
])
def test_has_apl_support(event_name, has_support):
    envelope_dict = load_event(event_name)
    request_envelope = serializer.deserialize(json.dumps(envelope_dict),
                                              RequestEnvelope)
    hi = HandlerInput(request_envelope)
    assert utils.has_apl_support(hi) == has_support
