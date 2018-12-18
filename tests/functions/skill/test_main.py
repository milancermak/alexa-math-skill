import jmespath
import pytest

from ask_sdk_model.interfaces.alexa.presentation.apl import \
    RenderDocumentDirective
from src.functions.skill import main, models
from .fixtures import ( # pylint: disable=unused-import
    dynamodb_client, launch_request, session_ended_request,
    did_select_operation_intent, did_select_difficulty_intent,
    did_answer_intent_correct, did_answer_intent_wrong,
    build_intent_event, locale
)


@pytest.fixture(autouse=True)
def use_mock_dynamodb_client(dynamodb_client):
    # uses a new mock object every time so it's safe
    main.sb.dynamodb_client = dynamodb_client

#
# assert helpers
#

def assert_has_apl(result):
    assert jmespath.search('response.directives[0].type', result) == \
        'Alexa.Presentation.APL.RenderDocument'
    assert jmespath.search('response.directives[0].datasources', result) is not None
    assert jmespath.search('response.directives[0].document', result) is not None

def assert_keypath(path, data, value):
    assert jmespath.search(path, data) == value

#
# tests
#

def test_launch_request_handler(launch_request):
    r = main.sb.lambda_handler()(launch_request, {})

    assert isinstance(r, dict)
    # TODO: could this be wrapped in a with statement? is it worth it?
    assert_keypath('sessionAttributes.launch_count', r, 0)
    assert_keypath('sessionAttributes.previous_session_end', r, 0)
    assert_keypath('sessionAttributes.session_data.operation', r, None)
    assert_keypath('sessionAttributes.session_data.difficulty', r, None)
    assert_keypath('sessionAttributes.session_data.correct_result', r, 0)
    assert_keypath('sessionAttributes.session_data.questions_count', r, 0)
    assert_keypath('sessionAttributes.session_data.correct_answers_count', r, 0)
    assert_keypath('sessionAttributes.session_data.streak_count', r, 0)

def test_session_ended_request_handler(session_ended_request):
    r = main.sb.lambda_handler()(session_ended_request, {})

    assert isinstance(r, dict)
    assert_keypath('sessionAttributes', r, {})

def test_did_select_operation_handler(did_select_operation_intent):
    r = main.sb.lambda_handler()(did_select_operation_intent, {})

    assert isinstance(r, dict)
    assert_keypath('sessionAttributes.session_data.operation', r, 'add')

def test_did_select_difficulty_handler(did_select_difficulty_intent):
    r = main.sb.lambda_handler()(did_select_difficulty_intent, {})

    assert isinstance(r, dict)
    assert_keypath('sessionAttributes.session_data.difficulty', r, 3)
    assert_has_apl(r)

def test_did_answer_handler_correct_answer(did_answer_intent_correct):
    r = main.sb.lambda_handler()(did_answer_intent_correct, {})

    assert isinstance(r, dict)
    assert_keypath('sessionAttributes.session_data.questions_count', r, 1)
    assert_keypath('sessionAttributes.session_data.correct_answers_count', r, 1)
    assert_keypath('sessionAttributes.session_data.streak_count', r, 1)
    assert_has_apl(r)

def test_did_answer_handler_wrong_answer(did_answer_intent_wrong):
    r = main.sb.lambda_handler()(did_answer_intent_wrong, {})

    assert isinstance(r, dict)
    assert_keypath('sessionAttributes.session_data.questions_count', r, 1)
    assert_keypath('sessionAttributes.session_data.correct_answers_count', r, 0)
    assert_keypath('sessionAttributes.session_data.streak_count', r, 0)
    assert_has_apl(r)

@pytest.mark.parametrize('intent_name', ['AMAZON.HelpIntent',
                                         'AMAZON.FallbackIntent',
                                         'AMAZON.StopIntent',
                                         'AMAZON.CancelIntent'])
def test_other_intents(intent_name):
    intent_event = build_intent_event(intent_name)
    r = main.sb.lambda_handler()(intent_event, {})
    assert isinstance(r, dict)

@pytest.mark.parametrize('intent_name', ['AMAZON.StopIntent',
                                         'AMAZON.CancelIntent'])
def test_early_stop(intent_name):
    intent_event = build_intent_event(intent_name)
    del intent_event['session']['attributes']['session_data']['operation']
    del intent_event['session']['attributes']['session_data']['difficulty']
    intent_event['session']['attributes']['session_data']['questions_count'] = 0

    r = main.sb.lambda_handler()(intent_event, {})

    assert isinstance(r, dict)
    assert_keypath('response.outputSpeech', r, None)
    assert_keypath('response.shouldEndSession', r, True)

@pytest.mark.parametrize('questions_count', [0, 1])
def test_build_question_content(questions_count, locale):
    attributes = {'launch_count': 4,
                  'previous_session_end': 15000000,
                  'session_data': {
                      'operation': 'mul',
                      'difficulty': 3,
                      'questions_count': questions_count
                  }}
    usage = models.SkillUsage.from_attributes(attributes)

    question, apl = main.build_question_content(usage, locale)

    assert isinstance(question, str)
    assert isinstance(apl, RenderDocumentDirective)
