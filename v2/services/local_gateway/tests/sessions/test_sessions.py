from concurrent.futures import ThreadPoolExecutor

import pytest

from amphora_local_gateway.sessions import Sessions, SessionDenied


def test_ticket_single_use_under_concurrent_exchange():
    sessions = Sessions()
    ticket = sessions.issue_ticket()
    def exchange():
        try: return sessions.exchange(ticket)
        except SessionDenied: return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _:exchange(), range(8)))
    accepted = [value for value in results if value is not None]
    assert len(accepted) == 1
    sessions.authenticate(accepted[0])
    sessions.revoke(accepted[0])
    with pytest.raises(SessionDenied): sessions.authenticate(accepted[0])


def test_expiry_restart_and_bounded_capacity():
    now = [100.0]
    sessions = Sessions(clock=lambda:now[0])
    ticket = sessions.issue_ticket()
    now[0] += 60
    with pytest.raises(SessionDenied): sessions.exchange(ticket)
    token = sessions.exchange(sessions.issue_ticket())
    with pytest.raises(SessionDenied): Sessions().authenticate(token)
    now[0] += 8 * 3600
    with pytest.raises(SessionDenied): sessions.authenticate(token)
    for _ in range(16): sessions.issue_ticket()
    with pytest.raises(SessionDenied, match='ticket_capacity'): sessions.issue_ticket()


@pytest.mark.parametrize('token',[None, '', 'short', 'x'*129, '\u2603'*40])
def test_malformed_session_tokens_denied(token):
    with pytest.raises(SessionDenied): Sessions().authenticate(token)
