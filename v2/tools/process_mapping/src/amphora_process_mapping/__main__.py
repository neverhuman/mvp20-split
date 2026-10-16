"""Explicit descriptor/schema/one-attempt worker commands."""
import argparse
import json
import sys

from amphora_tool_protocol import ProtocolError
from .capability import ProcessCapability,SCHEMAS,PROFILES
from .worker import run_process_worker


def main():
    parser=argparse.ArgumentParser(prog="amphora-process-mapping")
    commands=parser.add_subparsers(dest="command",required=True)
    describe=commands.add_parser("describe")
    describe.add_argument("--image-sha256",required=True)
    describe.add_argument("--operation",choices=tuple(PROFILES),default="map-materials")
    commands.add_parser("schema").add_argument("--record",choices=tuple(SCHEMAS),required=True)
    worker=commands.add_parser("worker")
    worker.add_argument("--config",required=True)
    worker.add_argument("--operation",choices=tuple(PROFILES),default="map-materials")
    args=parser.parse_args()
    try:
        capability=ProcessCapability(getattr(args,"operation","map-materials"))
        if args.command=="describe":print(capability.descriptor(args.image_sha256).model_dump_json())
        elif args.command=="schema":sys.stdout.buffer.write(capability.schema_bytes(args.record))
        else:print(json.dumps(run_process_worker(args.config,args.operation)))
    except ProtocolError:
        print("process_worker_incomplete",file=sys.stderr)
        raise SystemExit(3) from None
    except (ValueError,OSError,KeyError,TypeError):
        print("invalid_process_input_or_configuration",file=sys.stderr)
        raise SystemExit(2) from None


if __name__=="__main__":main()
