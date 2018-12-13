import datetime
import enum
from typing import Optional

import attr
import dateutil.parser
import dateutil.tz


asdict = attr.asdict # for a cleaner interface

# How many seconds in between launch requests should a session be kept?
# If the period is greater, a new clean session should be launched,
# ignoring any old choices the user made.
STALE_SESSION_THRESHOLD = 15 * 60


class Operation(enum.Enum):
    ADD = 'add'
    SUB = 'sub'
    MUL = 'mul'
    DIV = 'div'

    @classmethod
    def from_word(cls, word, _locale=None):
        # no locale is used when building SessionData
        mapping = {'addition': cls.ADD,
                   'subtraction': cls.SUB,
                   'multiplication': cls.MUL,
                   'division': cls.DIV}
        return mapping[word]

    def __call__(self, op1, op2):
        cls = self.__class__
        mapping = {cls.ADD: op1 + op2,
                   cls.SUB: op1 - op2,
                   cls.MUL: op1 * op2,
                   cls.DIV: op1 / op2}
        return mapping[self]

    def as_verb(self, _locale):
        cls = self.__class__
        mapping = {cls.ADD: 'plus',
                   cls.SUB: 'minus',
                   cls.MUL: 'times',
                   cls.DIV: 'divided by'}
        return mapping[self]

    def as_symbol(self):
        cls = self.__class__
        mapping = {cls.ADD: '+',
                   cls.SUB: '-',
                   cls.MUL: '×',
                   cls.DIV: '÷'}
        return mapping[self]


@attr.s(auto_attribs=True)
class SessionData:
    # pylint: disable=too-few-public-methods,no-member

    operation: Optional[Operation] = attr.ib(
        default=None,
        converter=lambda a: Operation(a) if a else None)
    difficulty: Optional[int] = attr.ib(default=None)

    correct_result: int = attr.ib(default=0)
    questions_count: int = attr.ib(default=0)
    correct_answers_count: int = attr.ib(default=0)
    streak_count: int = attr.ib(default=0)

    @classmethod
    def from_attributes(cls, attributes):
        attributes = attributes or {}
        return cls(operation=attributes.get('operation'),
                   difficulty=attributes.get('difficulty'),
                   correct_result=attributes.get('correct_result', 0),
                   questions_count=attributes.get('questions_count', 0),
                   correct_answers_count=attributes.get('correct_answers_count', 0),
                   streak_count=attributes.get('streak_count', 0))


@attr.s(auto_attribs=True, kw_only=True)
class SkillUsage:
    # pylint: disable=no-member

    launch_count: int = attr.ib(default=0)
    previous_session_end: Optional[datetime.datetime] = attr.ib(
        default=None,
        converter=lambda a: dateutil.parser.parse(a) if a else None
    )
    session_data: Optional[SessionData] = attr.ib(default=None)

    @classmethod
    def from_attributes(cls, attributes):
        attributes = attributes or {}
        session_data = SessionData.from_attributes(
            attributes.get('session_data'))

        return cls(launch_count=attributes.get('launch_count', 0),
                   previous_session_end=attributes.get('previous_session_end'),
                   session_data=session_data)

    def is_new_session(self):
        if self.previous_session_end is None:
            return True

        if self.session_data.operation is None:
            # indicates a shutdown due to a user command, i.e.
            # a StopIntent or a CancelIntent, hence no need to
            # resum previous session
            return True

        now = datetime.datetime.now(tz=dateutil.tz.tzutc())
        ts_delta = now - self.previous_session_end
        return ts_delta.total_seconds() >= STALE_SESSION_THRESHOLD
