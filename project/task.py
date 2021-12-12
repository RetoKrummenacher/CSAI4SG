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


""" 
functions
"""
def change_site_name(site_name):
    sp = site_name.split(' ',1)
    return sp[1]

def change_park_capacity(name, cap_col, max_free):
    cap = cap_col

    value = max_free[max_free['name'] == name].reset_index()['Anzahl frei'].iloc[0]
    if cap < value:
        cap = value
    
    return cap
    
def change_park_free(name, free_col, max_free):
    free = free_col
    
    # europe value, reset index so new one row df has 0 index for iloc[0]
    value = max_free[max_free['name'] == 'Europe'].reset_index()['Total Plätze'].iloc[0]
    
    # change europe where its obviously false
    if name == 'Europe' and free_col > value :
        free = value           
            
    return free

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
    
def change_date(df, time_col, unique_col, new_col):
    df = df.copy()  # copy need if changes in dataframe, else just reference
    # convert date str to utc rounded hours
    df[new_col] = pd.to_datetime(df[time_col], utc = True)
    # round on 15 minutes, the get those nearest to full hour
    df[new_col] = df[new_col].dt.round('15min')
    # drop duplicates 
    df = df.drop_duplicates(subset = [new_col, unique_col])
    # round on full hour
    df[new_col]  = df[new_col].dt.round('H')    
    # drop duplicates 
    df = df.drop_duplicates(subset = [new_col, unique_col])
    # only use those at full hour
    return df

def check_on_date(df, df_ori, time_col, time_col_ori, number_per_hour):
    # check
    check = pd.DataFrame(df[time_col].value_counts())
    # all not number_per_hour: e.g 15 parkings
    print('Rows where value counts not equals ',number_per_hour,':',
          len(check[check[time_col] != number_per_hour])) # no rows
    # are all hours in in?
    # create timestamps over full period of original dataframe
    end_date = max(pd.to_datetime(df_ori[time_col_ori], utc=True).dt.round('H'))
    start_date = min(pd.to_datetime(df_ori[time_col_ori], utc=True).dt.round('H'))
    def daterange(start_date, end_date):
        delta = dt.timedelta(hours=1)
        while start_date < end_date:
            yield start_date
            start_date += delta
    
    all_l = []
    for single_date in daterange(start_date, end_date):
        all_l.append(single_date)
    
    # check whats missing
    here_l = list(df[time_col].unique())
    missing = list(set(all_l).difference(set(here_l)))
    print(len(missing),'hours are missing in the original set')
    missing.sort()
    return (check, missing)

        
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
    
def plot_clusters(map_obj):
    for cord, angle in arrows:       
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


"""
scrip
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
# names for traffic site
traffic['name'] = traffic['SiteName'].apply(lambda x: change_site_name(x)) 

# use function to change date
park = change_date(park, 'Publikationszeit', 'name', 'date')
# check dates in park
value_counts_p, mis_p = check_on_date(park, park_raw, 'date', 'Publikationszeit', 15)
# some days and hours are missing completely, check mis_p

# use function to change date
traffic = change_date(traffic, 'DateTimeTo', 'name', 'date')
# check dates in traffic, there are 29 unique counting stations
value_counts_t, mis_t = check_on_date(traffic, traffic_raw, 'date', 'DateTimeTo', 29)
# many counting stations have not full set, check value_counts_t
# e.g. aussere Baselstrasse missing for 2019-03-24, 23:00

# change geopoints
park[['lat','lng']] = park['geoPoint'].str.split(',', expand=True) 
traffic[['lat','lng']] = traffic['geoPoint'].str.split(',', expand=True) 

# names for traffic site
traffic['name'] = traffic['SiteName'].apply(lambda x: change_site_name(x)) 

# there are cases where there are more Anzahl frei then Total Plätze
# it seems the capacity of the parkings is not accurate, as the 
# freie plätze is given the rrs of the ParkLeitSystem of Basel
# our solution. set the capacity to the highest value of ever freie platze
# for cases where there are more freie Plätze then Anzahl
max_free = pd.DataFrame(park.groupby(['name'])[['Anzahl frei','Total Plätze']].max()).reset_index()
park['free'] = park.apply(lambda row: change_park_free(row['name'], row['Anzahl frei'], max_free), axis=1)
park['capacity'] = park.apply(lambda row: change_park_capacity(row['name'], row['Total Plätze'], max_free), axis=1)
check_max_free = pd.DataFrame(park.groupby(['name'])[['free','capacity']].max()).reset_index()

# utilization
park['utilization'] = (park['capacity'] - park['free']) / park['capacity']  

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
# select unique geo koordinates
u_traffic = traffic[['lat','lng','name', 'average']].drop_duplicates()
u_park = park[['lat','lng','name','Total Plätze']].drop_duplicates()


m = folium.Map(basel, width=975, height =575, zoom_start=14, tiles='CartoDB Positron')
u_park.apply(plot_dot_park, color = 'blue', map_obj = m, axis = 1)
u_traffic.apply(plot_dot_traffic, color = 'red', map_obj = m, axis = 1)

m.save("overview.html")

# html for clustering
# - - - - - - - - - 
m = folium.Map(basel, width=975, height =575, zoom_start=14, tiles='CartoDB Positron')
plot_clusters(m)
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

# intersect time span of two dataframe
time_intersect = list(set(t_cluster['date']).intersection(p_cluster['date']))
# loop over time
relevant_time = [x for x in time_intersect if dt.datetime(2020,2,1) <= x < dt.datetime(2020,2,8)]
relevant_time.sort()

# # some seem to miss: RKR checked 2021-12-11 an its ok after changing change_date() if clause
# p_rel = p_cluster.loc[(p_cluster['date'] > '2020-02-03 16:00') & (p_cluster['date'] < '2020-02-04 01:00')]
# t_rel = t_cluster.loc[(t_cluster['date'] > '2020-02-03 16:00') & (t_cluster['date'] < '2020-02-04 01:00')]

for hour in relevant_time():
    # select data
    p = p_cluster.loc[(p_cluster['date'] == hour)]
    t = t_cluster.loc[(t_cluster['date'] == hour)]
    
    # do the map
    m = folium.Map(basel, width=975, height =575, zoom_start=14, tiles='CartoDB Positron')
    
    



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





