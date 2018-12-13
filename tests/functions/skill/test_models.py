# pylint: disable=no-self-use,no-member

import datetime

from dateutil.tz import tzutc
import pytest

from src.functions.skill import models


class TestOperation:

    def test_creation_from_word(self):
        # pylint: disable=invalid-name
        Op = models.Operation
        assert Op.from_word('addition') == Op.ADD
        assert Op.from_word('subtraction') == Op.SUB
        assert Op.from_word('multiplication') == Op.MUL
        assert Op.from_word('division') == Op.DIV

    def test_calling(self):
        Op = models.Operation
        assert Op.ADD(7, 3) == 10
        assert Op.SUB(7, 3) == 4
        assert Op.MUL(7, 3) == 21
        assert Op.DIV(21, 3) == 7

    def test_as_verb(self):
        Op = models.Operation
        locale = 'en-US'
        assert Op.ADD.as_verb(locale) == 'plus'
        assert Op.SUB.as_verb(locale) == 'minus'
        assert Op.MUL.as_verb(locale) == 'times'
        assert Op.DIV.as_verb(locale) == 'divided by'

    def test_as_symbol(self):
        Op = models.Operation
        assert Op.ADD.as_symbol() == '+'
        assert Op.SUB.as_symbol() == '-'
        assert Op.MUL.as_symbol() == '×'
        assert Op.DIV.as_symbol() == '÷'


class TestSessionData:

    def test_creation_from_partial_attributes(self):
        attributes = {'operation': 'add',
                      'difficulty': 3}
        session_data = models.SessionData.from_attributes(attributes)

        assert session_data.operation == models.Operation.ADD
        assert session_data.difficulty == 3
        assert session_data.correct_result == 0
        assert session_data.questions_count == 0
        assert session_data.correct_answers_count == 0
        assert session_data.streak_count == 0

    def test_creation_from_all_attributes(self):
        attributes = {'operation': 'div',
                      'difficulty': 2,
                      'correct_result': 8,
                      'questions_count': 20,
                      'correct_answers_count': 19,
                      'streak_count': 17}
        session_data = models.SessionData.from_attributes(attributes)
        assert session_data.operation == models.Operation.DIV
        assert session_data.difficulty == 2
        assert session_data.correct_result == 8
        assert session_data.questions_count == 20
        assert session_data.correct_answers_count == 19
        assert session_data.streak_count == 17

    def test_creation_no_attributes(self):
        session_data = models.SessionData.from_attributes(None)

        assert session_data.operation is None
        assert session_data.difficulty is None
        assert session_data.correct_result == 0
        assert session_data.questions_count == 0
        assert session_data.correct_answers_count == 0
        assert session_data.streak_count == 0


class TestSkillUsage:

    def test_creation_from_attributes(self):
        attributes = {'previous_session_end': '2018-10-11T12:00:00Z',
                      'session_data': {'operation': 'mul',
                                       'difficulty': 1},
                      'launch_count': 4}
        end_dt = datetime.datetime(2018, 10, 11, 12, 0, 0, tzinfo=tzutc())
        skill_usage = models.SkillUsage.from_attributes(attributes)

        assert skill_usage.launch_count == 4
        assert skill_usage.previous_session_end == end_dt
        assert skill_usage.session_data is not None
        assert skill_usage.session_data.operation == models.Operation.MUL
        assert skill_usage.session_data.difficulty == 1

    def test_creation_no_attributes(self):
        skill_usage = models.SkillUsage.from_attributes(None)

        assert skill_usage.launch_count == 0
        assert skill_usage.previous_session_end is None
        assert skill_usage.session_data is not None

    @pytest.mark.parametrize('attributes, expected', [
        (None, True),
        ({'session_data': {},
          'previous_session_end': '2010-01-01T02:00:00Z'}, True),
        ({'session_data': {'operation': 'sub'},
          'previous_session_end':
          datetime.datetime.now(tz=tzutc()).isoformat(timespec='seconds')},
         False),
        ({'session_data': {'operation': 'div'},
          'previous_session_end':
          (datetime.datetime.now(tz=tzutc()) - datetime.timedelta(days=1))\
          .isoformat(timespec='seconds')},
         True)
    ])
    def test_is_new_session(self, attributes, expected):
        skill_usage = models.SkillUsage.from_attributes(attributes)

        assert skill_usage.is_new_session() == expected
