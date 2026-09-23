import json, base64, hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
p = "amphora-solvency-score/benchmarks/bigsoldb-v1/inhouse_benchmark_receipt.v1.dsse.json"
env = json.load(open(p))
pub = json.load(open(".amphora/control/local-ed25519.pub.json"))
body = base64.b64decode(env["payload"]); pt = env["payloadType"]
pae = b"DSSEv1 " + str(len(pt)).encode() + b" " + pt.encode() + b" " + str(len(body)).encode() + b" " + body
pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub["public_key_hex"]))
pk.verify(base64.b64decode(env["signatures"][0]["sig"]), pae)
print("SIGNATURE_VERIFY=VALID keyid", env["signatures"][0]["keyid"])
print("envelope_sha256", hashlib.sha256(open(p, "rb").read()).hexdigest())
