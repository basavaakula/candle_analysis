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
    global_constants['trend_days'] = 20
    global_constants['curve_fit_poly_degree'] = 5
    global_constants['prev_trend_days'] = [4,8,11]
    global_out_dict = {}
    
    def __init__(self,symbs,delta_days=500):
        self.ff = 'poly10' 
        self.fitting_funcs = {'poly2':self.poly2,'poly3':self.poly3,'poly4':self.poly4,'poly5':self.poly5,'expo':self.expo,'poly6':self.poly6,'poly7':self.poly7,'poly8':self.poly8,'poly9':self.poly9,'poly10':self.poly10,'poly11':self.poly11,'poly12':self.poly12,'poly13':self.poly13,'sin_mix':self.sin_mix}
        self.delta_days = delta_days
        self.stocks = []
        self.marubozu = []
        self.doji = []
        self.reversal = []
        self.trend = {}
        for i in self.global_constants['prev_trend_days']:
            self.trend['TREND'+str(i)] = []
        self.symbs = symbs
        self.multi_stock()
    
    def single_stock(self,stock):
        self.stock_name = stock
        self.yahoo_fetch_history()
        self.process_data()
        self.find_trend()
    
    def multi_stock(self):
        self.TREND = {}
        for key in self.symbs:
            for stock in self.symbs[key]:
                self.MARUBOZU = 'FALSE'
                self.DOJI = 'FALSE'
                self.REVSERSAL = 'FALSE'
                for i in self.global_constants['prev_trend_days']:
                    self.TREND['TREND'+str(i)] = []
                
                self.stock_name = stock
                self.yahoo_fetch_history()
                #self.dat = pd.read_csv('dat.csv')
                self.process_data()
                self.find_trend()
                
                self.stocks.append(stock)
                self.marubozu.append(self.MARUBOZU)
                self.doji.append(self.DOJI)
                self.reversal.append(self.REVSERSAL)
                for i in self.global_constants['prev_trend_days']:
                    self.trend['TREND'+str(i)].extend(self.TREND['TREND'+str(i)])
        
        self.global_out_dict['STOCK'] = self.stocks
        self.global_out_dict['MARUBOZU'] = self.marubozu
        self.global_out_dict['DOJI'] = self.doji
        for i in self.global_constants['prev_trend_days']:
            self.global_out_dict['TREND'+str(i)] = self.trend['TREND'+str(i)]
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
        #reading into temp ff to remove "null" rows and then write back to dat.csv
        ff = pd.read_csv('dat.csv')
        ff = ff.dropna()
        ff.to_csv(os.getcwd()+'/dat.csv')
        self.dat = pd.read_csv('dat.csv')

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
    
    #https://machinelearningmastery.com/curve-fitting-with-python/ 
    def find_trend(self):
        #print(self.stock_name)
        high_price = self.dat["High"].to_list()
        low_price = self.dat["Low"].to_list()
        high_price = high_price[-int(self.global_constants['trend_days']):-1]
        low_price = low_price[-int(self.global_constants['trend_days']):-1]
        mean_values = list(map(lambda x,y: (x+y)/2.,high_price,low_price))
        x_data = np.arange(1,int(self.global_constants['trend_days']),1)
        if(len(mean_values)!=0):
            popt, _ = curve_fit(self.fitting_funcs[self.ff],x_data,mean_values)
            mean_fitted = self.fitting_funcs[self.ff](x_data,*popt)
            plt.plot(x_data,mean_values,'--b')
            plt.plot(x_data,mean_fitted,'-r')
            plt.show()
            for i in self.global_constants['prev_trend_days']:
                x_tick = self.global_constants['trend_days']-i
                mean_func_left_intrvl = self.fitting_funcs[self.ff](x_data[x_tick],*popt)
                mean_func_right_intrvl = self.fitting_funcs[self.ff](x_data[-1],*popt)
                mean_slope = (mean_func_right_intrvl-mean_func_left_intrvl)/i
                #print(mean_func_left_intrvl)
                #print(mean_func_right_intrvl)
                #print(mean_slope)
                if(mean_slope>0.0):
                    self.trend['TREND'+str(i)].append('BULLISH')
                else:
                    self.trend['TREND'+str(i)].append('BEARISH')
        else:
            for i in self.global_constants['prev_trend_days']:
                self.trend['TREND'+str(i)].append('UNKOWN')
    def sin_mix(self,x, a, b, c, d):
	    return a * np.sin(b - x) + c * x**2 + d 
    def expo(self,x, a, b, c):
	    return a * np.exp (-b * x) + c 
    def poly2(self,x, a, b, c):
	    return (a * x) + (b * x**2) + c
    def poly3(self,x, a, b, c, d):
	    return (a * x) + (b * x**2) + (c * x**3) + d
    def poly4(self,x, a, b, c, d, e):
	    return (a * x) + (b * x**2) + (c * x**3) + (d * x**4) + e
    def poly5(self,x, a, b, c, d, e, f):
	    return (a * x) + (b * x**2) + (c * x**3) + (d * x**4) + (e * x**5) + f
    def poly6(self,x, a, b, c, d, e, f,g):
	    return (a * x) + (b * x**2) + (c * x**3) + (d * x**4) + (e * x**5) + (f * x**6) + g 
    def poly7(self,x, a, b, c, d, e, f,g,h):
	    return (a * x) + (b * x**2) + (c * x**3) + (d * x**4) + (e * x**5) + (f * x**6) + (g * x**7) +h
    def poly8(self,x, a, b, c, d, e, f,g,h,i):
	    return (a * x) + (b * x**2) + (c * x**3) + (d * x**4) + (e * x**5) + (f * x**6) + (g * x**7) + (h * x**8) +i
    def poly9(self,x, a, b, c, d, e, f,g,h,i,j):
	    return (a * x) + (b * x**2) + (c * x**3) + (d * x**4) + (e * x**5) + (f * x**6) + (g * x**7) + (h * x**8) + (i * x**9) + j
    def poly10(self,x, a, b, c, d, e, f,g,h,i,j,k):
	    return (a * x) + (b * x**2) + (c * x**3) + (d * x**4) + (e * x**5) + (f * x**6) + (g * x**7) + (h * x**8) + (i * x**9) + (j * x**10) + k
    def poly11(self,x, a, b, c, d, e, f,g,h,i,j,k,l):
	    return (a * x) + (b * x**2) + (c * x**3) + (d * x**4) + (e * x**5) + (f * x**6) + (g * x**7) + (h * x**8) + (i * x**9) + (j * x**10) + (k * x**11) + l
    def poly12(self,x, a, b, c, d, e, f,g,h,i,j,k,l,m):
	    return (a * x) + (b * x**2) + (c * x**3) + (d * x**4) + (e * x**5) + (f * x**6) + (g * x**7) + (h * x**8) + (i * x**9) + (j * x**10) + (k * x**11) + (l * x**12) + m
    def poly13(self,x, a, b, c, d, e, f,g,h,i,j,k,l,m,n):
	    return (a * x) + (b * x**2) + (c * x**3) + (d * x**4) + (e * x**5) + (f * x**6) + (g * x**7) + (h * x**8) + (i * x**9) + (j * x**10) + (k * x**11) + (l * x**12) + (m * x**13) + n

stock_symbols = {}
stock_symbols['NIFTY auto'] = pd.read_csv('ind_niftyautolist.csv')['Symbol'].to_list()
stock_symbols['NIFTY bank'] = pd.read_csv('ind_niftybanklist.csv')['Symbol'].to_list()
stock_symbols['NIFTY it'] = pd.read_csv('ind_niftyitlist.csv')['Symbol'].to_list()
stock_symbols['NIFTY metal'] = pd.read_csv('ind_niftymetallist.csv')['Symbol'].to_list()
stock_symbols['NIFTY pharma'] = pd.read_csv('ind_niftypharmalist.csv')['Symbol'].to_list()
stock_symbols['NIFTY oilGas'] = pd.read_csv('ind_niftyoilgaslist.csv')['Symbol'].to_list()
cls_instance = stock_analsys(stock_symbols)
#cls_instance.single_stock('KOTAKBANK')
#cls_instance.single_stock('RELIANCE')
#nse = Nse()
#ll = nse.get_index_list()
#ll = nse.get_index_quote("nifty it")




