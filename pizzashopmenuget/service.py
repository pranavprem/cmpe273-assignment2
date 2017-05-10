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
    response["Item"]["store_hours"] = store_hours
    return response



""" body mapping templates: 
 input:
{"menu_id":{"S": "$input.params('menu-id')"}}

output:
#set($inputRoot = $input.path('$'))
{
    "menu_id": "$inputRoot.Item.menu_id.S",
    "store_name": "$inputRoot.Item.store_name.S",
    "selection": [
		#foreach($elem in $inputRoot.Item.selection.L)"$elem.S"#if($foreach.hasNext),#end#end
    ],
    "size": [
	    #foreach($elem in $inputRoot.Item.size.L)"$elem.S"#if($foreach.hasNext),#end#end
	    ],
    "price": [
	    #foreach($elem in $inputRoot.Item.price.L)"$elem.N"#if($foreach.hasNext),#end#end
    ],
    "store_hours":{
    	$inputRoot.Item.store_hours
    }
}
"""