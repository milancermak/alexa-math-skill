import math
import random

from models import Operation
import utils


# TODO: write tests for this module


@utils.randomize
def confirmation(_locale):
    return ['OK.', 'Alright.', 'Got it.'] # add some speechcons? gotcha?

@utils.randomize
def congratulations(_locale):
    return ['Yay!', 'Great job.', 'Hooray.'] # speechcons

@utils.randomize
def correct(_locale):
    return ['Yes.', 'Indeed.', 'You\'ve got that right.', 'Correct.']

def incorrect(_locale, result):
    return f'The correct result is {result}. Try another one.'

@utils.randomize
def streak_confirmation(_locale, streak_count):
    return [f'That\'s {streak_count} correct answers in a row. Keep going.',
            f'You got {streak_count} right answers in a row.',
            f'You\'re on a streak! {streak_count} so far. Can you do more?']

def streak_encouragement(_locale, streak_count):
    return utils.combine_messages(congratulations(_locale),
                                  streak_confirmation(_locale, streak_count))

def help_message(_locale):
    # pylint: disable=line-too-long
    return 'This skill helps you practice your math arithmetics. Simply choose the operation you want to practice, either addition, subtraction, multiplication or division and one of the easy, normal or hard difficulty levels. Alexa will then keep on giving you math exercises until you tell her to stop. So what would you like to train? Addition, subtraction, multiplication, or division?'

def start_message(_locale):
    return 'Let\'s get started'

def session_summary(_locale, session_data):
    return f'You\'ve got {session_data.correct_answers_count} out of {session_data.questions_count} correct. Bye!'

# prompts

def prompt_for_difficulty(_locale):
    # should work as a reprompt
    return 'Choose your difficulty level. Easy, normal, or hard?'

def prompt_for_operation(_locale):
    # should work as a reprompt
    return 'What would you like to train? Addition, subtraction, multiplication, or division?'

# training

# TODO: better name for the method maybe?
def exercise_question(_locale, operation, difficulty):
    op1, op2 = generate_operands(operation, difficulty)
    # TODO: check if the "What is" doesn't get tiring all the time
    return (f'What is {op1} {operation.as_verb(_locale)} {op2}?',
            operation(op1, op2))

def generate_operands(operation, difficulty):
    # pylint: disable=invalid-name
    op1_max, op2_max = {1: (10, 10),
                        2: (50, 50),
                        3: (100, 100),
                        4: (1000, 100),
                        5: (1000, 1000)}[difficulty]
    op1 = random.randint(0, o_max)
    op2 = random.randint(0, o_max)

    if operation in [Operation.SUB, Operation.DIV] and op1 < op2:
        # prevent "unwanted" results
        op1, op2 = op2, op1

    if operation == Operation.DIV and op1 % op2 != 0:
        # assure round results of division
        op1 = math.ceil(op1 / op2) * op2

    return op1, op2

def difficulty_to_value(_locale, spoken_difficulty):
    # pylint: disable=no-else-return
    if spoken_difficulty == 'easy':
        return 1
    elif spoken_difficulty == 'normal':
        return 2
    elif spoken_difficulty in ['hard', 'difficult']:
        return 3
    else:
        return 2
