"""Host opt-in configuration; credentials stay in named environment variables."""

import os

from ..supervision_capture import CaptureReader
from ..supervision_journal.storage import RequestJournal
from ..supervision_scope.observations import require
from .recording import SupervisorRecording


def configured(engine, config):
    require(type(config) is dict and not set(config) - {'capture_data'}, 'supervision_configuration')
    captures = None
    if 'capture_data' in config:
        peer = config['capture_data']
        require(type(peer) is dict and set(peer) == {'endpoint', 'token_env'}, 'supervision_capture_configuration')
        captures = CaptureReader(peer['endpoint'], os.environ[peer['token_env']])
    # This host records incoming history only. Request production gets its actor mapping in B2.
    result = SupervisorRecording(RequestJournal(engine, {}), captures)
    result.ready()
    return result
