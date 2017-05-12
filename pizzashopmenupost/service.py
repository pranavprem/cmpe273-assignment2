import boto3
import json

def makeformat(list, varname):
    return [dict({varname:item}) for item in list]

def handler(event, context):
    # Your code goes here!
    client = boto3.client("dynamodb")

    store_hours={}
    for item in event["store_hours"]:
        it=dict()
        it["S"] = event["store_hours"][item]
        store_hours[item] = it
    
    try:
        client.put_item(TableName="pizzashopmenu",
                        Item={"menu_id":{"S":event["menu_id"]},
                              "store_name": {"S":event["store_name"]},
                              "selection":{"L": makeformat(event["selection"], "S")},
                              "size":{"L":makeformat(event["size"], "S")},
                              "price":{"L":makeformat(event["price"], "N")},
                              "store_hours":{"M":store_hours},
                              "sequence":{"L":[{"S":"selection"}, {"S":"size"}]}})
    except Exception,e:
        return 400, e
    return 200, "OK"