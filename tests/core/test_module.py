import collections
import uuid

import pytest

from src import core
from tests import test_utils


@pytest.mark.parametrize('ret_val', [1, None])
def test_log_invocation_decorator(caplog, ret_val):
    @core.log_invocation
    def handler(*_args):
        return ret_val

    assert handler({}, None) == ret_val

    invocation_log, result_log = test_utils.load_log_events(caplog)
    assert 'invocation' in invocation_log
    assert 'result' in result_log

def test_log_invocation_decorator_throwing(caplog):
    Context = collections.namedtuple('Context',
                                     ['function_name',
                                      'function_version',
                                      'aws_request_id'])
    invocation_context = Context(function_name='tester',
                                 function_version='$LATEST',
                                 aws_request_id=str(uuid.uuid4))

    @core.log_invocation
    def handler(*_args):
        raise RuntimeError('No can do')

    with pytest.raises(RuntimeError):
        handler({}, invocation_context)

    invocation_log, error_log = test_utils.load_log_events(caplog)
    assert 'invocation' in invocation_log
    assert 'invocation' in error_log
    assert 'exception' in error_log
    assert 'function_name' in error_log
    assert 'function_version' in error_log
    assert 'aws_request_id' in error_log
