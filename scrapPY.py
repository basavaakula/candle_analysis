#!/usr/bin/python3

import pandas as pd
import requests
import os
from nsetools import Nse
from datetime import timezone
from datetime import date
from datetime import datetime,timedelta


def yahoo_fetch_history(num_days,stock):
    now = datetime.now()
    past = now - num_days
    period1 = int(datetime.timestamp(past))
    period2 = int(datetime.timestamp(now))
    url = 'https://query1.finance.yahoo.com/v7/finance/download/'+stock+'.NS'
    url += '?period1='+str(period1)+'&period2='+str(period2)+'&interval=1d&events=history&includeAdjustedClose=true'
    r = requests.get(url, allow_redirects=False)
    with open(os.getcwd()+'/dat.csv', 'wb') as f:f.write(r.content)

def process_data(dat):
    dictt = {}
    ll = {}
    ll['Open'] = (float(dat['Open'][len(dat)-1]))
    ll['High'] = (float(dat['High'][len(dat)-1]))
    ll['Low'] = (float(dat['Low'][len(dat)-1]))
    ll['Close'] = (float(dat['Close'][len(dat)-1]))
    ll['candle_len'] = float(ll['High']-ll['Low'])
    ll['open_close_diff'] = float(ll['Close']-ll['Open'])
    ll['candle_body'] = abs(ll['open_close_diff'])
    dictt['now'] = ll
    single_day_candles(dictt)

def single_day_candles(dictt):
    print(dictt)
    if(dictt['now']['open_close_diff']<0.0):
        print("LOSS = %f"%dictt['now']['open_close_diff'])
    else:
        print("PROFIT = %f"%dictt['now']['open_close_diff'])
    print("Candle body = %f"%dictt['now']['candle_body'])
    print("Candle len = %f"%dictt['now']['candle_len'])
    if(dictt['now']['candle_body']/dictt['now']['candle_len']>.95):
        print("Moribozu")
    


num_days = timedelta(days = 5)
nse = Nse()
yahoo_fetch_history(num_days,'RELIANCE')
dat = pd.read_csv('dat.csv')
process_data(dat)

yahoo_fetch_history(num_days,'INFY')
dat = pd.read_csv('dat.csv')
process_data(dat)



