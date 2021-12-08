# -*- coding: utf-8 -*-
"""
Created on Wed Dec  8 15:33:39 2021

@author: retok
"""

import pandas as pd
import os, sys
import datetime as dt

# # path setting for all the scripts
# sys.path.append(os.path.dirname(__file__))
# # path setting for all the data
# parent_path = os.path.join(os.path.dirname(os.path.dirname(__file__)))


now = dt.now()

current_time = now.strftime("%y-%m-%d")


parent_path = 'D://ComputerScience//S5//CSAI4SG//git//project'


traffic = pd.read_table(os.path.join(parent_path,'data','trafficCounts.csv'), sep = ';', encoding = 'utf-8')
parc = pd.read_table(os.path.join(parent_path,'data','parcLot.csv'), sep = ';', encoding = 'utf-8')


def change_date(date_string):
    sp = date_string.split('T')
    date = sp[0]
    y = int(date.split('-')[0])
    month = int(date.split('-')[1])
    d = int(date.split('-')[2])
    hour = sp[1].split('+')[0]
    h = int(hour.split(':')[0]) 
    m = int(hour.split(':')[1]) 
    
    if m != 0:
        m = 0
        if h == 23:
            h = 0
        else:
            h += 1
            
    return dt.datetime(y, month, d, h, m)


parc['date'] = parc['Publikationszeit'].apply(lambda x: change_date(x))   
traffic['date'] = traffic['DateTimeTo'].apply(lambda x: change_date(x))  
parc[['lat','lng']] = parc['geo_point_2d'].str.split(',', expand=True) 
traffic[['lat','lng']] = traffic['Geo Point'].str.split(',', expand=True) 
parc['utilization'] = parc['Anzahl frei'] / parc['Total Plätze']  











