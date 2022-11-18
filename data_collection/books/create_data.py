from pprint import pprint
import random
import itertools

# <time> <AM/PM>
time_hour = tuple(f"{i}時" for i in range(13))
time_minute = tuple(f"{i}分" for i in range(61))
AM_PM = ("午前", "午後")

# <month> <day> <year> , <weekday> <month> <day>
month = tuple(f"{i+1}月" for i in range(12))
day = tuple(f"{i+1}日" for i in range(31))
weekday = tuple(w+"曜日" for w in ("月", "火", "水", "木", "金", "土", "日"))
year = tuple(f"{i}年" for i in range(1980, 2021))

# product 
iter_time = itertools.product(AM_PM, time_hour, time_minute)
iter_month_day_weekday = itertools.product(month, day, weekday)
iter_year_month_day = itertools.product(year, month, day)

data = list(iter_time) + list(iter_month_day_weekday) + list(iter_year_month_day)
data = [' '.join(d) for d in data]
random.shuffle(data)
# pprint(data)

with open("./close_vocab.txt", "w") as f:
    f.writelines("\n".join(data))
