import boto3

def handler(event, context):
    client = boto3.client("dynamodb")
    try:
        client.delete_item(TableName="pizzashopmenu", Key=event)
    except Exception, e:
        return 400, e
    return 200, "OK"


""" body mapping templates: 
 input:
{"menu_id":{"S": "$input.params('menu-id')"}}
"""
