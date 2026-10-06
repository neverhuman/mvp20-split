# Preparation domain tests

Pure Runtime-owned recipe and reservation tests. No SQL or network. Checks immutable ordered configuration identity, scope/alias consistency, context capacity, closed profiles, each slot/campaign request/call ceiling and exact/conflicting replay. Actual publication, admission and concurrent reservations require the subsequent integration suite.

Run `dev/run_tests.py --module runtime --area supervision_preparation` from v2 with the development Python environment.
