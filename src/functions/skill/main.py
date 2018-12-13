import os

from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name

from core import log_invocation # pylint: disable=no-name-in-module
import content
import models
import utils


# TODO: add cards?
# TODO: add APL
# TODO: navigate home intent?
# TODO: support "make it harder/easier" and "change operation" intents
# TODO: 5 levels? in each level an operand's magnitue would increase
# TODO: no streaks?
# TODO: how to come back from HelpIntent?


sb = StandardSkillBuilder(table_name=os.environ['SKILL_TABLE_NAME'])
sb.skill_id = 'amzn1.ask.skill.d455ad8c-dde9-4ee8-a492-4e3985b5ff79'
sb.custom_user_agent = 'alexa-math-practice-skill/1.0.0'

#
# helpers
#

def request_handler(request_type):
    def wrapper(fn):
        return sb.request_handler(is_request_type(request_type))(fn)
    return wrapper

def intent_handler(*intent_names):
    def wrapper(fn):
        has_intent = lambda handler_input: \
            any([is_intent_name(name)(handler_input)
                 for name in intent_names])
        return sb.request_handler(has_intent)(fn)
    return wrapper

#
# handlers
#

@request_handler('LaunchRequest')
def launch_request_handler(handler_input):
    # TODO: handle launch with preselected op and diff

    # TODO: manage late answers (i.e. launch when the answer to an exercise question didn't come in time - do you want to continue or start a new session?)

    am = handler_input.attributes_manager
    usage = models.SkillUsage.from_attributes(am.persistent_attributes)
    if usage.is_new_session():
        # TODO: add intro message on first run?
        # TODO: maybe ask if they want to continue? if so then I'd need to remember the question as well /o\
        usage.session_data = models.SessionData()
    am.session_attributes = models.asdict(usage)

    locale = handler_input.request_envelope.request.locale
    message = content.prompt_for_operation(locale)
    return utils.build_response(handler_input, message)

@request_handler('SessionEndedRequest')
def session_ended_request_handler(handler_input):
    persist_skill_data(handler_input)

@intent_handler('DidAnswer')
def did_answer_handler(handler_input):

    am = handler_input.attributes_manager
    usage = models.SkillUsage.from_attributes(am.session_attributes)
    locale = handler_input.request_envelope.request.locale
    slots = handler_input.request_envelope.request.intent.slots

    answer = int(slots['answer'].value)
    is_correct = answer == usage.session_data.correct_result

    if is_correct:
        usage.session_data.correct_answers_count += 1
        usage.session_data.streak_count += 1

        outcome = content.correct(locale)
        streak_count = usage.session_data.streak_count
        # pylint: disable=bad-continuation
        if (streak_count == 5 or
            (streak_count >= 10 and streak_count % 10 == 0)):
            # on 5 in a row and every 10
            outcome = content.streak_encouragement(locale, streak_count)
    else:
        usage.session_data.streak_count = 0

        correct_result = usage.session_data.correct_result
        outcome = content.incorrect(locale, correct_result)

    question, result = content.exercise_question(locale,
                                                 usage.session_data.operation,
                                                 usage.session_data.difficulty)
    message = utils.combine_messages(outcome, question)

    usage.session_data.correct_result = result
    usage.session_data.questions_count += 1
    am.session_attributes = models.asdict(usage)

    return utils.build_response(handler_input, message, question)

@intent_handler('DidSelectOperation')
def did_select_operation_handler(handler_input):
    # TODO: what if I already have the difficulty level? i.e. I can directly ask a question

    am = handler_input.attributes_manager
    usage = models.SkillUsage.from_attributes(am.session_attributes)
    locale = handler_input.request_envelope.request.locale
    slots = handler_input.request_envelope.request.intent.slots

    spoken_operation = slots['operation'].value
    operation = models.Operation.from_word(spoken_operation, locale)
    usage.session_data.operation = operation
    am.session_attributes = models.asdict(usage)

    ack = content.confirmation(locale)
    question = content.prompt_for_difficulty(locale)
    message = utils.combine_messages(ack, question)

    return utils.build_response(handler_input, message, question)

@intent_handler('DidSelectDifficulty')
def did_select_difficulty_handler(handler_input):
    # TODO: handle also if they say "easier" or "harder" during
    # TODO: what if I don't have the operation set yet?

    am = handler_input.attributes_manager
    usage = models.SkillUsage.from_attributes(am.session_attributes)
    locale = handler_input.request_envelope.request.locale
    slots = handler_input.request_envelope.request.intent.slots

    spoken_difficulty = slots['difficulty'].value
    # TODO: use an enum for difficulty as well?
    difficulty = content.difficulty_to_value(locale, spoken_difficulty)
    difficulty = max(1, min(5, difficulty)) # keep it in the [1, 5] interval
    usage.session_data.difficulty = difficulty

    ack = content.confirmation(locale)
    start_message = content.start_message(locale)
    operation = usage.session_data.operation
    question, result = content.exercise_question(locale, operation, difficulty)
    message = utils.combine_messages(ack, start_message, question)

    usage.session_data.correct_result = result
    usage.session_data.questions_count += 1
    am.session_attributes = models.asdict(usage)

    return utils.build_response(handler_input, message, question)

@intent_handler('AMAZON.HelpIntent', 'AMAZON.FallbackIntent')
def help_intent_handler(handler_input):
    # TODO: is there a way how to get out of the help prompt? what can the user do next?
    locale = handler_input.request_envelope.request.locale
    message = content.help_message(locale)
    return utils.build_response(handler_input, message)

@intent_handler('AMAZON.StopIntent', 'AMAZON.CancelIntent')
def stop_or_cancel_intent_handler(handler_input):
    persist_skill_data(handler_input, user_initiated_shutdown=True)

    am = handler_input.attributes_manager
    usage = models.SkillUsage.from_attributes(am.session_attributes)
    locale = handler_input.request_envelope.request.locale

    message = content.session_summary(locale, usage.session_data)

    return handler_input.response_builder.speak(message)\
                                         .set_should_end_session(True)\
                                         .response

def persist_skill_data(handler_input, user_initiated_shutdown=False):
    session_end = handler_input.request_envelope.request.timestamp
    am = handler_input.attributes_manager

    usage = models.SkillUsage.from_attributes(am.session_attributes)
    usage.launch_count += 1
    usage.previous_session_end = session_end

    if user_initiated_shutdown:
        # we assume they won't want to resume a session on the next
        # launch, hence we persist empty session_data
        usage.session_data = models.SessionData()

    am.persistent_attributes = models.asdict(usage)
    am.save_persistent_attributes()

# @sb.exception_handler(can_handle_func=lambda _i, _e: True)
# def global_exception_handler(handler_input, exception):
#     pass

@log_invocation
def handler(event, context):
    return sb.lambda_handler()(event, context)
