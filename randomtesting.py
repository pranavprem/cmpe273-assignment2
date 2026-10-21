from datetime import datetime

# Scratch script from May 2017, used while figuring out store-hour parsing
# for pizzashoporderpost. "5pm" -> hour 17.

# if datetime.today().weekday() == 0:
#     day = "Mon"
# elif datetime.today().weekday() == 1:
#     day = "Tue"
# elif datetime.today().weekday() == 2:
#     day = "Wed"
# elif datetime.today().weekday() == 3:
#     day = "Thu"
# elif datetime.today().weekday() == 4:
#     day = "Fri"
# elif datetime.today().weekday() == 5:
#     day = "Sat"
# elif datetime.today().weekday() == 6:
#     day = "Sun"


def main():
    tes = "5pm"
    print(datetime.strptime(tes, "%I%p").strftime("%H"))


if __name__ == "__main__":
    main()
