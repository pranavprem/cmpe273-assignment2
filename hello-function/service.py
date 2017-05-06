def handler(event, context):
    # Your code goes here!
    # e = event.get("queryStringParameters").get('e')
    # pi = event.get("queryStringParameters").get('pi')
    keys=""
    for test in event.keys():
	keys=keys+test+"," 
    return {
        "statusCode": 200,
        "headers": { "Content-Type": "application/json"},
        "body": keys
    }
