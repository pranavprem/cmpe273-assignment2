import boto3


def handler(event, context):
    # Your code goes here!
    client = boto3.client("dynamodb")
    response = client.get_item(TableName="pizzashopmenu", Key=event)
    store_hours = []
    for item in response["Item"]["store_hours"]["M"]:
        store_hours.append([item, response["Item"]["store_hours"]["M"][item]["S"]])
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
	#foreach($elem in $inputRoot.Item.selection.L)"$elem.S"#if($foreach.hasNext),#end
	
        #end],
    "size": [
	#foreach($elem in $inputRoot.Item.size.L)"$elem.S"#if($foreach.hasNext),#end#end],
    "sequence": [
	#foreach($elem in $inputRoot.Item.sequence.L)
	        "$elem.S"#if($foreach.hasNext),#end
	    
	    #end

    ],
    "price": [
	    #foreach($elem in $inputRoot.Item.price.L)"$elem.N"#if($foreach.hasNext),#end#end
    
    ],
    "store_hours":{
    	#foreach($elem in $inputRoot.Item.store_hours)
    	    #foreach($el in $elem)"$el"#if($foreach.hasNext):#end#end#if($foreach.hasNext),#end

    #end}
}
"""