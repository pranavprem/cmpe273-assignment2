import boto3


def handler(event, context):
    # Your code goes here!
    client = boto3.client("dynamodb")
    response = client.get_item(TableName="pizzashopmenu", Key=event)
    store_hours = dict()
    store_hours["Mon"] = response["Item"]["store_hours"]["M"]["Mon"]["S"]
    store_hours["Tue"] = response["Item"]["store_hours"]["M"]["Tue"]["S"]
    store_hours["Wed"] = response["Item"]["store_hours"]["M"]["Wed"]["S"]
    store_hours["Thu"] = response["Item"]["store_hours"]["M"]["Thu"]["S"]
    store_hours["Fri"] = response["Item"]["store_hours"]["M"]["Fri"]["S"]
    store_hours["Sat"] = response["Item"]["store_hours"]["M"]["Sat"]["S"]
    store_hours["Sun"] = response["Item"]["store_hours"]["M"]["Sun"]["S"]
    # body mapping template: {"S": "$input.params('menu-id')"}
    response["Item"]["store_hours"] = store_hours
    return response
