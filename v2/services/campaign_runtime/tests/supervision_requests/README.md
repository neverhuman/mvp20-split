# Supervisor request binding tests

Pure Runtime scope projection, original request byte compatibility and rejection of foreign/mismatched claims. Literal fixtures live in contracts/supervision/tests/fixtures; planning-request.json was produced by the unchanged Planning0.69 RequestSnapshot profile before implementation verification. Runtime tests do not import private Planning code.

Run dev/run_tests.py --module runtime --area supervision_requests. These tests do not prove authentication, stored ancestry, aggregate budget, admitted policy, current grants or acceptance. The oversized valid snapshot oracle proves that transport byte limits reject explicitly without silently omitting selected nodes.
