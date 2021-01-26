#!/usr/bin/python3
import pandas as pd
import requests
import numpy as np
import os
from nsetools import Nse
from datetime import timezone
from datetime import date
from datetime import datetime,timedelta
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt



class stock_analsys:
    global_constants = {}
    #this tolerance is for verifying if the candle length and the candle body length are close....test for MARUBOZU
    global_constants['ratio_MARUBOZU'] = 0.9 
    global_constants['ratio_DOJI'] = 0.3
    global_constants['ratio_MEAN'] = 0.99
    global_constants['ratio_trend_REV'] = 3.
    global_constants['trend_days'] = 10
    global_constants['curve_fit_degree'] = 4
    global_out_dict = {}
    
    def __init__(self,symbs,delta_days=100):
        self.delta_days = delta_days
        self.stocks = []
        self.marubozu = []
        self.doji = []
        self.reversal = []
        self.symbs = symbs
        self.multi_stock()
    
    def single_stock(self,stock):
        self.stock_name = stock
        self.yahoo_fetch_history()
        self.dat = pd.read_csv('dat.csv')
        #self.process_data()
        self.find_trend()
    
    def multi_stock(self):
        for key in self.symbs:
            for stock in self.symbs[key]:
                self.MARUBOZU = 'FALSE'
                self.DOJI = 'FALSE'
                self.REVSERSAL = 'FALSE'
                self.stock_name = stock
                self.yahoo_fetch_history()
                self.dat = pd.read_csv('dat.csv')
                self.process_data()
                self.stocks.append(stock)
                self.marubozu.append(self.MARUBOZU)
                self.doji.append(self.DOJI)
                self.reversal.append(self.REVSERSAL)
        self.global_out_dict['STOCK'] = self.stocks
        self.global_out_dict['MARUBOZU'] = self.marubozu
        self.global_out_dict['DOJI'] = self.doji
        self.global_out_dict['TREND_REVERSAL'] = self.reversal
        self.df = pd.DataFrame(self.global_out_dict)
        self.df.to_csv(os.getcwd()+'/OUT.csv')
    
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
        now = 1
        ll['Open'] = (float(self.dat['Open'][len(self.dat)-now]))
        ll['High'] = (float(self.dat['High'][len(self.dat)-now]))
        ll['Low'] = (float(self.dat['Low'][len(self.dat)-now]))
        ll['Close'] = (float(self.dat['Close'][len(self.dat)-now]))
        ll['candle_len'] = float(ll['High']-ll['Low'])
        ll['open_close_diff'] = float(ll['Close']-ll['Open'])
        ll['body_len'] = abs(ll['open_close_diff'])
        ll['candle_mean'] = abs((ll['High']+ll['Low'])/2.)
        ll['body_mean'] = abs((ll['Open']+ll['Close'])/2.)
        ll['ratio_bodylen_cndlen'] = ll['body_len']/ll['candle_len']
        if(ll['open_close_diff']>0):#GAIN
            ll['upper_wick_len'] = ll['High']-ll['Close']
            ll['lower_wick_len'] = ll['Open']-ll['Low']
        else:#LOSS
            ll['upper_wick_len'] = ll['High']-ll['Open']
            ll['lower_wick_len'] = ll['Close']-ll['Low']
        dictt['now'] = ll
        self.analyze_candle(dictt)
    
    def process_data_all(self):
        self.dat['candle_len'] = (self.dat['High']-self.dat['Low']).to_list()
        self.dat['body_len'] = [abs(x) for x in (self.dat['Close']-self.dat['Open']).to_list()]

    def analyze_candle(self,dictt):
        #print(dictt)
        #print("Candle body = %f"%dictt['now']['body_len'])
        #print("Candle len = %f"%dictt['now']['candle_len'])
        #print("body mean = %f"%dictt['now']['body_mean'])
        #print("candle mean = %f"%dictt['now']['candle_mean'])
        #print("Upper wick len = %f"%dictt['now']['upper_wick_len'])
        #print("Lower wick len = %f"%dictt['now']['lower_wick_len'])
        #print("ratio_bodylen_cndlen = %f"%dictt['now']['ratio_bodylen_cndlen'])
        #print("ratio DOJI = %f"%self.global_constants['ratio_DOJI'])
        if(dictt['now']['ratio_bodylen_cndlen']>self.global_constants['ratio_MARUBOZU']):
            self.MARUBOZU = 'TRUE'
        if(dictt['now']['ratio_bodylen_cndlen']<self.global_constants['ratio_DOJI']):
            #if(dictt['now']['body_mean']/dictt['now']['candle_mean']>self.global_constants['ratio_MEAN']):
            if(dictt['now']['upper_wick_len']/dictt['now']['lower_wick_len']>self.global_constants['ratio_MEAN']):
                self.DOJI = 'TRUE'
            if((dictt['now']['upper_wick_len']/dictt['now']['lower_wick_len']>self.global_constants['ratio_trend_REV']) or (dictt['now']['lower_wick_len']/dictt['now']['upper_wick_len']>self.global_constants['ratio_trend_REV'])):
                self.REVSERSAL = 'TRUE'
    
    def find_trend(self):
        high_price = self.dat["High"].to_list()
        low_price = self.dat["Low"].to_list()
        high_price = high_price[-int(self.global_constants['trend_days']):-1]
        low_price = low_price[-int(self.global_constants['trend_days']):-1]
        mean_values = list(map(lambda x,y: (x+y)/2.,high_price,low_price))
        x_data = (np.linspace(0,10,len(high_price)))
        popt, _ = curve_fit(self.objective,x_data,mean_values)
        a, b, c, d, e, f = popt
        mean_fitted = self.objective(x_data,a,b,c,d,e,f)
        print(mean_fitted)
        plt.plot(x_data,mean_values,'o')
        plt.plot(x_data,mean_fitted,'-r')
        #plt.show()
        mean_func_left_intrvl = self.objective(x_data[0],a,b,c,d,e,f)
        mean_func_right_intrvl = self.objective(x_data[-1],a,b,c,d,e,f)
        mean_slope = (mean_func_right_intrvl-mean_func_left_intrvl)/self.global_constants['trend_days']
        print(mean_slope)
    
    def objective(self,x, a, b, c, d, e, f):
	    return (a * x) + (b * x**2) + (c * x**3) + (d * x**4) + (e * x**5) + f
    


stock_symbols = {}
#stock_symbols['NIFTY auto'] = pd.read_csv('ind_niftyautolist.csv')['Symbol'].to_list()
#stock_symbols['NIFTY bank'] = pd.read_csv('ind_niftybanklist.csv')['Symbol'].to_list()
#stock_symbols['NIFTY it'] = pd.read_csv('ind_niftyitlist.csv')['Symbol'].to_list()
#stock_symbols['NIFTY metal'] = pd.read_csv('ind_niftymetallist.csv')['Symbol'].to_list()
#stock_symbols['NIFTY pharma'] = pd.read_csv('ind_niftypharmalist.csv')['Symbol'].to_list()
#stock_symbols['NIFTY oilGas'] = pd.read_csv('ind_niftyoilgaslist.csv')['Symbol'].to_list()
cls_instance = stock_analsys(stock_symbols)
cls_instance.single_stock('TATAMOTORS')
#nse = Nse()
#ll = nse.get_index_list()
#ll = nse.get_index_quote("nifty it")




