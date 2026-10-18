"""Version 2 reviewed policy anchors; change through code review, never from payload metadata.

Trust requires this verifier/policy to come from the reviewed Git revision.
It does not authenticate a wholly replaced verifier or establish scientific truth.
"""
POLICY_INPUT_SHA256 = {'claims.json': 'c8d54b37c05aa21da1fd26549c8947eaa891ceae1254875fb4c6db09262f9692', 'byte_reconstruction.v1.json': 'cd72f7cf961fec8c0ee249dc442b7e71474896d54e2a72adebe2419b9c4dbfa4', 'capsule_allowlist.json': '23ba3103a4b3e44615c6c18d45633375727ebe20dc16898234b3bc02bf130d6a', 'source_lock.json': 'e534a5ee1f22f31aa16235e8078ddea2923d447b5fd05015cd256acfd18309f9'}
