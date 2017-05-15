import boto3
from datetime import datetime

def handler(event, context):
    client = boto3.client("dynamodb")
    item = client.get_item(TableName="pizzashoporder", Key={"order_id":{"S":event["order_id"]}})
    menu = client.get_item(TableName="pizzashopmenu",
                           Key={"menu_id":{"S":item["Item"]["menu_id"]["S"]}})
    if item["Item"]["order_status"]["S"] == "selecting":
        response = "Which size do you want? "
        i = 1
        client.update_item(TableName="pizzashoporder",
                           Key={"order_id":{"S":event["order_id"]}},
                           UpdateExpression="SET ord.#o = :o",
                           ExpressionAttributeNames={"#o": "selection"},
                           ExpressionAttributeValues=
                           {":o": {"S":menu["Item"]["selection"]["L"][event["selection_number"]-1]["S"]}})
        client.update_item(TableName="pizzashoporder",
                           Key={"order_id":{"S":event["order_id"]}},
                           UpdateExpression="SET #o = :o",
                           ExpressionAttributeNames={"#o": "order_status"},
                           ExpressionAttributeValues=
                           {":o":{"S":"ordering"}})
        for item in menu["Item"]["size"]["L"]:
            response = response + str(i) + ". " + item["S"]
            if i < len(menu["Item"]["size"]["L"]):
                response = response + ", "
            i = i + 1
        return 200,"OK",dict({"Message":response})
    if item["Item"]["order_status"]["S"] == "ordering":
        response = "Your order costs $"
        i = 1
        client.update_item(TableName="pizzashoporder",
                           Key={"order_id":{"S":event["order_id"]}},
                           UpdateExpression="SET ord.#o = :o",
                           ExpressionAttributeNames={"#o": "size"},
                           ExpressionAttributeValues=
                           {":o": {"S":menu["Item"]["size"]["L"][event["selection_number"]-1]["S"]}})
        client.update_item(TableName="pizzashoporder",
                           Key={"order_id":{"S":event["order_id"]}},
                           UpdateExpression="SET #o = :o",
                           ExpressionAttributeNames={"#o": "order_status"},
                           ExpressionAttributeValues=
                           {":o":{"S":"processing"}})
        client.update_item(TableName="pizzashoporder",
                           Key={"order_id":{"S":event["order_id"]}},
                           UpdateExpression="SET ord.#o = :o",
                           ExpressionAttributeNames={"#o": "costs"},
                           ExpressionAttributeValues=
                           {":o": {"N":menu["Item"]["price"]["L"][event["selection_number"]-1]["N"]}})
        client.update_item(TableName="pizzashoporder",
                           Key={"order_id":{"S":event["order_id"]}},
                           UpdateExpression="SET ord.#o = :o",
                           ExpressionAttributeNames={"#o": "order_time"},
                           ExpressionAttributeValues=
                           {":o": {"S":datetime.now().strftime('%m-%d-%Y@%H:%M:%S')}})

        response = response + menu["Item"]["price"]["L"][event["selection_number"]-1]["N"] + ". We will email you when the order is ready. Thank you!"
        return 200,"OK",dict({"Message":response})



"""
Input:
{
"order_id":"$input.params('order-id')",
"selection_number": $input.path('$').input
}

"""