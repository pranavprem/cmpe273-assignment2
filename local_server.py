#!/usr/bin/env python3
"""Local stand-in for API Gateway and DynamoDB.

The Lambda handlers in each pizzashop* folder are unchanged as the source of
the business logic. This process does the job the 2017 Velocity templates did:
it turns HTTP JSON into the event shape each handler expects, and turns
handler return values back into HTTP.

By default DynamoDB is an in-memory moto backend, so the API runs without AWS
credentials. Pass --aws to call the real tables in AWS_DEFAULT_REGION
(us-west-2 in the original configs).
"""

import argparse
import importlib.util
import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import boto3

ROOT = Path(__file__).resolve().parent

FUNCTIONS = (
    "pizzashopmenupost",
    "pizzashopmenudelete",
    "pizzashopmenuget",
    "pizzashopmenuput",
    "pizzashoporderpost",
    "pizzashoporderput",
    "pizzashoporderget",
)

_services = None


def load_service(folder):
    path = ROOT / folder / "service.py"
    spec = importlib.util.spec_from_file_location(f"{folder.replace('-', '_')}_service", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def services():
    global _services
    if _services is None:
        _services = {name: load_service(name) for name in FUNCTIONS}
    return _services


def freeze_module(module, when):
    """Pin datetime.now/today on a handler module. strptime still works."""

    class Frozen(datetime):
        @classmethod
        def now(cls, tz=None):
            return when

        @classmethod
        def today(cls):
            return when

    module.datetime = Frozen


def freeze_clock(when):
    loaded = services()
    freeze_module(loaded["pizzashoporderpost"], when)
    freeze_module(loaded["pizzashoporderput"], when)


def create_tables():
    client = boto3.client("dynamodb")
    existing = set(client.list_tables().get("TableNames", []))
    for name, key in (("pizzashopmenu", "menu_id"), ("pizzashoporder", "order_id")):
        if name in existing:
            continue
        client.create_table(
            TableName=name,
            KeySchema=[{"AttributeName": key, "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": key, "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )


def interpret_result(result):
    """Map a handler return value to (status, payload).

    These functions predate Lambda proxy responses, and they do not share one
    tuple order. Menu PUT returns (body, 200, "OK"). The others return
    (status, "OK") or (status, "OK", body).
    """
    if not isinstance(result, tuple):
        return 200, result
    if len(result) == 2 and isinstance(result[0], int):
        return result[0], result[1]
    if len(result) == 3 and isinstance(result[0], int):
        return result[0], result[2]
    if len(result) == 3 and isinstance(result[1], int):
        return result[1], result[0]
    return 200, result


def public_menu(payload):
    item = payload["Item"]
    return {
        "menu_id": item["menu_id"]["S"],
        "store_name": item["store_name"]["S"],
        "selection": [entry["S"] for entry in item["selection"]["L"]],
        "size": [entry["S"] for entry in item["size"]["L"]],
        "sequence": [entry["S"] for entry in item["sequence"]["L"]],
        "price": [entry["N"] for entry in item["price"]["L"]],
        "store_hours": {day: hours for day, hours in item["store_hours"]},
    }


def public_order(payload):
    return {
        "menu_id": payload["menu_id"],
        "order_id": payload["order_id"],
        "customer_name": payload["customer_name"],
        "customer_email": payload["customer_email"],
        "order_status": payload["order_status"],
        "order": {key: value for key, value in payload["order"]},
    }


def jsonable(payload):
    if isinstance(payload, Exception):
        return {"error": str(payload)}
    return payload


def call_handler(name, event):
    try:
        result = services()[name].handler(event, None)
    except Exception as exc:
        return 500, {"error": str(exc)}
    status, payload = interpret_result(result)
    if payload == "OK":
        payload = None
    return status, jsonable(payload)


def route(method, path, body):
    parts = [unquote(part) for part in path.strip("/").split("/") if part]
    if not parts:
        if method == "GET":
            return 200, {
                "service": "cmpe273 pizza shop",
                "routes": [
                    "POST /menu",
                    "GET /menu/{menu-id}",
                    "PUT /menu/{menu-id}",
                    "DELETE /menu/{menu-id}",
                    "POST /order",
                    "GET /order/{order-id}",
                    "PUT /order/{order-id}",
                ],
            }
        return 404, {"error": "not found"}

    resource, ident = parts[0], parts[1] if len(parts) > 1 else None
    if resource == "menu" and method == "POST" and ident is None:
        return call_handler("pizzashopmenupost", body or {})
    if resource == "menu" and ident:
        key = {"menu_id": {"S": ident}}
        if method == "GET":
            status, payload = call_handler("pizzashopmenuget", key)
            if status == 200:
                payload = public_menu(payload)
            return status, payload
        if method == "DELETE":
            return call_handler("pizzashopmenudelete", key)
        if method == "PUT":
            event = {"menu_id": {"S": ident}}
            if body and "selection" in body:
                event["selections"] = body["selection"]
            return call_handler("pizzashopmenuput", event)
    if resource == "order" and method == "POST" and ident is None:
        return call_handler("pizzashoporderpost", body or {})
    if resource == "order" and ident:
        if method == "GET":
            status, payload = call_handler("pizzashoporderget", {"order_id": {"S": ident}})
            if status == 200:
                payload = public_order(payload)
            return status, payload
        if method == "PUT":
            if not body or "input" not in body:
                return 400, {"error": "input is required"}
            try:
                number = int(body["input"])
            except (TypeError, ValueError):
                return 400, {"error": "input must be a number"}
            return call_handler(
                "pizzashoporderput",
                {"order_id": ident, "selection_number": number},
            )
    return 404, {"error": "not found"}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_PUT(self):
        self._handle()

    def do_DELETE(self):
        self._handle()

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}")

    def _read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        if not raw.strip():
            return {}
        return json.loads(raw.decode())

    def _handle(self):
        path = urlparse(self.path).path
        try:
            body = self._read_body()
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid JSON"})
            return
        status, payload = route(self.command, path, body)
        self._send(status, payload)

    def _send(self, status, payload):
        if payload is None:
            encoded = b""
        else:
            encoded = (json.dumps(payload, indent=2) + "\n").encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main():
    parser = argparse.ArgumentParser(description="Run the pizza shop API locally")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument(
        "--now",
        help="Freeze the order clock at this local time (YYYY-MM-DDTHH:MM:SS)",
    )
    parser.add_argument(
        "--aws",
        action="store_true",
        help="Use real DynamoDB instead of the in-memory backend",
    )
    args = parser.parse_args()

    os.environ.setdefault("AWS_DEFAULT_REGION", "us-west-2")
    os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
    mock = None
    if not args.aws:
        os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
        os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
        os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
        from moto import mock_aws

        mock = mock_aws()
        mock.start()
        create_tables()
        print("DynamoDB: in-memory tables pizzashopmenu, pizzashoporder")
    else:
        print("DynamoDB: real AWS in", os.environ.get("AWS_DEFAULT_REGION"))

    if args.now:
        when = datetime.strptime(args.now, "%Y-%m-%dT%H:%M:%S")
        freeze_clock(when)
        print(f"Clock frozen at {when.strftime('%A %Y-%m-%d %H:%M:%S')}")

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Pizza shop listening on http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping")
    finally:
        server.server_close()
        if mock is not None:
            mock.stop()


if __name__ == "__main__":
    main()
