# Independent Studio installation checks

Owns discovery of exact public generated schema pins for `verify_studio.py`.
New contract groups and their validation-profile hashes must enter the isolated
consumer closure without a hand-maintained group list. Missing profile sources
and empty or ambiguous publication shapes fail closed. Schema content hashes and
public-path containment are checked by the actual staging/build gate.

Run `python -m pytest tests/studio_installation -q` from dev. These checks do not
qualify the consumer build or real browser; UI-01/V1 owns those separate gates.
