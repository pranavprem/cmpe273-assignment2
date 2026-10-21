import json
import threading
from datetime import datetime
from http.server import ThreadingHTTPServer
from urllib import error, request

import pytest
from moto import mock_aws

from local_server import Handler, create_tables, freeze_clock


@pytest.fixture
def base_url():
    mock = mock_aws()
    mock.start()
    create_tables()
    freeze_clock(datetime(2017, 5, 15, 10, 30, 0))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        yield url
    finally:
        httpd.shutdown()
        httpd.server_close()
        mock.stop()


def call(base, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = request.Request(
        base + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data is not None else {},
    )
    try:
        with request.urlopen(req) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except error.HTTPError as exc:
        raw = exc.read()
        return exc.code, json.loads(raw) if raw else None


MENU = {
    "menu_id": "menu-1",
    "store_name": "Pizza Hut",
    "selection": ["Cheese", "Pepperoni"],
    "size": ["Slide", "Small", "Medium", "Large", "X-Large"],
    "price": ["3.50", "7.00", "10.00", "15.00", "20.00"],
    "store_hours": {
        "Mon": "10am-10pm",
        "Tue": "10am-10pm",
        "Wed": "10am-10pm",
        "Thu": "10am-10pm",
        "Fri": "10am-10pm",
        "Sat": "11am-12pm",
        "Sun": "11am-12pm",
    },
}


def test_http_order_flow(base_url):
    status, index = call(base_url, "GET", "/")
    assert status == 200
    assert "POST /menu" in index["routes"]

    status, payload = call(base_url, "POST", "/menu", MENU)
    assert status == 200
    assert payload is None

    status, menu = call(base_url, "GET", "/menu/menu-1")
    assert status == 200
    assert menu["store_name"] == "Pizza Hut"
    assert menu["sequence"] == ["selection", "size"]
    assert menu["price"][3] == "15.00"
    assert menu["store_hours"]["Sat"] == "11am-12pm"
    assert menu["selection"] == ["Cheese", "Pepperoni"]

    status, updated = call(base_url, "PUT", "/menu/menu-1", {})
    assert status == 200
    assert updated["selection"] == ["Cheese", "Pepperoni", "Vegetable"]

    status, updated = call(base_url, "PUT", "/menu/menu-1")
    assert updated["selection"].count("Vegetable") == 1

    status, posted = call(
        base_url,
        "POST",
        "/order",
        {
            "menu_id": "menu-1",
            "order_id": "order-1",
            "customer_name": "John Smith",
            "customer_email": "foobar@gmail.com",
        },
    )
    assert posted["Message"].startswith("Hi John Smith, please choose one of these selection:")
    assert "3. Vegetable" in posted["Message"]

    status, choosing = call(base_url, "PUT", "/order/order-1", {"input": "1"})
    assert choosing["Message"].startswith("Which size do you want? 1. Slide")

    status, done = call(base_url, "PUT", "/order/order-1", {"input": "4"})
    assert done["Message"] == (
        "Your order costs $15.00. We will email you when the order is ready. Thank you!"
    )

    status, order = call(base_url, "GET", "/order/order-1")
    assert order["customer_email"] == "foobar@gmail.com"
    assert order["order_status"] == "processing"
    assert order["order"] == {
        "selection": "Cheese",
        "size": "Large",
        "costs": "15.00",
        "order_time": "05-15-2017@10:30:00",
    }

    status, _gone = call(base_url, "DELETE", "/menu/menu-1")
    assert status == 200
    status, missing = call(base_url, "GET", "/menu/menu-1")
    assert status == 500
    assert "error" in missing
