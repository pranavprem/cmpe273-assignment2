import boto3


def handler(event, context):
    # Your code goes here!
    client = boto3.client("dynamodb")
    
    try:
        client.update_item(TableName="pizzashopmenu", Key=event, UpdateExpression="SET #sel = list_append(#sel, :val1)",ExpressionAttributeNames={"#sel": "selection"}, ExpressionAttributeValues={":val1":{"L":[{"S":"Vegetable"}]}})
        item = client.get_item(TableName="pizzashopmenu", Key=event)
        response = {}
        response ["menu_id"] = item["Item"]["menu_id"]["S"]
        response ["selection"] = [select["S"] for select in item["Item"]["selection"]["L"]]
    except Exception,e:
        return 400, e
    return response, 200, "OK"

""" body mapping templates: 
 input:
{"menu_id":{"S": "$input.params('menu-id')"}}
"""