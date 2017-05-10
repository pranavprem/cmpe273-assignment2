import boto3


def handler(event, context):
    # Your code goes here!
    client = boto3.client("dynamodb")
    
    try:
        
        client.update_item(TableName="pizzashopmenu", Key=event, UpdateExpression="SET #sel = list_append(#sel, :val1)",ExpressionAttributeNames={"#sel": "selection"}, ExpressionAttributeValues={":val1":{"L":[{"S":"Vegetable"}]}})
    except Exception,e:
        return 400, e
    return 200,"OK"
