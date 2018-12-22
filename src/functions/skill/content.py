import math
import random

from ask_sdk_model.interfaces.alexa.presentation.apl import \
    RenderDocumentDirective

from models import Operation
import utils


@utils.randomize
def confirmation(_locale):
    return ['OK.', 'Alright.', 'Got it.'] # add some speechcons? gotcha?

@utils.randomize
def congratulations(_locale):
    return ['Yay!', 'Great job.', 'Hooray.'] # speechcons

@utils.randomize
def correct(_locale):
    return ['Yes.', 'Indeed.', 'You\'ve got that right.', 'Correct.']

def incorrect(result, _locale):
    return f'The correct result is {result}. Try another one.'

@utils.randomize
def streak_confirmation(streak_count, _locale):
    return [f'That\'s {streak_count} correct answers in a row. Keep going.',
            f'You got {streak_count} right answers in a row.',
            f'You\'re on a streak! {streak_count} so far. Can you do more?']

def streak_encouragement(streak_count, _locale):
    return utils.combine_messages(congratulations(_locale),
                                  streak_confirmation(streak_count, _locale))

def dead_end_message(_locale):
    # pylint: disable=line-too-long
    return 'Sorry, I don\'t understand that. Let\'s try from the beginning. What would you like to train? Addition, subtraction, multiplication, or division?'

def help_message(_locale):
    # pylint: disable=line-too-long
    return 'This skill helps you practice your math arithmetics. Simply choose the operation you want to practice and a difficulty level. Alexa will then keep on giving you math exercises until you tell her to stop. So what would you like to train? Addition, subtraction, multiplication, or division?'

def intro_message(launch_count, _locale):
    # pulint: disable=line-too-long
    if launch_count == 0:
        return 'Hello and welcome to match practice. This skill helps you to get great in basic math arithmetics by you training exercise to solve.'
    return 'Welcome back to math practice.'

def start_message(_locale):
    return 'Let\'s get started'

def session_summary(session_data, _locale):
    return f'You\'ve got {session_data.correct_answers_count} out of {session_data.questions_count} correct. Talk to you soon!'

# prompts

def prompt_for_difficulty(_locale):
    # should work as a reprompt
    return 'Choose your difficulty level. Easy, normal, or hard?'

def prompt_for_operation(_locale):
    # should work as a reprompt
    return 'What would you like to train? Addition, subtraction, multiplication, or division?'

# training

def build_question(usage, locale):
    op1, op2, result = generate_ops(usage.session_data.operation,
                                    usage.session_data.difficulty)
    question = training_question(op1, op2, usage.session_data, locale)
    apl_data = {
        'data': {
            'type': 'object',
            'properties': {
                'op1': op1,
                'op2': op2,
                'operand': usage.session_data.operation.as_symbol()
            }
        }
    }

    apl = RenderDocumentDirective(document=apl_document(),
                                  datasources=apl_data)

    return question, result, apl

def training_question(op1, op2, session_data, _locale):
    if session_data.questions_count == 0:
        lead = 'What is'
    else:
        lead = random.choice(['What is', '', 'How about', 'And'])

    return f'{lead} {op1} {session_data.operation.as_verb(_locale)} {op2}?'

def generate_ops(operation, difficulty):
    # pylint: disable=invalid-name
    add_sub_limits = {
        1: (10, 10),
        2: (50, 50),
        3: (100, 100),
        4: (1000, 100),
        5: (1000, 1000)
    }
    mul_div_limits = {
        1: (10, 10),
        2: (30, 30),
        3: (50, 50),
        4: (100, 50),
        5: (1000, 100)
    }

    # using "is" to compare the enums does not work when running tests (??)

    if operation.value in [Operation.ADD.value, Operation.SUB.value]:
        op1_max, op2_max = add_sub_limits[difficulty]
    else:
        op1_max, op2_max = mul_div_limits[difficulty]

    op1 = random.randint(1, op1_max)
    op2 = random.randint(1, op2_max)

    if (operation.value in [Operation.SUB.value, Operation.DIV.value] and
        op1 < op2): # pylint: disable=bad-continuation
        # prevent "unwanted" results
        op1, op2 = op2, op1

    if operation.value == Operation.DIV.value and op1 % op2 != 0:
        # assure round results of division
        op1 = math.ceil(op1 / op2) * op2

    return op1, op2, operation(op1, op2)

def difficulty_to_value(spoken_difficulty, _locale):
    # pylint: disable=no-else-return
    if spoken_difficulty == 'easy':
        return 1
    elif spoken_difficulty == 'normal':
        return 2
    elif spoken_difficulty in ['hard', 'difficult']:
        return 3
    else:
        return 2

def apl_document():
    # py version of apl_document.json
    return \
    {'type': 'APL',
     'version': '1.0',
     'import': [{'name': 'alexa-styles', 'version': '1.0.0'},
                {'name': 'alexa-viewport-profiles', 'version': '1.0.0'}],
     'mainTemplate': {
         'parameters': ['payload'],
         'item':
             {'type': 'Container',
              'alignItems': 'center',
              'justifyContent': 'center',
              'height': '100vh',
              'width': '100vw',
              'items': [
                  {'type': 'Text',
                   'fontSize': '${@viewportProfile == @hubRoundSmall ? @fontSizeLarge : @fontSizeXXLarge}',
                   'fontWeight': '@fontWeightLight',
                   'text': '${payload.data.properties.op1} ${payload.data.properties.operand} ${payload.data.properties.op2}'}]}}}
