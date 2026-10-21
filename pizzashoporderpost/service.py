from datetime import datetime

import boto3

DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def closed_message(store_hours, now):
    """Return a closed message, or None when the store is open.

    Hours are compared at hour resolution. "10am-10pm" is open from 10:00
    inclusive until 22:00 exclusive. The original check used `<=` on the
    opening hour, so the store was closed for that entire hour (10:30 counted
    as closed). A missing weekday is "closed today"; the old code raised
    KeyError and the message below was unreachable.
    """
    today = store_hours.get(DAYS[now.weekday()])
    if today is None:
        return "Restaurant closed today"
    window = today["S"].split("-")
    open_hour = int(datetime.strptime(window[0], "%I%p").strftime("%H"))
    close_hour = int(datetime.strptime(window[1], "%I%p").strftime("%H"))
    current_hour = int(now.strftime("%H"))
    if current_hour < open_hour or current_hour >= close_hour:
        return "Restaurant is now closed"
    return None


def handler(event, context):
    client = boto3.client("dynamodb")
    try:
        menu = client.get_item(TableName="pizzashopmenu", Key={"menu_id": {"S": event["menu_id"]}})
        closed = closed_message(menu["Item"]["store_hours"]["M"], datetime.now())
        if closed:
            return 200, "OK", {"Message": closed}

        client.put_item(
            TableName="pizzashoporder",
            Item={
                "order_id": {"S": event["order_id"]},
                "menu_id": {"S": event["menu_id"]},
                "customer_name": {"S": event["customer_name"]},
                "customer_email": {"S": event["customer_email"]},
                "order_status": {"S": "selecting"},
                "ord": {"M": {}},
            },
        )

        choices = ", ".join(
            f"{index}. {item['S']}"
            for index, item in enumerate(menu["Item"]["selection"]["L"], start=1)
        )
        response = f"Hi {event['customer_name']}, please choose one of these selection: {choices}"
    except Exception as e:
        return 400, e
    return 200, "OK", {"Message": response}
