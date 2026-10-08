"""Serve the local browser boundary or open a one-time workspace session."""

import argparse
import http.client
import json
import os
import threading
from pathlib import Path
import webbrowser

from .configuration import Configuration, GatewayError, Peer, require
from .server import GatewayServer


def launch(endpoint, key_env, environment):
    peer = Peer.load({"endpoint":endpoint, "token_env":key_env}, environment)
    connection = http.client.HTTPConnection("127.0.0.1", peer.port, timeout=10)
    try:
        connection.request("POST", "/launcher/ticket", headers={"Authorization":"Bearer " + peer.token})
        response = connection.getresponse()
        require(response.status == 200, "gateway_launcher_unavailable")
        raw = response.read(4097)
        require(len(raw) <= 4096, "gateway_ticket_response")
        record = json.loads(raw)
        ticket = record.get("ticket")
        require(type(ticket) is str and 32 <= len(ticket) <= 128 and all(c.isascii() and (c.isalnum() or c in "_-") for c in ticket), "gateway_ticket_response")
        require(webbrowser.open("http://127.0.0.1:" + str(peer.port) + "/#launch=" + ticket), "gateway_browser_unavailable")
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    serve = actions.add_parser("serve")
    serve.add_argument("--config", type=Path, required=True)
    serve.add_argument("--port", type=int, required=True)
    serve.add_argument("--stop-file", type=Path)
    browser = actions.add_parser("launch")
    browser.add_argument("--endpoint", required=True)
    browser.add_argument("--key-env", default="AMPHORA_GATEWAY_SESSION_KEY")
    args = parser.parse_args()
    try:
        if args.action == "launch":
            launch(args.endpoint, args.key_env, os.environ)
            print("Local workspace opened.")
            return 0
        require(1024 <= args.port <= 65535, "gateway_port")
        server = GatewayServer(Configuration.load(args.config, os.environ), args.port)
        stopped = threading.Event()
        if args.stop_file:
            def watch_stop():
                while not stopped.wait(.25):
                    if args.stop_file.exists():
                        server.shutdown()
                        return
            threading.Thread(target=watch_stop, daemon=True).start()
        try:
            server.serve_forever(poll_interval=.25)
        except KeyboardInterrupt:
            pass
        finally:
            stopped.set()
            server.server_close()
        return 0
    except GatewayError as error:
        print(json.dumps({"status":"rejected", "reason":str(error)}))
        return 2
    except Exception:
        print(json.dumps({"status":"rejected", "reason":"gateway_unavailable"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
