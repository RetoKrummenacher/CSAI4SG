# -*- coding: utf-8 -*-
"""
Created on Wed Dec  8 15:33:39 2021

@author: retok
"""

import pandas as pd               # a data.frame handler like R
import numpy as np                # for histograms
import bisect                     # for bin determination
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

import imgkit


""" 
functions
"""
def change_site_name(site_name):
    sp = site_name.split(' ',1)
    return sp[1]

def change_park_capacity(entry, name ,d):
    d_d = d.get('Anzahl frei')
    value = d_d.get(name)
    if name != 'Europe' and entry < value:
        entry = value    
    return entry
    
def change_park_free(entry, name, d):
    d_d = d.get('Total Plätze')
    value = d_d.get(name)    
    # change europe where its obviously false
    if name == 'Europe' and entry > value :
        entry = value           
            
    return entry

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

def plot_park_cluster(cord, color, map_obj, free, capacity, utilization):
    folium.Circle(location=cord, radius=450, fill_color = color,
                  fill=True, color='grey', weight=1, 
                  tooltip='Frei: ' + str(free) + '; Kapazität: ' + str(capacity) + 
                  '; Belegung: ' + str(round(utilization,3) * 100)+ '%', 
                  fill_opacity=0.4).add_to(map_obj)
    
def plot_arrow(cord, angle, color, map_obj, pw, size=9):
    icon_arrow = BeautifyIcon(
        icon=' fa fa-angle-double-down',
        inner_icon_style="""font-size:{2}rem;transform: rotate({0}deg);
                    color:{1};opacity:0.8;""".format(angle, color, size),
        background_color='transparent',
        border_color='transparent',
    )
    
    # add arrow
    folium.Marker(location=cord, icon=icon_arrow,
                  tooltip='Anzahl Personenwagen: ' + str(pw)).add_to(map_obj)
    
def change_date(df, time_col, new_col):
    df = df.copy()  # copy need if changes in dataframe, else just reference
    # convert date str to utc rounded hours
    df[new_col] = pd.to_datetime(df[time_col], utc = True)
    # round on 15 minutes, the get those nearest to full hour
    df[new_col] = df[new_col].dt.round('15min')
    # drop duplicates 
    df = df.drop_duplicates()
    # round on full hour
    df[new_col]  = df[new_col].dt.round('H')    
    # drop duplicates 
    df = df.drop_duplicates()
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
basel = [47.55777131440573, 7.5918295281706865]  # basel
inter_tokb = [47.55866679121571, 7.592048476255378] # arrow to kleinbasel
inter_togb = [47.56118158101615, 7.588564901186044] # arrow to kleinbasel
kb_in = [47.57118487571712, 7.600878933966805] # kleinbasel in
kb_out = [47.56659343678, 7.605334669686331] # kleinbasel out
gb_west_in = [47.55521649435031, 7.575291688622761] # gb in form west
gb_west_out = [47.55970599232563, 7.580109075351799] # gb out to west
gb_east_in = [47.55380087693972, 7.595126984456187] # gb in form est
gb_east_out = [47.549809396450826, 7.593506716982079] # gb out to est
kb = [47.563625981205035, 7.597494837472192]  # kleinbasel
gb = [47.552285168616876, 7.585847935404933] # grossbasel

# arrow list incldugin the angle of arrow
arrows = {'inter_togb' : (inter_togb, 40), 'inter_tokb': (inter_tokb, 220),
          'kb_in' : (kb_in, 30), 'kb_out' : (kb_out,265), 
          'gb_west_in' : (gb_west_in, 290), 'gb_west_out' : (gb_west_out,140), 
          'gb_east_in' : (gb_east_in, 100), 'gb_east_out' : (gb_east_out, -55)}
# cluster list
clusters = {'kb' : kb, 'gb' : gb}
   
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
park = change_date(park, 'Publikationszeit', 'date')
# check dates in park
# value_counts_p, mis_p = check_on_date(park, park_raw, 'date', 'Publikationszeit', 15)
# some days and hours are missing completely, check mis_p

# use function to change date
traffic = change_date(traffic, 'DateTimeTo', 'date')
# check dates in traffic, there are 29 unique counting stations
# value_counts_t, mis_t = check_on_date(traffic, traffic_raw, 'date', 'DateTimeTo', 29)
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
# make dictionary with name as index
d = max_free.set_index(['name']).to_dict()
park['free'] = park.apply(lambda row: change_park_free(row['Anzahl frei'], row['name'], d), axis=1)
park['capacity'] = park.apply(lambda row: change_park_capacity(row['Total Plätze'], row['name'] ,d), axis=1)
check_max_free = pd.DataFrame(park.groupby(['name'])[['free','capacity']].max()).reset_index()

# utilization
park['utilization'] = (park['capacity'] - park['free']) / park['capacity']  

# average counts over 2019 per day
# select 2019 data
df2019 = traffic[traffic['date'].dt.year == 2019].copy()
# average over PW group by site
df2019_avg = pd.DataFrame(df2019.groupby('name')['PW'].mean())
df2019_avg.rename(columns={'PW' : 'average'}, inplace=True)
# merge that to traffic
traffic = traffic.merge(df2019_avg, left_on = 'name', right_on = 'name', 
                     how = 'left').set_axis(traffic.index) 

# add clustering to data
traffic = traffic.merge(traffic_cluster[['geoPoint','DirectionName','cluster']], 
                    on = ['geoPoint','DirectionName'], how = 'left').set_axis(traffic.index)
park = park.merge(park_cluster[['geoPoint','cluster']], left_on = 'geoPoint', right_on = 'geoPoint', 
                     how = 'left').set_axis(park.index) 


# html for overview:
# - - - - - - - - -
# select unique geo koordinates
u_traffic = traffic[['lat','lng','name', 'average']].drop_duplicates()
u_park = park[['lat','lng','name','Total Plätze']].drop_duplicates()

m = folium.Map(basel,zoom_start=14, tiles='CartoDB Positron')
u_park.apply(plot_dot_park, color = 'blue', map_obj = m, axis = 1)
u_traffic.apply(plot_dot_traffic, color = 'red', map_obj = m, axis = 1)

m.save(os.path.join(parent_path,"overview.html"))


# create the html for over time for the clusters
# - - - - - - - - - - - - - - - - - - - - 
# aggregate data over cluster for traffic and parking by time
# reset index to keep by cols as columns and not as index
t_cluster = pd.DataFrame(traffic.groupby(['cluster','date'])['PW'].sum()).reset_index()
p_cluster = pd.DataFrame(park.groupby(['cluster','date'])
                         [['capacity','free']].sum()).reset_index()

# calculate utilization
p_cluster['utilization'] = (p_cluster['capacity'] - p_cluster['free']) / p_cluster['capacity']  

# select data
start_date = '2020-2-1' # included
end_date = '2020-2-8' # excluded
# get our data and make sure to use copies
p_work = p_cluster[(p_cluster['date'] >= start_date) & (p_cluster['date'] < end_date)].copy()
t_work = t_cluster[(t_cluster['date'] >= start_date) & (t_cluster['date'] < end_date)].copy()


def add_colors(entry, edges):
    # color dictionary with HEX colors
    d = {1 : '#bfff00', 2 : '#ffff00', 3 : '#ffbf00', 
             4 : '#ff8000', 5 : '#ff4000'}
    
    # determin bin number
    bin = bisect.bisect_left(edges, entry)
    # return the color from the dictionary
    return d.get(bin,1)    

# different sizes doesn't look got, so same size for all
def add_colors_size(entry, edges, what = 'c'):
    # color dictionary with HEX colors
    d = {1 : ('#00cc00',8), 2 : ('#ffcc00',8), 3 : ('#ff9933',8), 
             4 : ('#ff5050',8), 5 : ('#b30000',8)}
    
    # determin bin number
    bin = bisect.bisect_left(edges, entry)
    # bin can be zero (no clue why 0 <0.0)
    if bin == 0:
        bin = 1    
    # return the color from the dictionary
    color, size =  d.get(bin)
    if what == 's':
        return size
    else:
        return color


# generate histogram with 5 bins for colors
hist = np.histogram(p_work['utilization'].unique(), bins = 5)
# edges for the bins, a bin lies between two numbers
edges = list(hist[1])
# generate color from data
p_work['color'] = p_work.apply(lambda row: add_colors(row['utilization'], edges), axis=1)
# same for traffic
hist = np.histogram(t_work['PW'].unique(), bins = 5)
# edges for the bins, a bin lies between two numbers
edges = list(hist[1])
# generate color from data
t_work['color'] = t_work.apply(lambda row: add_colors_size(row['PW'], edges), axis=1)
t_work['size'] = t_work.apply(lambda row: add_colors_size(row['PW'], edges, 's'), axis=1)


# empty images list
images = []

# loop over hours in work frames
for hour in p_work['date'].unique():   
    # select data
    p = p_work.loc[(p_work['date'] == hour)]
    t = t_work.loc[(t_work['date'] == hour)]
    
    # do the map
    m = folium.Map(basel, width=975, height =575, zoom_start=14, tiles='CartoDB Positron')
    
    # plot the arrows
    for key, tup in arrows.items():      
        # get color and size of that cord
        idx = t.index[t['cluster'] == key][0]  # index of row with cluster == key
        color = t.at[idx ,'color']
        size = t.at[idx ,'size']
        pw = t.at[idx ,'PW']
        plot_arrow(tup[0], tup[1], color, m, pw, size)    
        
    # plot the parking clusters
    for key, cluster in clusters.items():      
        # get color and size of that cord
        idx = p.index[p['cluster'] == key][0]  # index of row with cluster == key
        color = p.at[idx ,'color']   
        free = p.at[idx ,'free']   
        capacity = p.at[idx ,'capacity']   
        utilization = p.at[idx ,'utilization']   
        plot_park_cluster(cluster, color, m, free, capacity, utilization) 
        
    # add a title to the html
    title = hour.strftime("%A %d %B, %Y - %I%p")
    title_html = '''
                 <h3 align="left" style="font-size:16px;"><b>{}</b></h3>
                 '''.format(title)   

    m.get_root().html.add_child(folium.Element(title_html))
    
    image_name = hour.strftime('%Y_%m_%d_%I%p')
    image_name_html = os.path.join(parent_path,
                                'html',image_name + '.html')
    image_name_png = os.path.join(parent_path,
                                'png',image_name + '.png')
    m.save(image_name_html)   
            
    # html to pgn
    mapUrl = 'file://{0}/{1}'.format(os.path.join(parent_path,
                                'html'), image_name + '.html')
    # use selenium webdriver to save the html as png image
    driver = webdriver.Firefox()
    driver.set_window_size(1000, 700)
    driver.set_window_position(0, 0)
    driver.get(mapUrl)
    # wait for 2 seconds for the maps and other assets to be loaded in the browser
    time.sleep(5)
    driver.save_screenshot(image_name_png)
    driver.quit()
    
    # add to images list
    im = pil.Image.open(image_name_png)
    images.append(im)
    
    # loop
 
    
 # duration in milli seconds, endless: loop = 0
images[0].save(os.path.join(parent_path,'running.gif'),
               save_all=True, append_images=images[1:], optimize=False, duration=500, loop=1)
    
    

# try to calcualte an rolling average
# - - - - - - - - - - - - - - - - 

# calculate sum for each time stamp
t = pd.DataFrame(traffic.groupby(['date'])['PW'].sum()).reset_index()
p = pd.DataFrame(park.groupby(['date'])[['capacity','free']].sum()).reset_index() 

# select common 
# intersect time span of two dataframe
time_intersect = list(set(t['date']).intersection(p['date']))

# select common times
t = t[t['date'].isin(time_intersect)]
p = p[p['date'].isin(time_intersect)]

window_size = 672
t_rol = t.rolling(window_size, center = True, on ='date', closed = 'both').mean()
p_rol = p.rolling(window_size, center = True, on ='date', closed = 'both').mean()

# exclude those that ara np.nan
t_rol.dropna(inplace = True)
p_rol.dropna(inplace = True)

# calculate utilization
p_rol['utilization'] = (p_rol['capacity'] - p_rol['free']) / p_rol['capacity']  

# calucate indexed series 
start_index = min(t_rol['date'])
end_index = max(t_rol['date'])
# index of that row 
t_idx = t_rol.index[t_rol['date'] == start_index][0]
p_idx = p_rol.index[p_rol['date'] == start_index][0] 
                    
t_rol['index'] = t_rol['PW'] / t_rol.at[t_idx,'PW'] * 100
p_rol['index'] = p_rol['utilization'] / p_rol.at[p_idx,'utilization'] * 100

f = plt.figure()
f.set_figwidth(20)
f.set_figheight(10)
plt.rcParams.update({'font.size': 14})

plt.plot(t_rol['date'], t_rol['index'], color = 'tab:red', label = "Traffic", linewidth=2)
plt.plot(p_rol['date'], p_rol['index'], color = 'tab:blue', label = "Parking utilization", linewidth=2)
plt.title('Rolling Average over 28 days')

plt.xlim([start_index, end_index])

plt.xlabel('Time')
plt.ylabel('Index (' + start_index.strftime('%Y-%m-%d %I%p') + '=100)' )
plt.legend(loc = 'lower right')
plt.grid()
plt.show()










