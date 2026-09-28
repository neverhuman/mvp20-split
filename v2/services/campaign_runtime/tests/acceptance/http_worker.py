"""Public HTTP worker fixture: standard library only, no database or owner imports."""

import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener


def main():
    assert not any("DATABASE" in key or "POSTGRES" in key or key.startswith("PG") for key in os.environ)
    request = json.loads(sys.stdin.readline())
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(Request(request["endpoint"] + request["path"],
            data=json.dumps(request["command"]).encode(), headers={
                "Authorization": "Bearer " + request["token"], "Content-Type": "application/json"}), timeout=8) as response:
            result = {"status": response.status, "body": json.loads(response.read())}
    except HTTPError as error:
        result = {"status": error.code, "body": json.loads(error.read())}
    print(json.dumps(result), flush=True)
    if request.get("stay"):
        sys.stdin.readline()  # Parent kills the worker while its issued lease is live.


if __name__ == "__main__":
    main()
