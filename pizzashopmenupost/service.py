import boto3


def makeformat(items, varname):
    return [{varname: item} for item in items]


def handler(event, context):
    client = boto3.client("dynamodb")
    try:
        store_hours = {}
        for item in event["store_hours"]:
            store_hours[item] = {"S": event["store_hours"][item]}

        client.put_item(
            TableName="pizzashopmenu",
            Item={
                "menu_id": {"S": event["menu_id"]},
                "store_name": {"S": event["store_name"]},
                "selection": {"L": makeformat(event["selection"], "S")},
                "size": {"L": makeformat(event["size"], "S")},
                "price": {"L": makeformat(event["price"], "N")},
                "store_hours": {"M": store_hours},
                "sequence": {"L": [{"S": "selection"}, {"S": "size"}]},
            },
        )
    except Exception as e:
        return 400, e
    return 200, "OK"
