#!/usr/bin/python3
import pandas as pd
import requests
import os
from nsetools import Nse
from datetime import timezone
from datetime import date
from datetime import datetime,timedelta


class stock_analsys:
    global_tolerances = {}
    global_tolerances['ratio_MARUBOZU'] = 0.9 
    #this tolerance is for verifying if the candle length and the candle body length are close....test for MARUBOZU
    global_tolerances['ratio_DOJI'] = 0.3
    global_tolerances['ratio_MEAN'] = 0.99
    
    def __init__(self,delta_days,stock_name):
        self.delta_days = delta_days 
        self.stock_name = stock_name
        self.yahoo_fetch_history()
        self.dat = pd.read_csv('dat.csv')
        self.process_data()
    
    def yahoo_fetch_history(self):
        now = datetime.now()
        past = now - timedelta(days = self.delta_days) 
        period1 = int(datetime.timestamp(past))
        period2 = int(datetime.timestamp(now))
        url = 'https://query1.finance.yahoo.com/v7/finance/download/'+self.stock_name+'.NS'
        url += '?period1='+str(period1)+'&period2='+str(period2)+'&interval=1d&events=history&includeAdjustedClose=true'
        r = requests.get(url, allow_redirects=False)
        with open(os.getcwd()+'/dat.csv', 'wb') as f:f.write(r.content)

    def process_data(self):
        dictt = {}
        ll = {}
        now = 2
        ll['Open'] = (float(self.dat['Open'][len(self.dat)-now]))
        ll['High'] = (float(self.dat['High'][len(self.dat)-now]))
        ll['Low'] = (float(self.dat['Low'][len(self.dat)-now]))
        ll['Close'] = (float(self.dat['Close'][len(self.dat)-now]))
        ll['candle_len'] = float(ll['High']-ll['Low'])
        ll['open_close_diff'] = float(ll['Close']-ll['Open'])
        ll['candle_body'] = abs(ll['open_close_diff'])
        ll['candle_mean'] = abs((ll['High']+ll['Low'])/2.)
        ll['body_mean'] = abs((ll['Open']+ll['Close'])/2.)
        ll['ratio_bodylen_cndlen'] = ll['candle_body']/ll['candle_len']
        dictt['now'] = ll
        self.single_day_candles(dictt)

    def single_day_candles(self,dictt):
        print(dictt)
        if(dictt['now']['open_close_diff']<0.0):
            print("LOSS = %f"%dictt['now']['open_close_diff'])
        else:
            print("PROFIT = %f"%dictt['now']['open_close_diff'])
        print("Candle body = %f"%dictt['now']['candle_body'])
        print("Candle len = %f"%dictt['now']['candle_len'])
        print("body mean = %f"%dictt['now']['body_mean'])
        print("candle mean = %f"%dictt['now']['candle_mean'])
        print("")
        if(dictt['now']['ratio_bodylen_cndlen']>self.global_tolerances['ratio_MARUBOZU']):
            print("Moribozu")
        if(dictt['now']['ratio_bodylen_cndlen']>self.global_tolerances['ratio_DOJI']):
            if(dictt['now']['body_mean']/dictt['now']['candle_mean']>self.global_tolerances['ratio_MEAN']):
                print("DOJI")
    


stock_name = "TATAMOTORS"
cls_instance = stock_analsys(10,stock_name)
#nse = Nse()




