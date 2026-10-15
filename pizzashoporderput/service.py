from datetime import datetime

import boto3


def handler(event, context):
    client = boto3.client("dynamodb")
    item = client.get_item(TableName="pizzashoporder", Key={"order_id": {"S": event["order_id"]}})
    menu = client.get_item(
        TableName="pizzashopmenu",
        Key={"menu_id": {"S": item["Item"]["menu_id"]["S"]}},
    )
    choice = event["selection_number"] - 1
    if item["Item"]["order_status"]["S"] == "selecting":
        client.update_item(
            TableName="pizzashoporder",
            Key={"order_id": {"S": event["order_id"]}},
            UpdateExpression="SET ord.#o = :o",
            ExpressionAttributeNames={"#o": "selection"},
            ExpressionAttributeValues={":o": {"S": menu["Item"]["selection"]["L"][choice]["S"]}},
        )
        client.update_item(
            TableName="pizzashoporder",
            Key={"order_id": {"S": event["order_id"]}},
            UpdateExpression="SET #o = :o",
            ExpressionAttributeNames={"#o": "order_status"},
            ExpressionAttributeValues={":o": {"S": "ordering"}},
        )
        sizes = ", ".join(
            f"{index}. {size['S']}" for index, size in enumerate(menu["Item"]["size"]["L"], start=1)
        )
        return 200, "OK", {"Message": f"Which size do you want? {sizes}"}
    if item["Item"]["order_status"]["S"] == "ordering":
        client.update_item(
            TableName="pizzashoporder",
            Key={"order_id": {"S": event["order_id"]}},
            UpdateExpression="SET ord.#o = :o",
            ExpressionAttributeNames={"#o": "size"},
            ExpressionAttributeValues={":o": {"S": menu["Item"]["size"]["L"][choice]["S"]}},
        )
        client.update_item(
            TableName="pizzashoporder",
            Key={"order_id": {"S": event["order_id"]}},
            UpdateExpression="SET #o = :o",
            ExpressionAttributeNames={"#o": "order_status"},
            ExpressionAttributeValues={":o": {"S": "processing"}},
        )
        price = menu["Item"]["price"]["L"][choice]["N"]
        client.update_item(
            TableName="pizzashoporder",
            Key={"order_id": {"S": event["order_id"]}},
            UpdateExpression="SET ord.#o = :o",
            ExpressionAttributeNames={"#o": "costs"},
            ExpressionAttributeValues={":o": {"N": price}},
        )
        client.update_item(
            TableName="pizzashoporder",
            Key={"order_id": {"S": event["order_id"]}},
            UpdateExpression="SET ord.#o = :o",
            ExpressionAttributeNames={"#o": "order_time"},
            ExpressionAttributeValues={":o": {"S": datetime.now().strftime("%m-%d-%Y@%H:%M:%S")}},
        )
        message = (
            f"Your order costs ${price}. We will email you when the order is ready. Thank you!"
        )
        return 200, "OK", {"Message": message}


"""
Input:
{
"order_id":"$input.params('order-id')",
"selection_number": $input.path('$').input
}

"""
