# Typed binding execution verification

Owner: Campaign Runtime; [BP-04.04A](../../../../docs/Build%20Plans/BP-04/BP-04.04A%20Typed%20artifact%20and%20collection%20bindings.md).

B1 proves that a valid compiled wire-v4 binding plan cannot accidentally execute before durable conversion/publication is implemented. The PostgreSQL admission test preserves the original rejected command receipt and creates no run. B2 replaces this deliberate gate only after real typed conversion and protection transitions exist; B3/V1 add competing-process and installed-peer proof.

Select with `dev/run_tests.py --module runtime --area bindings --coverage`; explicitly enable the labeled PostgreSQL fixture. Run serially with other single-campaign owner suites. Wire/schema fixtures belong to `contracts/campaigns/tests/executable`; semantic compiler oracles remain in `tests/compiler/test_bindings.py`. Test ownership stays with its behavioral module.
