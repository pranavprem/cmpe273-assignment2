import boto3


def handler(event, context):
    client = boto3.client("dynamodb")
    item = client.get_item(TableName="pizzashoporder", Key=event)
    order_item = item["Item"]
    order = []
    for name, value in order_item["ord"]["M"].items():
        if name == "costs":
            order.append([name, value["N"]])
        else:
            order.append([name, value["S"]])
    return {
        "menu_id": order_item["menu_id"]["S"],
        "order_id": order_item["order_id"]["S"],
        "customer_name": order_item["customer_name"]["S"],
        "customer_email": order_item["customer_email"]["S"],
        "order_status": order_item["order_status"]["S"],
        "order": order,
    }


""" body mapping templates:
 input:
{"order_id":{"S": "$input.params('order-id')"}}

output:
#set($inputRoot = $input.path('$'))
{
    "menu_id": "$inputRoot.menu_id",
    "order_id": "$inputRoot.order_id",
    "customer_name": "$inputRoot.customer_name",
    "customer_email": "$inputRoot.customer_email",
    "order_status": "$inputRoot.order_status",
    "order":{
        #foreach($elem in $inputRoot.order)
            #foreach($el in $elem)"$el"#if($foreach.hasNext):#end#end#if($foreach.hasNext),#end

    #end}
}

"""
