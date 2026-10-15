from datetime import datetime

import boto3
import pytest
from moto import mock_aws

from local_server import freeze_module, load_service
from tests.helpers import SAMPLE_MENU, SAMPLE_ORDER, create_table

MONDAY_OPEN = datetime(2017, 5, 15, 10, 30, 0)
MONDAY_AT_OPEN = datetime(2017, 5, 15, 10, 0, 0)
MONDAY_BEFORE = datetime(2017, 5, 15, 9, 0, 0)
MONDAY_AT_CLOSE = datetime(2017, 5, 15, 22, 0, 0)
SATURDAY_OPEN = datetime(2017, 5, 6, 11, 30, 0)
SATURDAY_CLOSED = datetime(2017, 5, 6, 12, 0, 0)


@pytest.fixture
def aws():
    with mock_aws():
        create_table("pizzashopmenu", "menu_id")
        create_table("pizzashoporder", "order_id")
        yield


def test_hello_lists_event_keys():
    hello = load_service("hello-function")
    result = hello.handler({"pi": 3.14, "e": 2.718}, None)
    assert result["statusCode"] == 200
    assert result["body"] == "pi,e,"


def test_dynamo_smoke_reads_comment(capsys):
    with mock_aws():
        client = create_table("Comments", "commentId")
        client.put_item(
            TableName="Comments",
            Item={"commentId": {"S": "test-invoke-request"}, "body": {"S": "hi"}},
        )
        dynamo = load_service("dynamoTest")
        assert dynamo.handler({}, None) is None
    captured = capsys.readouterr()
    assert "test-invoke-request" in captured.out


def test_menu_post_get_and_delete(aws):
    post = load_service("pizzashopmenupost")
    get = load_service("pizzashopmenuget")
    delete = load_service("pizzashopmenudelete")

    assert post.handler(SAMPLE_MENU, None) == (200, "OK")

    response = get.handler({"menu_id": {"S": "menu-1"}}, None)
    item = response["Item"]
    assert item["menu_id"] == {"S": "menu-1"}
    assert item["sequence"] == {"L": [{"S": "selection"}, {"S": "size"}]}
    assert item["price"]["L"][3] == {"N": "15.00"}
    assert ["Mon", "10am-10pm"] in item["store_hours"]
    assert item["store_hours"][0] == ["Mon", "10am-10pm"]

    assert delete.handler({"menu_id": {"S": "menu-1"}}, None) == (200, "OK")
    gone = boto3.client("dynamodb").get_item(
        TableName="pizzashopmenu", Key={"menu_id": {"S": "menu-1"}}
    )
    assert "Item" not in gone


def test_menu_post_rejects_incomplete_body(aws):
    post = load_service("pizzashopmenupost")
    status, error = post.handler({"menu_id": "x"}, None)
    assert status == 400
    assert isinstance(error, Exception)


def test_menu_put_adds_vegetable_once(aws):
    post = load_service("pizzashopmenupost")
    put = load_service("pizzashopmenuput")
    post.handler(SAMPLE_MENU, None)

    body, status, ok = put.handler({"menu_id": {"S": "menu-1"}}, None)
    assert (status, ok) == (200, "OK")
    assert body == {"menu_id": "menu-1", "selection": ["Cheese", "Pepperoni", "Vegetable"]}

    body, status, ok = put.handler({"menu_id": {"S": "menu-1"}}, None)
    assert status == 200
    assert body["selection"] == ["Cheese", "Pepperoni", "Vegetable"]

    body, status, ok = put.handler(
        {
            "menu_id": {"S": "menu-1"},
            "selections": ["Cheese", "Pepperoni", "Vegetable", "Mushroom"],
        },
        None,
    )
    assert body["selection"] == ["Cheese", "Pepperoni", "Vegetable", "Mushroom"]


def _order_modules(when):
    post = load_service("pizzashoporderpost")
    put = load_service("pizzashoporderput")
    get = load_service("pizzashoporderget")
    freeze_module(post, when)
    freeze_module(put, when)
    return post, put, get


def test_order_conversation(aws):
    menu = load_service("pizzashopmenupost")
    menu_put = load_service("pizzashopmenuput")
    menu.handler(SAMPLE_MENU, None)
    menu_put.handler({"menu_id": {"S": "menu-1"}}, None)
    post, put, get = _order_modules(MONDAY_OPEN)

    status, ok, payload = post.handler(SAMPLE_ORDER, None)
    assert (status, ok) == (200, "OK")
    assert payload["Message"] == (
        "Hi John Smith, please choose one of these selection: 1. Cheese, 2. Pepperoni, 3. Vegetable"
    )

    status, ok, payload = put.handler({"order_id": "order-1", "selection_number": 1}, None)
    assert payload["Message"] == (
        "Which size do you want? 1. Slide, 2. Small, 3. Medium, 4. Large, 5. X-Large"
    )

    status, ok, payload = put.handler({"order_id": "order-1", "selection_number": 4}, None)
    assert payload["Message"] == (
        "Your order costs $15.00. We will email you when the order is ready. Thank you!"
    )

    order = get.handler({"order_id": {"S": "order-1"}}, None)
    assert order["order_status"] == "processing"
    assert dict(order["order"]) == {
        "selection": "Cheese",
        "size": "Large",
        "costs": "15.00",
        "order_time": "05-15-2017@10:30:00",
    }


@pytest.mark.parametrize(
    ("when", "expected"),
    [
        (MONDAY_AT_OPEN, None),
        (MONDAY_OPEN, None),
        (MONDAY_BEFORE, "Restaurant is now closed"),
        (MONDAY_AT_CLOSE, "Restaurant is now closed"),
        (SATURDAY_OPEN, None),
        (SATURDAY_CLOSED, "Restaurant is now closed"),
    ],
)
def test_store_hours(aws, when, expected):
    menu = load_service("pizzashopmenupost")
    menu.handler(SAMPLE_MENU, None)
    post, _put, _get = _order_modules(when)
    _status, _ok, payload = post.handler(SAMPLE_ORDER, None)
    if expected is None:
        assert "please choose one of these selection" in payload["Message"]
    else:
        assert payload["Message"] == expected
        stored = boto3.client("dynamodb").get_item(
            TableName="pizzashoporder", Key={"order_id": {"S": "order-1"}}
        )
        assert "Item" not in stored


def test_store_closed_all_day_when_weekday_missing(aws):
    menu = load_service("pizzashopmenupost")
    hours = dict(SAMPLE_MENU)
    hours["store_hours"] = {"Tue": "10am-10pm"}
    menu.handler(hours, None)
    post, _put, _get = _order_modules(MONDAY_OPEN)
    _status, _ok, payload = post.handler(SAMPLE_ORDER, None)
    assert payload["Message"] == "Restaurant closed today"
