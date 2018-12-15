from collections import namedtuple
from functools import partial
from random import randint

import pytest

from src.functions.skill import content
from src.functions.skill.models import Operation

# ducktaped SessionData structures
CountSessionData = namedtuple('CountSessionData', ['correct_answers_count',
                                                   'questions_count'])

QODSessionData = namedtuple('QODSessionData', ['questions_count',
                                               'operation',
                                               'difficulty'])


@pytest.fixture(params=['en-US'])
def locale(request):
    return request.param

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
    partial(content.incorrect, 4),
    partial(content.streak_encouragement, 20),
    partial(content.session_summary, CountSessionData(8, 4))
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

def test_training_question(operation, difficulty, locale):
    session_data = QODSessionData(randint(0, 5),
                                  operation,
                                  difficulty)
    question, result = content.training_question(session_data, locale)

    assert isinstance(question, str)
    assert isinstance(result, int)

def test_generate_operands(operation, difficulty):
    op1, op2 = content.generate_operands(operation, difficulty)

    assert isinstance(op1, int)
    assert isinstance(op2, int)

    if operation is Operation.SUB or operation is Operation.DIV:
        assert op1 >= op2

    if operation is Operation.DIV:
        assert op1 % op2 == 0
