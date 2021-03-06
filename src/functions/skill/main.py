import os
import time

from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
import jmespath

from core import logger, log_invocation # pylint: disable=no-name-in-module
import content
import models
import utils


# TODO: navigate home intent?
# TODO: support "make it harder/easier" and "change operation" intents
# TODO: prompt for a 5-star review

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

def has_session_attribute(handler_input, attr_name):
    skill_attributes = handler_input.attributes_manager.session_attributes
    value = jmespath.search(f'session_data.{attr_name}', skill_attributes)
    return value is not None

#
# handlers
#

@request_handler('LaunchRequest')
def launch_request_handler(handler_input):
    # TODO: handle launch with preselected op and diff
    # TODO: manage late answers (i.e. launch when the answer to an exercise question didn't come in time - do you want to continue or start a new session?)

    am = handler_input.attributes_manager
    usage = models.SkillUsage.from_attributes(am.persistent_attributes)
    locale = handler_input.request_envelope.request.locale

    intro = content.intro_message(usage.launch_count, locale)
    # TODO: maybe ask if they want to continue? if so then I'd need to remember the question as well /o\
    usage.session_data = models.SessionData()
    am.session_attributes = models.asdict(usage)
    prompt = content.prompt_for_operation(locale)
    message = utils.combine_messages(intro, prompt)

    return utils.build_response(handler_input, message)

@request_handler('SessionEndedRequest')
def session_ended_request_handler(handler_input):
    persist_skill_data(handler_input)

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

@sb.request_handler(can_handle_func=lambda hi: \
                    is_intent_name('DidSelectDifficulty')(hi) and \
                    has_session_attribute(hi, 'operation'))
def did_select_difficulty_handler(handler_input):
    # TODO: handle also if they say "easier" or "harder" during

    am = handler_input.attributes_manager
    usage = models.SkillUsage.from_attributes(am.session_attributes)
    locale = handler_input.request_envelope.request.locale
    slots = handler_input.request_envelope.request.intent.slots

    spoken_difficulty = slots['difficulty'].value
    difficulty = content.difficulty_to_value(spoken_difficulty, locale)
    usage.session_data.difficulty = difficulty

    ack = content.confirmation(locale)
    start_message = content.start_message(locale)
    question, result, apl = content.build_question(usage, locale)
    usage.session_data.correct_result = result
    message = utils.combine_messages(ack, start_message, question)
    am.session_attributes = models.asdict(usage)

    rb = handler_input.response_builder
    rb.speak(message).ask(question)
    if utils.has_apl_support(handler_input):
        rb.add_directive(apl)
    return rb.response

@sb.request_handler(can_handle_func=lambda hi: \
                    is_intent_name('DidAnswer')(hi) and \
                    has_session_attribute(hi, 'operation') and \
                    has_session_attribute(hi, 'difficulty'))
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
            outcome = content.streak_encouragement(streak_count, locale)
    else:
        usage.session_data.streak_count = 0

        correct_result = usage.session_data.correct_result
        outcome = content.incorrect(correct_result, locale)
    usage.session_data.questions_count += 1

    question, result, apl = content.build_question(usage, locale)
    usage.session_data.correct_result = result
    message = utils.combine_messages(outcome, question)
    am.session_attributes = models.asdict(usage)

    rb = handler_input.response_builder
    rb.speak(message).ask(question)
    if utils.has_apl_support(handler_input):
        rb.add_directive(apl)
    return rb.response

@intent_handler('AMAZON.StopIntent', 'AMAZON.CancelIntent')
def stop_or_cancel_intent_handler(handler_input):
    persist_skill_data(handler_input, user_initiated_shutdown=True)

    am = handler_input.attributes_manager
    usage = models.SkillUsage.from_attributes(am.session_attributes)
    locale = handler_input.request_envelope.request.locale

    if usage.session_data.questions_count == 0:
        return handler_input.response_builder.set_should_end_session(True)\
                                             .response

    message = content.session_summary(usage.session_data, locale)

    return handler_input.response_builder.speak(message)\
                                         .set_should_end_session(True)\
                                         .response

def persist_skill_data(handler_input, user_initiated_shutdown=False):
    am = handler_input.attributes_manager

    usage = models.SkillUsage.from_attributes(am.session_attributes)
    usage.launch_count += 1
    usage.previous_session_end = int(time.time())

    if user_initiated_shutdown:
        # we assume they won't want to resume a session on the next
        # launch, hence we persist empty session_data
        usage.session_data = models.SessionData()

    if usage.session_data.operation:
        # TODO FIXIT HACK :(
        operation = usage.session_data.operation
        usage.session_data.operation = operation.value

    am.persistent_attributes = models.asdict(usage)
    am.save_persistent_attributes()

@intent_handler('AMAZON.HelpIntent', 'AMAZON.FallbackIntent')
def help_intent_handler(handler_input):
    locale = handler_input.request_envelope.request.locale
    message = content.help_message(locale)
    return utils.build_response(handler_input, message)

@sb.exception_handler(can_handle_func=lambda _i, _e: True)
def global_exception_handler(handler_input, exception):
    logger.warning('handler exception', exc_info=exception)
    locale = handler_input.request_envelope.request.locale
    message = content.dead_end_message(locale)
    return utils.build_response(handler_input, message)

@log_invocation
def handler(event, context):
    return sb.lambda_handler()(event, context)
