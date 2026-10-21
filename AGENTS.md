# Agent guide

Pizza ordering Lambdas from CMPE 273 (SJSU, spring 2017). Read the [README](README.md) for the API contract and the course context. This file is how to work on the code without changing what the assignment did.

## Architecture

One directory per Lambda. The handler is always `service.handler(event, context)` in that directory's `service.py`. Do not merge the functions into one service, and do not put shared imports in a package the handlers load. They were deployed as separate zip files; `local_server.py` loads each `service.py` by path so the names do not collide.

`local_server.py` is the 2026 local runner. It is not deployed. It recreates the API Gateway Velocity templates (still copied in the handler docstrings) and, unless `--aws` is set, serves DynamoDB with moto.

Tables:

- `pizzashopmenu`, partition key `menu_id` (S)
- `pizzashoporder`, partition key `order_id` (S)

The order blob lives in the attribute `ord`. `sequence` on a menu is always `selection`, then `size`, and is written by `pizzashopmenupost`, not by the client.

## Event shapes

Handlers do not all see the public HTTP body.

| Function | Event |
| --- | --- |
| `pizzashopmenupost` | Public menu JSON. Plain strings, not DynamoDB types. |
| `pizzashopmenuget`, `pizzashopmenudelete` | `{"menu_id": {"S": "<id>"}}` used as the DynamoDB key. |
| `pizzashopmenuput` | `{"menu_id": {"S": "<id>"}}`. Optional `selections` (plural) is a list of strings. The public JSON field is `selection`. Missing `selections` means "add Vegetable". |
| `pizzashoporderpost` | Public order JSON (`menu_id`, `order_id`, `customer_name`, `customer_email`). |
| `pizzashoporderput` | `{"order_id": "<id>", "selection_number": <int>}`. 1-based. |
| `pizzashoporderget` | `{"order_id": {"S": "<id>"}}`. |

`event.json` in each folder is that post-template payload, for reference. `hello-function/event.json` and `dynamoTest/event.json` are still the python-lambda placeholder `{"pi", "e"}`.

## Return values

These are not Lambda proxy responses, except `hello-function`, which returns `{statusCode, headers, body}`.

- Menu POST and DELETE: `(200, "OK")` or `(400, exception)`.
- Menu GET: the raw `get_item` response, with `store_hours` replaced by a list of `[day, hours]` pairs for the Velocity template.
- Menu PUT: `(body, 200, "OK")` on success, where `body` is `{menu_id, selection}`. Status is the second element. `(400, exception)` on failure.
- Order POST and PUT: `(200, "OK", {"Message": "..."})`.
- Order GET: a plain dict. `order` is a list of `[name, value]` pairs, not a dict. The local server turns that into the public object.

Keep those shapes. `interpret_result` in `local_server.py` is the translator.

## Commands

Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
ruff check .
ruff format .
python local_server.py --now 2017-05-15T10:30:00
python randomtesting.py
```

Pins live in `requirements.txt` (boto3, used by the handlers) and `requirements-dev.txt` (moto, pytest, ruff). CI is `.github/workflows/ci.yml`.

`--now` only affects the copies of the order handlers that `local_server.services()` has loaded. Tests that call `load_service` get a fresh module and must `freeze_module` themselves. May 15, 2017 was a Monday; May 6, 2017 was a Saturday. Both are used as frozen clocks in the tests.

## Conventions

- Match the existing handler style: a `handler`, boto3 low-level client, DynamoDB typed attributes. Do not switch the handlers to the resource API or to a web framework.
- Messages are part of the contract, including the grammar "one of these selection" and the word `costs` (not `cost`).
- Region defaults to `us-west-2` because that is what every `config.yaml` says. Handlers call `boto3.client("dynamodb")` with no region and inherit `AWS_DEFAULT_REGION`.
- Ruff formats and lints (E, F, I, UP). Line length 100. Do not add a second formatter.
- No license file. Do not add one.

## Gotchas

- Opening-hour check: `10am-10pm` must be open at 10:00. The 2017 code used `hour <= open_hour`, which closed the store for the entire opening hour. `closed_message` uses `hour < open_hour` and `hour >= close_hour`. Do not "restore" the old comparison.
- A missing weekday used to raise `KeyError` even though the function contained `Restaurant closed today`. It now returns that message. A malformed range still falls through to `(400, exception)`.
- Empty-body menu PUT adds `Vegetable` only when it is absent. A second empty PUT must not append it again. `list_append` of an empty list is skipped for the same reason.
- Hour parsing is `datetime.strptime(value, "%I%p")` on strings like `10am` and `10pm`. No space, no minutes. `12pm` is noon. Overnight windows do not work.
- `PUT /order` indexes the selection or size list with `selection_number - 1` and does not catch a bad index.
- Menu GET and order GET assume the item exists. A miss raises `KeyError`. The local server surfaces that as HTTP 500.
- `config.yaml` `aws_access_key_id` and `aws_secret_access_key` stay empty. Credentials come from the environment or `~/.aws/credentials`. Never commit keys, `.env`, or a virtualenv.
- Do not commit `pizzashopenv/`, `dist/`, `*.zip`, or `*.pyc`. Those were the original virtualenv, python-lambda build zips, and a binary, and they are gitignored now.
- `dynamoTest` reads a `Comments` table and prints the item or `something happened`. It is not part of the pizza API. `hello-function` is the python-lambda starter.

## What not to refactor

Leave the per-function layout, the `ord` attribute, the low-level DynamoDB types, the tuple return orders, and the assignment's sample data (including "Slide" and weekend `11am-12pm`). A cleaner single-app rewrite would no longer be this project.
