import boto3


def handler(event, context):
    client = boto3.client("dynamodb")

    try:
        menu = client.get_item(TableName="pizzashopmenu", Key={"menu_id": event["menu_id"]})
        current_options = [select["S"] for select in menu["Item"]["selection"]["L"]]
        # An empty body (no "selections" key) means "add Vegetable".
        # The API Gateway template named the field "selections"; the public
        # JSON field is "selection".
        incoming = event["selections"] if "selections" in event else ["Vegetable"]
        new_options = [{"S": select} for select in incoming if select not in current_options]
        if new_options:
            client.update_item(
                TableName="pizzashopmenu",
                Key={"menu_id": event["menu_id"]},
                UpdateExpression="SET #sel = list_append(#sel, :val1)",
                ExpressionAttributeNames={"#sel": "selection"},
                ExpressionAttributeValues={":val1": {"L": new_options}},
            )
        item = client.get_item(TableName="pizzashopmenu", Key={"menu_id": event["menu_id"]})
        response = {
            "menu_id": item["Item"]["menu_id"]["S"],
            "selection": [select["S"] for select in item["Item"]["selection"]["L"]],
        }
    except Exception as e:
        return 400, e
    return response, 200, "OK"


"""
body mapping templates:
 input:
#set($inputRoot = $input.path('$'))
{"menu_id":{"S": "$input.params('menu-id')"},
"selections":$inputRoot.selection}
"""
