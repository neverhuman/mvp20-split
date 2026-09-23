#!/usr/bin/env python3
import base64, json, sys

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
CANDIDATE_KEYS = [
    "verdict", "interpretation", "summary", "attack_description", "repair_summary",
    "does_not_close", "claim_under_attack", "corrected", "repairs", "supersedes",
    "receipt_id", "schema", "repair_item_id", "campaign_item_id",
]


def find_dsse_envelope(d):
    if isinstance(d, dict) and {"payload", "payloadType", "signatures"} <= set(d.keys()):
        return d
    if isinstance(d, dict):
        for v in d.values():
            if isinstance(v, dict) and {"payload", "payloadType", "signatures"} <= set(v.keys()):
                return v
    return None


def main():
    paths = [l.strip() for l in sys.stdin if l.strip()]
    for p in paths:
        full = p if p.startswith("/") else ROOT + "/" + p
        print("=" * 100)
        print(p)
        try:
            d = json.load(open(full))
        except Exception as e:
            print("  (not JSON or unreadable):", e)
            continue
        env = find_dsse_envelope(d)
        if env is None:
            print("  (no DSSE envelope found)")
            continue
        try:
            body = json.loads(base64.standard_b64decode(env["payload"]))
        except Exception as e:
            print("  (payload decode failed):", e)
            continue
        for k in CANDIDATE_KEYS:
            if k in body:
                v = body[k]
                s = json.dumps(v, indent=2, sort_keys=True) if not isinstance(v, str) else v
                if len(s) > 1800:
                    s = s[:1800] + " ...[truncated]"
                print(f"  -- {k} --")
                print("  " + s.replace("\n", "\n  "))


if __name__ == "__main__":
    main()
