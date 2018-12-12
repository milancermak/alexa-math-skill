from ask_sdk_model import Response
import pytest

from src.functions.skill import utils
from .fixtures import handler_input # pylint: disable=unused-import


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
