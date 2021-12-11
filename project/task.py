# -*- coding: utf-8 -*-
"""
Created on Wed Dec  8 15:33:39 2021

@author: retok
"""

import pandas as pd               # a data.frame handler like R
import folium                     # displaying maps
from folium.plugins import BeautifyIcon
import os, sys
import matplotlib.pyplot as plt

import osmnx as ox                # connection to OpenStreetMap
from selenium import webdriver    # for rendering in browser to save as .png
import datetime as dt
import math
import PIL as pil                 # for saving gifs

import time


""" functions
"""
def change_date(date_string):
    sp = date_string.split('T')
    date = sp[0]
    y = int(date.split('-')[0])
    month = int(date.split('-')[1])
    d = int(date.split('-')[2])
    hour = sp[1].split('+')[0]
    h = int(hour.split(':')[0]) 
    m = int(hour.split(':')[1]) 
    
    if 30 < m <= 59:
        m = 0
        if h == 23:
            h = 0
        else:
            h += 1
    else:
        m = 0               
            
    return dt.datetime(y, month, d, h, m)

def change_site_name(site_name):
    sp = site_name.split(' ',1)
    return sp[1]

def plot_dot_park(row, color, map_obj):
    #radius = row.PW / maxPW * 10
    folium.Circle(location=[row.lat, row.lng],radius=30, color = color,
                        fill=True, fillcolor = color, fill_opacity =1, 
                        tooltip=row['name'] +': Total ' + str(row['Total Plätze']) 
                        + ' Plätze'
                        ).add_to(map_obj)

def plot_dot_traffic(row, color, map_obj):
    #radius = row.PW / maxPW * 10
    folium.Circle(location=[row.lat, row.lng],radius=30, color = color,
                        fill=True, fillcolor = color, fill_opacity =1, 
                        tooltip=row['name'] +': '  + str(int(row['average']))
                        + ' cars on average per hour 2019'
                        ).add_to(map_obj)

def plot_park_cluster(cord, color, map_obj):
    folium.Circle(location=cord, radius=450, fill_color = color,
                  fill=True, color='grey', weight=1, fill_opacity=0.4).add_to(map_obj)
    
def plot_arrow(cord, angle, color, map_obj):
    icon_arrow = BeautifyIcon(
        icon=' fa fa-angle-double-down',
        inner_icon_style="""font-size:9rem;transform: rotate({0}deg);
                    color:{1};opacity:0.6;""".format(angle, color),
        background_color='transparent',
        border_color='transparent',
    )
    
    # add arrow
    folium.Marker(location=cord, icon=icon_arrow).add_to(map_obj)
        
# coordinate
# coordinate
basel = [47.55777131440573, 7.5918295281706865]  # basel
inter_tokb = [47.55866679121571, 7.592048476255378] # arrow to kleinbasel
inter_togb = [47.56118158101615, 7.588564901186044] # arrow to kleinbasel
kb_in = [47.57118487571712, 7.600878933966805] # kleinbasel in
kb_out = [47.56659343678, 7.605334669686331] # kleinbasel out
gb_west_in = [47.55522242670782, 7.576898975372455] # gb in form west
gb_west_out = [47.559049484406906, 7.5799774835732645] # gb out to west
gb_est_in = [47.55380087693972, 7.595126984456187] # gb in form est
gb_est_out = [47.549809396450826, 7.593506716982079] # gb out to est
kb = [47.563625981205035, 7.597494837472192]  # kleinbasel
gb = [47.551745406132355, 7.5874981679309625] # grossbasel

# arrow list incldugin the angle of arrow
arrows = [(inter_togb, 40), (inter_tokb, 220), (kb_in, 30), (kb_out,265), 
          (gb_west_in, 290), (gb_west_out,140), (gb_est_in, 100), 
          (gb_est_out, -55)]
# cluster list
clusters = [kb,gb]
    
def plotter(map_obj):
    for cord, angle in arrows:
        
        # call color function
        
        plot_arrow(cord, angle, 'red', map_obj)
    
    for cord in clusters:
        plot_park_cluster(cord, 'blue', map_obj)
    


# # path setting for all the scripts
# sys.path.append(os.path.dirname(__file__))
# # path setting for all the data
# parent_path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
parent_path = 'D://ComputerScience//S5//CSAI4SG//git//project'

# load the date
traffic_raw = pd.read_table(os.path.join(parent_path,'data','trafficCounts.csv'), sep = ';', encoding = 'utf-8')
park_raw = pd.read_table(os.path.join(parent_path,'data','parcLot.csv'), sep = ';', encoding = 'utf-8')

# load cluster mapping
traffic_cluster = pd.read_table(os.path.join(parent_path,'data','traffic_cluster.csv'), sep = ';', encoding = 'utf-8')
park_cluster = pd.read_table(os.path.join(parent_path,'data','park_cluster.csv'), sep = ';', encoding = 'utf-8')

""" scrip
"""

traffic = traffic_raw.copy()
park = park_raw.copy()

# drop those from germany and frances
traffic = traffic[traffic['SiteCode'] < 1000]  # SiteCode are integers

# rename geoPoint columns to match in both dataset
traffic.rename(columns={'Geo Point': 'geoPoint'}, inplace = True)
park.rename(columns={'geo_point_2d': 'geoPoint'}, inplace = True)

# rename the name of the side as we use this in visualization
park.rename(columns={'Name': 'name'}, inplace = True)

# work the row entries for data and geo coordinate
# python datetime format
park['date'] = park['Publikationszeit'].apply(lambda x: change_date(x))   
traffic['date'] = traffic['DateTimeTo'].apply(lambda x: change_date(x))  

# geopoints
park[['lat','lng']] = park['geoPoint'].str.split(',', expand=True) 
traffic[['lat','lng']] = traffic['geoPoint'].str.split(',', expand=True) 

# names for traffic site
traffic['name'] = traffic['SiteName'].apply(lambda x: change_site_name(x)) 

# utilization
park['utilization'] = (park['Total Plätze'] - park['Anzahl frei']) / park['Total Plätze']  

# average counts over 2019 per day
# select 2019 data
df2019 = traffic[traffic['date'].dt.year == 2019]
# average over PW group by site
df2019_avg = pd.DataFrame(df2019.groupby('name')['PW'].mean())
df2019_avg.rename(columns={'PW' : 'average'}, inplace=True)
# merge that to traffic
traffic = traffic.merge(df2019_avg, left_on = 'name', right_on = 'name', 
                     how = 'left').set_axis(traffic.index) 

# add clustering to data
traffic = traffic.merge(traffic_cluster[['geoPoint','DirectionName','cluster']], 
                    left_on = ['geoPoint','DirectionName'], right_on = ['geoPoint','DirectionName'], 
                     how = 'left').set_axis(traffic.index)
park = park.merge(park_cluster[['geoPoint','cluster']], left_on = 'geoPoint', right_on = 'geoPoint', 
                     how = 'left').set_axis(park.index) 


# html for overview:
# - - - - - - - - -
# select unique ge koordinates
u_traffic = traffic[['lat','lng','name', 'average']].drop_duplicates()
u_park = park[['lat','lng','name','Total Plätze']].drop_duplicates()


m = folium.Map(basel, width=975, height =575, zoom_start=14, tiles='CartoDB Positron')
u_park.apply(plot_dot_park, color = 'blue', map_obj = m, axis = 1)
u_traffic.apply(plot_dot_traffic, color = 'red', map_obj = m, axis = 1)

m.save("overview.html")

# html for clustering
# - - - - - - - - - 
m = folium.Map(basel, width=975, height =575, zoom_start=14, tiles='CartoDB Positron')
plotter(m)
m.save("clusters.html")

# create the html for over time for the clusters
# - - - - - - - - - - - - - - - - - - - - 

# aggregate data over cluster for traffic and parking by time
# reset index to keep by cols as columns and not as index
t_cluster = pd.DataFrame(traffic.groupby(['cluster','date'])['PW'].sum()).reset_index()
p_cluster = pd.DataFrame(park.groupby(['cluster','date'])
                         [['Total Plätze','Anzahl frei']].sum()).reset_index()

# calculate utilization
p_cluster['utilization'] = (p_cluster['Total Plätze'] - p_cluster['Anzahl frei']) / p_cluster['Total Plätze']  

# do the map
m = folium.Map(basel, width=975, height =575, zoom_start=14, tiles='CartoDB Positron')
# intersect time span of two dataframe
time_intersect = list(set(t_cluster['date']).intersection(p_cluster['date']))
# loop over time
relevant_time = [x for x in time_intersect if dt.datetime(2020,2,1) <= x < dt.datetime(2020,2,8)]
relevant_time.sort()

# some seem to miss
p_rel = p_cluster.loc[(p_cluster['date'] > '2020-02-03 16:00') & (p_cluster['date'] < '2020-02-04 01:00')]

t_rel = t_cluster.loc[(t_cluster['date'] > '2020-02-03 16:00') & (t_cluster['date'] < '2020-02-04 01:00')]





# html to pgn
mapFname = 'mymap.html'
mapUrl = 'file://{0}/{1}'.format(os.getcwd(), mapFname)
# use selenium webdriver to save the html as png image
driver = webdriver.Firefox()
driver.set_window_size(1000, 700)
driver.set_window_position(0, 0)
driver.get(mapUrl)
# wait for 2 seconds for the maps and other assets to be loaded in the browser
time.sleep(2)
driver.save_screenshot(os.path.join('png','o.png'))
driver.quit()

# add a title to the html
loc = traffic.at[1,'date'].strftime("%A %d %B, %Y - %I%p")
title_html = '''
             <h3 align="center" style="font-size:16px; background-color:rgb(220,220,220);"><b>{}</b></h3>
             '''.format(loc)   

m.get_root().html.add_child(folium.Element(title_html))



# plot line for all counting stations
agg = traffic.groupby(['date']).PW.agg('sum')
agg = agg.reset_index()

# select just on hour
hour_slice = agg[agg['date'].dt.hour == 10]
x = hour_slice['date']
y = hour_slice['PW']

# plot
plt.style.use('seaborn-whitegrid')
fig = plt.figure()
ax = plt.axes()
ax.plot(x,y)




# calculate arrow
47.547981303298585, 7.598350672962081
47.54998125941649, 7.596247845638821





