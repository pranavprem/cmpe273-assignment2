import boto3
import json
from datetime import datetime

def makeformat(list, varname):
    return [dict({varname:item}) for item in list]

def handler(event, context):
    # Your code goes here!
    client = boto3.client("dynamodb")
    try:
        menu = client.get_item(TableName="pizzashopmenu", Key={"menu_id":{"S":event["menu_id"]}})
        if datetime.today().weekday() == 0:
            day = "Mon"
        elif datetime.today().weekday() == 1:
            day = "Tue"
        elif datetime.today().weekday() == 2:
            day = "Wed"
        elif datetime.today().weekday() == 3:
            day = "Thu"
        elif datetime.today().weekday() == 4:
            day = "Fri"
        elif datetime.today().weekday() == 5:
            day = "Sat"
        elif datetime.today().weekday() == 6:
            day = "Sun"

        if menu["Item"]["store_hours"]["M"][day] is not None:
            hours = menu["Item"]["store_hours"]["M"][day]["S"].split("-")
        else:
            return 200, "OK", {"Message":"Restaurant closed today"}

        open_time = datetime.strptime(hours[0], "%I%p").strftime("%H")
        close_time = datetime.strptime(hours[1], "%I%p").strftime("%H")
        now_time = datetime.now().strftime('%H')
        if int(now_time) <= int(open_time) and int(now_time) >= int(close_time):
            return 200, "OK", {"Message":"Restaurant is now closed"}
        else:
            client.put_item(TableName="pizzashoporder",
                            Item={"order_id":{"S":event["order_id"]},
                                  "menu_id":{"S":event["menu_id"]},
                                  "customer_name":{"S":event["customer_name"]},
                                  "customer_email":{"S":event["customer_email"]},
                                  "order_status":{"S":"selecting"},
                                  "ord":{"M":{}}})

            response = "Hi "+event["customer_name"]+", please choose one of these selection: "
            i = 1
            for item in menu["Item"]["selection"]["L"]:
                response = response + str(i) + ". " + item["S"]
                if i < len(menu["Item"]["selection"]["L"]):
                    response = response + ", "
                i = i + 1
    except Exception, e:
        return 400, e
    return 200, "OK", {"Message":response}
