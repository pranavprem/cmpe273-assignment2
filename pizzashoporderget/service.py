import boto3


def handler(event, context):
    # Your code goes here!
    client = boto3.client("dynamodb")
    item = client.get_item(TableName="pizzashoporder", Key=event)
    response = dict()
    response["menu_id"] = item["Item"]["menu_id"]["S"]
    response["order_id"] = item["Item"]["order_id"]["S"]
    response["customer_name"] = item["Item"]["customer_name"]["S"]
    response["customer_email"] = item["Item"]["customer_email"]["S"]
    response["order_status"] = item["Item"]["order_status"]["S"]
    response["order"] = []
    for it in item["Item"]["ord"]["M"]:
        if it == "costs":
            response["order"].append([it, item["Item"]["ord"]["M"][it]["N"]])
        else:
            response["order"].append([it, item["Item"]["ord"]["M"][it]["S"]])
    return response



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