import functools
import logging
import os
import sys

import structlog


# TODO: not sure how this behaves in Lambda
logging.basicConfig(format="%(message)s",
                    stream=sys.stdout,
                    level=logging.INFO)


def add_service_context(_logger, _method, event_dict):
    """
    Function intended as a processor for structlog. It adds information
    about the service environment and reasonable defaults when not running in Lambda.
    """
    event_dict['region'] = os.environ.get('REGION', os.uname().nodename)
    event_dict['service'] = os.environ.get('SERVICE', os.path.abspath(__file__))
    event_dict['stage'] = os.environ.get('STAGE', 'dev')
    return event_dict

structlog.configure_once(
    processors=[
        structlog.stdlib.add_log_level,
        add_service_context,
        structlog.processors.TimeStamper(fmt='iso', utc=True, key='ts'),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    #logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True
)

logger = structlog.get_logger()

def log_invocation(fn):
    """
    A decorator for Lambda handlers that logs the input event and the return
    value of the function. Easy and convenient way how to add more visibility
    to the runtime of your Lambdas.
    """

    @functools.wraps(fn)
    def wrapper(event, context):
        try:
            logger.info('lambda invocation', invocation=event)
            result = fn(event, context)
        except Exception as e: # pylint: disable=broad-except,invalid-name
            logger.error('execution error',
                         exc_info=e,
                         invocation=event,
                         function_name=context.function_name,
                         function_version=context.function_version,
                         aws_request_id=context.aws_request_id)
            raise e
        else:
            logger.info('lambda result', result=result)
            return result

    return wrapper
