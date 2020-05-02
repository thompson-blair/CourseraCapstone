#!/usr/bin/env python
# coding: utf-8

# In[91]:


# import libraries
import urllib.request
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import pgeocode
#!conda install -c conda-forge folium=0.5.0 --yes
import folium
import requests
from pandas.io.json import json_normalize


# In[2]:


# Foursquare login
CLIENT_ID = 'PXLZMKWUHM34CRH3OVZS2AL2QHVQFYQWKQ53MH3K04YNGDBV'
CLIENT_SECRET = 'VUFJAB5KL2NPLRCPIAFKQW3FJ15SQAAATZURVXTXWBRD3RCB'
VERSION = '20200501'
LIMIT = 50


# In[18]:


# request and read page
url = "https://www.zipcodestogo.com/Orange/CA/"
page = urllib.request.urlopen(url)
soup = BeautifulSoup(page, "lxml")
print(soup.prettify())


# In[23]:


# find table on page
wiki_table=soup.find('table')
wiki_table


# In[50]:


# create empty list
A=[]
B=[]
C=[]

# add each element of table to each list
for row in wiki_table.findAll('tr'):
    cells=row.findAll('td')
    if len(cells) == 4:
        A.append(cells[0].find(text=True))
        B.append(cells[1].find(text=True))
        C.append(cells[2].find(text=True))


# In[96]:


# create dataframe using lists A, B, C, D
df=pd.DataFrame(A,columns=['ZipCode'])
df['City']=B
df['State']=C
df = df[df.ZipCode != 'Zip Code']
df = df.drop_duplicates(subset='City', keep='first')
df = df.reset_index(drop=True)
df


# In[97]:


# add latitude and longitude for postal codes
nomi = pgeocode.Nominatim('us')
zip_code = []
lat = []
lon = []
zip_code = df['ZipCode']
for i in zip_code:
    lat.append(nomi.query_postal_code(i)['latitude'])
    lon.append(nomi.query_postal_code(i)['longitude'])
df['Latitude'] = lat
df['Longitude'] = lon

df


# In[85]:


df = df.dropna()
df


# In[98]:


latitude = 33.787914
longitude = -117.853104

# create map of Orange County using latitude and longitude values
map_oc = folium.Map(location=[latitude, longitude], zoom_start=10)

# add markers to map
for lat, lng, label in zip(df['Latitude'], df['Longitude'], df['City']):
    label = folium.Popup(label, parse_html=True)
    folium.CircleMarker(
        [lat, lng],
        radius=5,
        popup=label,
        color='blue',
        fill=True,
        fill_color='#3186cc',
        fill_opacity=0.7,
        parse_html=False).add_to(map_oc)  
    
map_oc


# In[101]:


def getNearbyVenues(names, latitudes, longitudes, radius=1000):
    
    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)
            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            radius, 
            LIMIT)
            
        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']
        
        # return only relevant information for each nearby venue
        venues_list.append([(
            name, 
            lat, 
            lng, 
            v['venue']['name'], 
            v['venue']['location']['lat'], 
            v['venue']['location']['lng'],  
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['City', 
                  'City Latitude', 
                  'City Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    
    return(nearby_venues)


# In[102]:


# get nearby venues in OC
oc_venues = getNearbyVenues(names=df['City'],
                                   latitudes=df['Latitude'],
                                   longitudes=df['Longitude']
                                  )


# In[103]:


oc_venues.head()


# In[104]:


oc_venues.groupby('City').count()


# In[105]:


# one hot encoding
oc_onehot = pd.get_dummies(oc_venues[['Venue Category']], prefix="", prefix_sep="")

# add neighborhood column back to dataframe
oc_onehot['City'] = oc_venues['City'] 

# move neighborhood column to the first column
fixed_columns = [oc_onehot.columns[-1]] + list(oc_onehot.columns[:-1])
toronto_onehot = oc_onehot[fixed_columns]

oc_onehot.head()


# In[106]:


oc_grouped = oc_onehot.groupby('City').mean().reset_index()
oc_grouped


# In[107]:


num_top_venues = 5

for city in oc_grouped['City']:
    print("----"+city+"----")
    temp = oc_grouped[oc_grouped['City'] == city].T.reset_index()
    temp.columns = ['venue','freq']
    temp = temp.iloc[1:]
    temp['freq'] = temp['freq'].astype(float)
    temp = temp.round({'freq': 2})
    print(temp.sort_values('freq', ascending=False).reset_index(drop=True).head(num_top_venues))
    print('\n')


# In[108]:


def return_most_common_venues(row, num_top_venues):
    row_categories = row.iloc[1:]
    row_categories_sorted = row_categories.sort_values(ascending=False)
    
    return row_categories_sorted.index.values[0:num_top_venues]


# In[117]:


num_top_venues = 10

indicators = ['st', 'nd', 'rd']

# create columns according to number of top venues
columns = ['City']
for ind in np.arange(num_top_venues):
    try:
        columns.append('{}{} Most Common Venue'.format(ind+1, indicators[ind]))
    except:
        columns.append('{}th Most Common Venue'.format(ind+1))

# create a new dataframe
city_venues_sorted = pd.DataFrame(columns=columns)
city_venues_sorted['City'] = oc_grouped['City']

for ind in np.arange(oc_grouped.shape[0]):
    city_venues_sorted.iloc[ind, 1:] = return_most_common_venues(oc_grouped.iloc[ind, :], num_top_venues)

city_venues_sorted.head()


# In[118]:


city_venues_sorted.set_index('City', inplace=True)


# In[119]:


city_venues_sorted[city_venues_sorted.isin(['Brewery'])].dropna(how='all')


# In[ ]:




