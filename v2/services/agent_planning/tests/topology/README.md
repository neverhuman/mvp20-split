# Topology verification

Owner: Planning topology module, BP-08.04. Tests remain scoped here. Pure fixtures declare public plan/release metadata and do not claim actual compiler or Registry evidence. test_policy owns exact single-edit changes and rejection oracles; test_storage uses owned PostgreSQL and scripted current readers for retry/concurrency/conflict/rollback/immutable history; test_peers exercises real bounded HTTP clients against loopback protocol stubs. No live model call or actual Runtime admission occurs here.

Run with pytest importlib mode and v2/dev config. Storage requires AMPHORA_TEST_POSTGRES=1 and forward Planning0020; never use older installed migrators or reset retained data.71 focused tests18.90s and prior128-regression scope49.01s passed; topology350statements/30branches100%. Existing supervision API/metadata client regressions remain separate selectable areas. Actual owner/compiler/adoption and independent replacement remain later BP-08.04 gates.
