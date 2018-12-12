import functools
import random


def build_response(handler_input, message, question=None):
    # just a convenience so I don't have to type it all the time
    question = question or message
    return handler_input.response_builder.speak(message)\
                                         .ask(question)\
                                         .response

def combine_messages(*messages):
    # pylint: disable=invalid-name
    punctuated = []
    for message in messages:
        m = message.strip()
        if not m.endswith(('.', '?', '!', '¿', '¡')):
            m += '.'
        punctuated.append(m)

    return ' '.join(punctuated)

def randomize(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return random.choice(fn(*args, **kwargs))
    return wrapper

def speechcon(phrase):
    # # https://developer.amazon.com/docs/custom-skills/speechcon-reference-interjections-english-us.html
    return f'<say-as interpret-as="interjection">{phrase}</say-as>'
