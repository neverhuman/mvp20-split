#!/usr/bin/env bash
# Regression suite for the hourly loop's availability behaviour.
#
# These exist because the loop's verification machinery was extensively tested
# and its ABILITY TO KEEP RUNNING was not. On 2026-08-06 three usage-limit
# refusals latched the saturation gate for 80 hours; every check below is a
# fact that, had it held, would have prevented that.
#
# Fires are simulated: a fake agent binary and a stubbed ssh, against a
# throwaway ROOT. Nothing here touches live state or spends a real fire.
set -uo pipefail
cd "$(dirname "$0")"
rc=0
for t in t0_parser.sh t1_classify.sh t5_gate.sh t9_recovery.sh t10_lanes.sh t11_summary.sh t12_routing.sh; do
    echo "=============================================================="
    echo "== $t"
    echo "=============================================================="
    bash "$t" || rc=1
    echo
done
[ "$rc" -eq 0 ] && echo "ALL SUITES PASSED" || echo "SUITE FAILURES PRESENT"
exit "$rc"
