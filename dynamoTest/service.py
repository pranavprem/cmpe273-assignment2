import boto3

def handler(event, context):
    client = boto3.client('dynamodb')
    try:
        print client.get_item(TableName='Comments', Key={'commentId':{'S':'test-invoke-request'}})
    except Exception:
        print "something happened"
