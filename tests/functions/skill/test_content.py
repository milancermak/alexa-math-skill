from collections import namedtuple
from functools import partial
from random import randint

import pytest

from ask_sdk_model.interfaces.alexa.presentation.apl import \
    RenderDocumentDirective
from src.functions.skill import content
from src.functions.skill.models import Operation, SkillUsage
from .fixtures import locale # pylint: disable=unused-import

# ducktaped SessionData structures
CountSessionData = namedtuple('CountSessionData', ['correct_answers_count',
                                                   'questions_count'])

QODSessionData = namedtuple('QODSessionData', ['questions_count',
                                               'operation',
                                               'difficulty'])

@pytest.fixture(params=[Operation.ADD,
                        Operation.SUB,
                        Operation.MUL,
                        Operation.DIV])
def operation(request):
    return request.param

@pytest.fixture(params=list(range(1, 6)))
def difficulty(request):
    return request.param

@pytest.mark.parametrize('difficulty_str, expected', [
    ('easy', 1),
    ('normal', 2),
    ('hard', 3),
    ('difficult', 3),
    ('any', 2)
])
def test_difficulty_to_value(difficulty_str, expected, locale):
    assert content.difficulty_to_value(difficulty_str, locale) == expected

@pytest.mark.parametrize('fn', [
    content.help_message,
    content.start_message,
    content.prompt_for_difficulty,
    content.prompt_for_operation,
    content.dead_end_message,
    partial(content.incorrect, 4),
    partial(content.streak_encouragement, 20),
    partial(content.session_summary, CountSessionData(8, 4)),
    partial(content.intro_message, 0),
    partial(content.intro_message, 1),
])
def test_for_string_value_single(fn, locale):
    assert isinstance(fn(locale), str)

@pytest.mark.parametrize('fn', [
    content.confirmation,
    content.congratulations,
    content.correct,
    partial(content.streak_confirmation, 10)
])
def test_for_string_value_in_randomized(fn, locale):
    results_set = set()
    for _ in range(50):
        results_set.add(fn(locale))

    assert all([isinstance(result, str) for result in results_set])

@pytest.mark.parametrize('questions_count', [0, 1])
def test_build_question(questions_count, locale):
    attributes = {'launch_count': 4,
                  'previous_session_end': 15000000,
                  'session_data': {
                      'operation': 'mul',
                      'difficulty': 3,
                      'questions_count': questions_count
                  }}
    usage = SkillUsage.from_attributes(attributes)

    question, result, apl = content.build_question(usage, locale)

    assert isinstance(question, str)
    assert isinstance(result, int)
    assert isinstance(apl, RenderDocumentDirective)


def test_training_question(operation, difficulty, locale):
    session_data = QODSessionData(randint(0, 5),
                                  operation,
                                  difficulty)
    question = content.training_question(randint(1, 100),
                                         randint(1, 100),
                                         session_data,
                                         locale)
    assert isinstance(question, str)

def test_generate_ops(operation, difficulty):
    op1, op2, result = content.generate_ops(operation, difficulty)

    assert isinstance(op1, int)
    assert isinstance(op2, int)
    assert isinstance(result, int)

    if operation is Operation.SUB or operation is Operation.DIV:
        assert op1 >= op2

    if operation is Operation.DIV:
        assert op1 % op2 == 0
