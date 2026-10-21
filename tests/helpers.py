import boto3

SAMPLE_MENU = {
    "menu_id": "menu-1",
    "store_name": "Pizza Hut",
    "selection": ["Cheese", "Pepperoni"],
    "size": ["Slide", "Small", "Medium", "Large", "X-Large"],
    "price": ["3.50", "7.00", "10.00", "15.00", "20.00"],
    "store_hours": {
        "Mon": "10am-10pm",
        "Tue": "10am-10pm",
        "Wed": "10am-10pm",
        "Thu": "10am-10pm",
        "Fri": "10am-10pm",
        "Sat": "11am-12pm",
        "Sun": "11am-12pm",
    },
}

SAMPLE_ORDER = {
    "menu_id": "menu-1",
    "order_id": "order-1",
    "customer_name": "John Smith",
    "customer_email": "foobar@gmail.com",
}


def create_table(name, key):
    client = boto3.client("dynamodb")
    client.create_table(
        TableName=name,
        KeySchema=[{"AttributeName": key, "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": key, "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    return client
