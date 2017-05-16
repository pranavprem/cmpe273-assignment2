import boto3


def handler(event, context):
    # Your code goes here!
    client = boto3.client("dynamodb")

    try:
        new_options = []
        keys_in_event = [keys for keys in event]
        if "selections" not in keys_in_event:
            new_options.append(dict({"S":"Vegetable"}))
        else:
            menu = client.get_item(TableName="pizzashopmenu",
                                   Key={"menu_id":event["menu_id"]})
            selection = menu["Item"]["selection"]["L"]
            current_options = []
            for select in selection:
                current_options.append(select["S"])
            for select in event["selections"]:
                if select not in current_options:
                    new_options.append(dict({"S":select}))
        client.update_item(TableName="pizzashopmenu", Key={"menu_id":event["menu_id"]},
                           UpdateExpression="SET #sel = list_append(#sel, :val1)",
                           ExpressionAttributeNames={"#sel": "selection"},
                           ExpressionAttributeValues={":val1":{"L":new_options}})
        item = client.get_item(TableName="pizzashopmenu", Key={"menu_id":event["menu_id"]})
        response = {}
        response["menu_id"] = item["Item"]["menu_id"]["S"]
        response["selection"] = [select["S"] for select in item["Item"]["selection"]["L"]]
    except Exception, e:
        return 400, e
    return response, 200, "OK"

"""
body mapping templates: 
 input:
#set($inputRoot = $input.path('$'))
{"menu_id":{"S": "$input.params('menu-id')"},
"selections":$inputRoot.selection}
"""