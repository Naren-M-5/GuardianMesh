#!/usr/bin/env python3
import argparse
import hashlib
import hmac
import json
import time
import urllib.request
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a GuardianMesh scenario")
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/v1/integrations/ring/webhook")
    parser.add_argument("--secret", default="change-me")
    args = parser.parse_args()
    events = json.loads(args.scenario.read_text(encoding="utf-8"))
    for event in events:
        body = json.dumps(event, separators=(",", ":")).encode()
        timestamp = str(int(time.time()))
        signature = hmac.new(args.secret.encode(), timestamp.encode() + b"." + body,
                             hashlib.sha256).hexdigest()
        request = urllib.request.Request(args.url, data=body, method="POST", headers={
            "Content-Type": "application/json", "X-Ring-Timestamp": timestamp,
            "X-Ring-Signature": f"sha256={signature}",
        })
        with urllib.request.urlopen(request) as response:
            print(response.read().decode())


if __name__ == "__main__":
    main()
